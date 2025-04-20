import os
import re
import time
import shutil
import asyncio
import logging
from datetime import datetime
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaDocument, Message, InlineKeyboardMarkup, InlineKeyboardButton
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from plugins.antinsfw import check_anti_nsfw
from helper.utils import progress_for_pyrogram, humanbytes, convert
from helper.database import codeflixbots
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global dictionary to track ongoing operations
renaming_operations = {}

# Enhanced regex patterns for season, episode, chapter, and volume extraction
SEASON_EPISODE_PATTERNS = [
    # Standard patterns (S01E02, S01EP02)
    (re.compile(r'S(\d+)(?:E|EP)(\d+)'), ('season', 'episode')),
    # Patterns with spaces/dashes (S01 E02, S01-EP02)
    (re.compile(r'S(\d+)[\s-]*(?:E|EP)(\d+)'), ('season', 'episode')),
    # Full text patterns (Season 1 Episode 2)
    (re.compile(r'Season\s*(\d+)\s*Episode\s*(\d+)', re.IGNORECASE), ('season', 'episode')),
    # Patterns with brackets/parentheses ([S01][E02])
    (re.compile(r'\[S(\d+)\]\[E(\d+)\]'), ('season', 'episode')),
    # Fallback patterns (S01 13, Episode 13)
    (re.compile(r'S(\d+)[^\d]*(\d+)'), ('season', 'episode')),
    (re.compile(r'(?:E|EP|Episode)\s*(\d+)', re.IGNORECASE), (None, 'episode')),
    # Chapter and Volume patterns
    (re.compile(r'Chapter\s*(\d+)', re.IGNORECASE), (None, 'chapter')),
    (re.compile(r'Volume\s*(\d+)', re.IGNORECASE), (None, 'volume')),
    # Final fallback (standalone number)
    (re.compile(r'\b(\d+)\b'), (None, 'episode'))
]

# Quality detection patterns
QUALITY_PATTERNS = [
    (re.compile(r'\b(\d{3,4}[pi])\b', re.IGNORECASE), lambda m: m.group(1)),  # 1080p, 720p
    (re.compile(r'\b(4k|2160p)\b', re.IGNORECASE), lambda m: "4k"),
    (re.compile(r'\b(2k|1440p)\b', re.IGNORECASE), lambda m: "2k"),
    (re.compile(r'\b(HDRip|HDTV)\b', re.IGNORECASE), lambda m: m.group(1)),
    (re.compile(r'\b(4kX264|4kx265)\b', re.IGNORECASE), lambda m: m.group(1)),
    (re.compile(r'\[(\d{3,4}[pi])\]', re.IGNORECASE), lambda m: m.group(1))  # [1080p]
]

async def extract_season_episode(source_text, user_id):
    """Extract season, episode, chapter, or volume numbers from source (filename or caption)"""
    extraction_mode = await codeflixbots.get_extraction_mode(user_id)
    logger.info(f"Extracting metadata from {extraction_mode}: {source_text}")
    
    for pattern, (season_group, metadata_type) in SEASON_EPISODE_PATTERNS:
        match = pattern.search(source_text)
        if match:
            season = match.group(1) if season_group else None
            value = match.group(1) if metadata_type else match.group(2)
            logger.info(f"Extracted {metadata_type}: {value}, season: {season} from {source_text}")
            return season, value, metadata_type
    logger.warning(f"No metadata pattern matched for {source_text}")
    return None, None, None

async def extract_quality(source_text, user_id):
    """Extract quality information from source (filename or caption)"""
    extraction_mode = await codeflixbots.get_extraction_mode(user_id)
    logger.info(f"Extracting quality from {extraction_mode}: {source_text}")
    
    for pattern, extractor in QUALITY_PATTERNS:
        match = pattern.search(source_text)
        if match:
            quality = extractor(match)
            logger.info(f"Extracted quality: {quality} from {source_text}")
            return quality
    logger.warning(f"No quality pattern matched for {source_text}")
    return "Unknown"

async def cleanup_files(*paths):
    """Safely remove files if they exist"""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.error(f"Error removing {path}: {e}")

async def process_thumbnail(thumb_path):
    """Process and resize thumbnail image"""
    if not thumb_path or not os.path.exists(thumb_path):
        return None
    
    try:
        with Image.open(thumb_path) as img:
            img = img.convert("RGB").resize((320, 320))
            img.save(thumb_path, "JPEG")
        return thumb_path
    except Exception as e:
        logger.error(f"Thumbnail processing failed: {e}")
        await cleanup_files(thumb_path)
        return None

async def add_metadata(input_path, output_path, user_id):
    """Add metadata to media file using ffmpeg"""
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError("FFmpeg not found in PATH")
    
    metadata = {
        'title': await codeflixbots.get_title(user_id),
        'artist': await codeflixbots.get_artist(user_id),
        'author': await codeflixbots.get_author(user_id),
        'video_title': await codeflixbots.get_video(user_id),
        'audio_title': await codeflixbots.get_audio(user_id),
        'subtitle': await codeflixbots.get_subtitle(user_id)
    }
    
    cmd = [
        ffmpeg,
        '-i', input_path,
        '-metadata', f'title={metadata["title"]}',
        '-metadata', f'artist={metadata["artist"]}',
        '-metadata', f'author={metadata["author"]}',
        '-metadata:s:v', f'title={metadata["video_title"]}',
        '-metadata:s:a', f'title={metadata["audio_title"]}',
        '-metadata:s:s', f'title={metadata["subtitle"]}',
        '-map', '0',
        '-c', 'copy',
        '-loglevel', 'error',
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {stderr.decode()}")

@Client.on_message(filters.private & filters.command("setextract"))
async def set_extract_command(client, message):
    """Handle /setextract command to choose extraction mode"""
    user_id = message.from_user.id
    current_mode = await codeflixbots.get_extraction_mode(user_id)

    # Create inline keyboard with Filename and Caption options
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Filename", callback_data=f"extract_filename_{user_id}"),
            InlineKeyboardButton("Caption", callback_data=f"extract_caption_{user_id}")
        ]
    ])

    await message.reply_text(
        f"Current extraction mode: **{current_mode.capitalize()}**\n"
        "Choose the source for metadata extraction (season, episode, quality, etc.):",
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex(r"extract_(filename|caption)_(\d+)"))
async def handle_extract_callback(client, callback_query):
    """Handle callback queries for extraction mode selection"""
    mode = callback_query.matches[0].group(1)  # filename or caption
    user_id = int(callback_query.matches[0].group(2))

    if callback_query.from_user.id != user_id:
        await callback_query.answer("This button is not for you!", show_alert=True)
        return

    # Update extraction mode in the database
    await codeflixbots.set_extraction_mode(user_id, mode)
    await callback_query.message.edit_text(
        f"Extraction mode set to: **{mode.capitalize()}**\n"
        "Metadata (season, episode, quality, etc.) will now be extracted from the {mode}."
    )
    await callback_query.answer(f"Set to {mode} mode")

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def auto_rename_files(client, message):
    """Main handler for auto-renaming files"""
    user_id = message.from_user.id
    format_template = await codeflixbots.get_format_template(user_id)
    
    if not format_template:
        return await message.reply_text("Please set a rename format using /autorename")

    # Get file information
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_size = message.document.file_size
        media_type = "document"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video"
        file_size = message.video.file_size
        media_type = "video"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "audio"
        file_size = message.audio.file_size
        media_type = "audio"
    else:
        return await message.reply_text("Unsupported file type")

    # NSFW check
    if await check_anti_nsfw(file_name, message):
        return await message.reply_text("NSFW content detected")

    # Prevent duplicate processing
    if file_id in renaming_operations:
        if (datetime.now() - renaming_operations[file_id]).seconds < 10:
            return
    renaming_operations[file_id] = datetime.now()

    try:
        # Determine extraction source (filename or caption)
        extraction_mode = await codeflixbots.get_extraction_mode(user_id)
        source_text = message.caption or file_name if extraction_mode == "caption" else file_name

        # Extract metadata from source
        season, value, metadata_type = await extract_season_episode(source_text, user_id)
        quality = await extract_quality(source_text, user_id)
        
        # Replace placeholders in template
        replacements = {
            '{season}': season or 'XX',
            '{episode}': value or 'XX' if metadata_type == 'episode' else 'XX',
            '{chapter}': value or 'XX' if metadata_type == 'chapter' else 'XX',
            '{volume}': value or 'XX' if metadata_type == 'volume' else 'XX',
            '{quality}': quality,
            'Season': season or 'XX',
            'Episode': value or 'XX' if metadata_type == 'episode' else 'XX',
            'Chapter': value or 'XX' if metadata_type == 'chapter' else 'XX',
            'Volume': value or 'XX' if metadata_type == 'volume' else 'XX',
            'QUALITY': quality
        }
        
        for placeholder, value in replacements.items():
            format_template = format_template.replace(placeholder, value)

        # Prepare file paths
        ext = os.path.splitext(file_name)[1] or ('.mp4' if media_type == 'video' else '.mp3')
        new_filename = f"{format_template}{ext}"
        download_path = f"downloads/{new_filename}"
        metadata_path = f"metadata/{new_filename}"
        
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

        # Download file
        msg = await message.reply_text("**Downloading...**")
        try:
            file_path = await client.download_media(
                message,
                file_name=download_path,
                progress=progress_for_pyrogram,
                progress_args=("Downloading...", msg, time.time())
            )
        except Exception as e:
            await msg.edit(f"Download failed: {e}")
            raise

        # Process metadata
        await msg.edit("**Processing metadata...**")
        try:
            await add_metadata(file_path, metadata_path, user_id)
            file_path = metadata_path
        except Exception as e:
            await msg.edit(f"Metadata processing failed: {e}")
            raise

        # Prepare for upload
        await msg.edit("**Preparing upload...**")
        caption = await codeflixbots.get_caption(message.chat.id) or f"**{new_filename}**"
        thumb = await codeflixbots.get_thumbnail(message.chat.id)
        thumb_path = None

        # Handle thumbnail
        if thumb:
            thumb_path = await client.download_media(thumb)
        elif media_type == "video" and message.video.thumbs:
            thumb_path = await client.download_media(message.video.thumbs[0].file_id)
        
        thumb_path = await process_thumbnail(thumb_path)

        # Upload file
        await msg.edit("**Uploading...**")
        try:
            upload_params = {
                'chat_id': message.chat.id,
                'caption': caption,
                'thumb': thumb_path,
                'progress': progress_for_pyrogram,
                'progress_args': ("Uploading...", msg, time.time())
            }

            if media_type == "document":
                await client.send_document(document=file_path, **upload_params)
            elif media_type == "video":
                await client.send_video(video=file_path, **upload_params)
            elif media_type == "audio":
                await client.send_audio(audio=file_path, **upload_params)

            await msg.delete()
        except Exception as e:
            await msg.edit(f"Upload failed: {e}")
            raise

    except Exception as e:
        logger.error(f"Processing error: {e}")
        await message.reply_text(f"Error: {str(e)}")
    finally:
        # Clean up files
        await cleanup_files(download_path, metadata_path, thumb_path)
        renaming_operations.pop(file_id, None)
