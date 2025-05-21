import random
import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import pytz
from config import Config
from helper.database import codeflixbots

# MongoDB client setup
mongo_client = AsyncIOMotorClient(Config.DB_URL)
db = mongo_client[Config.DB_NAME]
users_col = db["users"]
settings_col = db["settings"]

# Initialize active sequences and message IDs
active_sequences = {}
message_ids = {}

# Admin mode and admins
ADMIN_MODE = Config.ADMIN_MODE
ADMINS = Config.ADMINS

# Quality order dictionary
quality_order = {
    "144p": 1, "240p": 2, "360p": 3, "480p": 4,
    "720p": 5, "1080p": 6, "1440p": 7, "2160p": 8
}

# Extract quality from filename
def extract_quality(filename):
    filename = filename.lower()
    patterns = [
        (r'2160p|4k', '2160p'),
        (r'1440p|2k', '1440p'),
        (r'1080p|fhd', '1080p'),
        (r'720p|hd', '720p'),
        (r'480p|sd', '480p'),
        (r'(\d{3,4})p', lambda m: f"{m.group(1)}p")
    ]
    
    for pattern, value in patterns:
        match = re.search(pattern, filename)
        if match:
            return value if isinstance(value, str) else value(match)
    return "unknown"

# Sorting key function
def sorting_key(f, sort_mode="episode"):
    filename = f["file_name"].lower()
    season = episode = 0
    season_match = re.search(r's(\d+)', filename)
    episode_match = re.search(r'e(\d+)', filename) or re.search(r'ep?(\d+)', filename)
    
    if season_match:
        season = int(season_match.group(1))
    if episode_match:
        episode = int(episode_match.group(1))
    
    quality = extract_quality(filename)
    quality_priority = quality_order.get(quality.lower(), 9)
    padded_episode = f"{episode:04d}"
    
    if sort_mode == "quality":
        return (quality_priority, season, padded_episode, filename)
    elif sort_mode == "title":
        return (filename, season, padded_episode, quality_priority)
    elif sort_mode == "both":
        return (filename, quality_priority, season, padded_episode)
    else:  # episode (default)
        return (season, padded_episode, quality_priority, filename)

# Decorator to check ban status
def check_ban_status(func):
    async def wrapper(client, message: Message):
        user_id = message.from_user.id
        user_data = await users_col.find_one({"_id": user_id})
        if user_data and user_data.get("banned", False):
            await message.reply_text("You are banned from using this bot!")
            return
        return await func(client, message)
    return wrapper

# Decorator to restrict to admins
def admin_only(func):
    async def wrapper(client, message: Message):
        user_id = message.from_user.id
        if user_id not in ADMINS:
            await message.reply_text("This command is for admins only!")
            return
        return await func(client, message)
    return wrapper

# Decorator to restrict to owner
def owner_only(func):
    async def wrapper(client, message: Message):
        user_id = message.from_user.id
        if user_id != Config.OWNER_ID:
            await message.reply_text("This command is for the bot owner only!")
            return
        return await func(client, message)
    return wrapper

# Start Command Handler
@Client.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    user = message.from_user
    user_id = user.id
    
    # Add user to database if not exists
    await codeflixbots.add_user(client, message)
    
    # Initialize user settings if not present
    await users_col.update_one(
        {"_id": user_id},
        {"$setOnInsert": {
            "sort_mode": "episode",
            "sticker_mode": "default",
            "sticker_id": Config.DEFAULT_STICKER,
            "file_count": 0,
            "last_activity": datetime.now(pytz.UTC),
            "dump_channel": None
        }},
        upsert=True
    )

    # Initialize completion sticker if not set
    await settings_col.update_one(
        {"_id": "bot_settings"},
        {"$setOnInsert": {"completion_sticker": Config.DEFAULT_STICKER}},
        upsert=True
    )

    # Initial interactive text and sticker sequence
    m = await message.reply_text("ʜᴇʜᴇ..ɪ'ᴍ ᴀɴʏᴀ!\nᴡᴀɪᴛ ᴀ ᴍᴏᴍᴇɴᴛ. . .")
    await asyncio.sleep(0.4)
    await m.edit_text("🎊")
    await asyncio.sleep(0.5)
    await m.edit_text("⚡")
    await asyncio.sleep(0.5)
    await m.edit_text("ᴡᴀᴋᴜ ᴡᴀᴋᴜ!...")
    await asyncio.sleep(0.4)
    await m.delete()

    # Send sticker after the text sequence
    await message.reply_sticker(Config.DEFAULT_STICKER)

    # Define buttons for the start message
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
        [InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Codeflix_Bots'),
         InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/CodeflixSupport')],
        [InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about')]
    ])

    # Send start message with or without picture
    if Config.START_PIC:
        await message.reply_photo(
            Config.START_PIC,
            caption=Config.START_TXT.format(user.mention),
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            text=Config.START_TXT.format(user.mention),
            reply_markup=buttons,
            disable_web_page_preview=True
        )

# File/Video Handler for Auto-Queue
@Client.on_message(filters.private & (filters.document | filters.video))
@check_ban_status
async def handle_file(client, message: Message):
    user_id = message.from_user.id
    
    # Automatically start a sequence if not already active
    if user_id not in active_sequences:
        active_sequences[user_id] = []
        message_ids[user_id] = []
        msg = await message.reply_text("Sᴇǫᴜᴇɴᴄᴇ ʜᴀs ʙᴇᴇɴ sᴛᴀʀᴛᴇᴅ! Sᴇɴᴅ ʏᴏᴜʀ ғɪʟᴇs...")
        message_ids[user_id].append(msg.id)
    
    # Add file to sequence
    file_name = message.document.file_name if message.document else message.video.file_name
    file_id = message.document.file_id if message.document else message.video.file_id
    active_sequences[user_id].append({"file_id": file_id, "file_name": file_name})
    
    # Send confirmation with file count
    file_count = len(active_sequences[user_id])
    await message.reply_text(f"Fɪʟᴇ Aᴅᴅᴇᴅ Iɴ Qᴜᴇᴜᴇ {file_count}")

# Set Sticker Command Handler
@Client.on_message(filters.private & filters.command("setsticker"))
@check_ban_status
async def set_sticker(client, message: Message):
    user_id = message.from_user.id
    if not message.reply_to_message or not message.reply_to_message.sticker:
        await message.reply_text("Please reply to a sticker with /setsticker to set it as your custom sticker.")
        return
    
    sticker_id = message.reply_to_message.sticker.file_id
    await users_col.update_one(
        {"_id": user_id},
        {"$set": {"sticker_id": sticker_id}}
    )
    await message.reply_text("Custom sticker set successfully!")

# Get Sticker Command Handler
@Client.on_message(filters.private & filters.command("getsticker"))
@check_ban_status
async def get_sticker(client, message: Message):
    user_id = message.from_user.id
    user_data = await users_col.find_one({"_id": user_id})
    sticker_id = user_data.get("sticker_id", Config.DEFAULT_STICKER)
    await message.reply_sticker(sticker_id)
    await message.reply_text("This is your currently set sticker.")

# Delete Sticker Command Handler
@Client.on_message(filters.private & filters.command("delsticker"))
@check_ban_status
async def delete_sticker(client, message: Message):
    user_id = message.from_user.id
    await users_col.update_one(
        {"_id": user_id},
        {"$set": {"sticker_id": Config.DEFAULT_STICKER}}
    )
    await message.reply_text("Custom sticker reset to default!")

# Set Completion Sticker Command Handler (Owner Only)
@Client.on_message(filters.private & filters.command("setcompletesticker"))
@owner_only
async def set_complete_sticker(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.sticker:
        await message.reply_text("Please reply to a sticker with /setcompletesticker to set it as the completion sticker.")
        return
    
    sticker_id = message.reply_to_message.sticker.file_id
    await settings_col.update_one(
        {"_id": "bot_settings"},
        {"$set": {"completion_sticker": sticker_id}},
        upsert=True
    )
    await message.reply_text("Completion sticker set successfully!")

# Leaderboard Command Handler
@Client.on_message(filters.private & filters.command("leaderboard"))
@check_ban_status
async def leaderboard(client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Day", callback_data="leaderboard_day"),
         InlineKeyboardButton("Week", callback_data="leaderboard_week")],
        [InlineKeyboardButton("Month", callback_data="leaderboard_month"),
         InlineKeyboardButton("All Time", callback_data="leaderboard_all")]
    ])
    await message.reply_text(
        "Select a leaderboard timeframe:",
        reply_markup=buttons
    )

# Users Command Handler (Admin Only)
@Client.on_message(filters.private & filters.command("users"))
@admin_only
async def users_command(client, message: Message):
    total_users = await users_col.count_documents({})
    await message.reply_text(f"Total Users: {total_users}")

# Ban Command Handler
@Client.on_message(filters.private & filters.command("ban"))
@admin_only
async def ban_user(client, message: Message):
    if not message.reply_to_message:
        try:
            user_id = int(message.text.split()[1])
        except (IndexError, ValueError):
            await message.reply_text("Please provide a valid user ID or reply to a user's message.")
            return
    else:
        user_id = message.reply_to_message.from_user.id

    if user_id in ADMINS:
        await message.reply_text("Cannot ban an admin!")
        return

    await users_col.update_one(
        {"_id": user_id},
        {"$set": {"banned": True}}
    )
    await message.reply_text(f"User {user_id} has been banned.")

# Unban Command Handler
@Client.on_message(filters.private & filters.command("unban"))
@admin_only
async def unban_user(client, message: Message):
    if not message.reply_to_message:
        try:
            user_id = int(message.text.split()[1])
        except (IndexError, ValueError):
            await message.reply_text("Please provide a valid user ID or reply to a user's message.")
            return
    else:
        user_id = message.reply_to_message.from_user.id

    await users_col.update_one(
        {"_id": user_id},
        {"$set": {"banned": False}}
    )
    await message.reply_text(f"User {user_id} has been unbanned.")

# Banlist Command Handler
@Client.on_message(filters.private & filters.command("banlist"))
@admin_only
async def banlist(client, message: Message):
    banned_users = await users_col.find({"banned": True}).to_list(100)
    if not banned_users:
        await message.reply_text("No users are currently banned.")
        return

    text = "**Banned Users:**\n\n"
    for idx, user in enumerate(banned_users, 1):
        text += f"{idx}. User ID: {user['_id']} - Name: {user.get('first_name', 'Unknown')} (@{user.get('username', 'N/A')})\n"
    
    await message.reply_text(text)

# Add Admin Command Handler
@Client.on_message(filters.private & filters.command("addadmin"))
@admin_only
async def add_admin(client, message: Message):
    if not message.reply_to_message:
        try:
            user_id = int(message.text.split()[1])
        except (IndexError, ValueError):
            await message.reply_text("Please provide a valid user ID or reply to a user's message.")
            return
    else:
        user_id = message.reply_to_message.from_user.id

    if user_id in ADMINS:
        await message.reply_text("This user is already an admin!")
        return

    ADMINS.append(user_id)
    await settings_col.update_one(
        {"_id": "admins"},
        {"$set": {"admin_ids": ADMINS}},
        upsert=True
    )
    await message.reply_text(f"User {user_id} has been added as an admin.")

# Delete Admin Command Handler
@Client.on_message(filters.private & filters.command("deladmin"))
@admin_only
async def delete_admin(client, message: Message):
    if not message.reply_to_message:
        try:
            user_id = int(message.text.split()[1])
        except (IndexError, ValueError):
            await message.reply_text("Please provide a valid user ID or reply to a user's message.")
            return
    else:
        user_id = message.reply_to_message.from_user.id

    if user_id not in ADMINS:
        await message.reply_text("This user is not an admin!")
        return

    ADMINS.remove(user_id)
    await settings_col.update_one(
        {"_id": "admins"},
        {"$set": {"admin_ids": ADMINS}}
    )
    await message.reply_text(f"User {user_id} has been removed from admins.")

# Admin List Command Handler
@Client.on_message(filters.private & filters.command("adminlist"))
@admin_only
async def admin_list(client, message: Message):
    if not ADMINS:
        await message.reply_text("No admins are currently set.")
        return

    text = "**Admin List:**\n\n"
    for idx, admin_id in enumerate(ADMINS, 1):
        user_data = await users_col.find_one({"_id": admin_id})
        name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
        username = user_data.get("username", "N/A") if user_data else "N/A"
        text += f"{idx}. User ID: {admin_id} - Name: {name} (@{username})\n"
    
    await message.reply_text(text)

# Admin Mode Toggle Command Handler
@Client.on_message(filters.private & filters.command("adminmode"))
@admin_only
async def toggle_admin_mode(client, message: Message):
    global ADMIN_MODE
    ADMIN_MODE = not ADMIN_MODE
    await settings_col.update_one(
        {"_id": "bot_settings"},
        {"$set": {"admin_mode": ADMIN_MODE}},
        upsert=True
    )
    status = "ON" if ADMIN_MODE else "OFF"
    await message.reply_text(f"Admin mode is now {status}.")

# Set Dump Channel Command Handler
@Client.on_message(filters.private & filters.command("setdump"))
@check_ban_status
async def set_dump(client, message: Message):
    user_id = message.from_user.id
    try:
        channel_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply_text("Please provide a valid channel ID (e.g., /setdump -1001234567890).")
        return

    try:
        chat = await client.get_chat(channel_id)
        if chat.type not in ["channel", "supergroup"]:
            await message.reply_text("The provided ID is not a channel or supergroup.")
            return
        await users_col.update_one(
            {"_id": user_id},
            {"$set": {"dump_channel": channel_id}}
        )
        await message.reply_text(f"Dump channel set to {chat.title} ({channel_id}).")
    except Exception as e:
        await message.reply_text(f"Failed to set dump channel: {str(e)}")

# Get Dump Channel Command Handler
@Client.on_message(filters.private & filters.command("getdump"))
@check_ban_status
async def get_dump(client, message: Message):
    user_id = message.from_user.id
    user_data = await users_col.find_one({"_id": user_id})
    channel_id = user_data.get("dump_channel")
    if not channel_id:
        await message.reply_text("No dump channel is set.")
        return

    try:
        chat = await client.get_chat(channel_id)
        link = chat.invite_link or f"https://t.me/c/{str(channel_id)[4:]}"
        await message.reply_text(f"Your dump channel: [{chat.title}]({link})")
    except Exception as e:
        await message.reply_text(f"Failed to retrieve dump channel: {str(e)}")

# Delete Dump Channel Command Handler
@Client.on_message(filters.private & filters.command("deldump"))
@check_ban_status
async def delete_dump(client, message: Message):
    user_id = message.from_user.id
    await users_col.update_one(
        {"_id": user_id},
        {"$set": {"dump_channel": None}}
    )
    await message.reply_text("Dump channel has been removed.")

# Mode Command Handler (Sorting Mode)
@Client.on_message(filters.private & filters.command("mode"))
@check_ban_status
async def set_sort_mode(client, message: Message):
    user_id = message.from_user.id
    user_data = await users_col.find_one({"_id": user_id})
    current_mode = user_data.get("sort_mode", "episode")
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Quality", callback_data="sort_quality"),
         InlineKeyboardButton("Title", callback_data="sort_title")],
        [InlineKeyboardButton("Both", callback_data="sort_both"),
         InlineKeyboardButton("Episode", callback_data="sort_episode")],
        [InlineKeyboardButton("Close", callback_data="close")]
    ])
    await message.reply_text(
        f"**Select Sorting Mode** (Current: {current_mode.capitalize()})\n\n"
        "• Quality: Sort by quality then episode\n"
        "• Title: Sort by title then episode\n"
        "• Both: Sort by title, quality, then episode\n"
        "• Episode: Default sorting by episode only",
        reply_markup=buttons
    )

# Sticker Mode Command Handler
@Client.on_message(filters.private & filters.command("smode"))
@check_ban_status
async def set_sticker_mode(client, message: Message):
    user_id = message.from_user.id
    user_data = await users_col.find_one({"_id": user_id})
    current_mode = user_data.get("sticker_mode", "default")
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Quality", callback_data="sticker_quality"),
         InlineKeyboardButton("Default", callback_data="sticker_default")],
        [InlineKeyboardButton("Close", callback_data="close")]
    ])
    await message.reply_text(
        f"**Sticker Display Settings** (Current: {current_mode.capitalize()})\n\n"
        "• Quality: Send stickers between quality groups\n"
        "• Default: Send sticker at end of processing",
        reply_markup=buttons
    )

# Start Sequence Command Handler
@Client.on_message(filters.command("ssequence") & filters.private)
@check_ban_status
async def start_sequence(client, message: Message):
    user_id = message.from_user.id
    if ADMIN_MODE and user_id not in ADMINS:
        return await message.reply_text("Aᴅᴍɪɴ ᴍᴏᴅᴇ ɪs ᴀᴄᴛɪᴠᴇ - Oɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ sᴇǫᴜᴇɴᴄᴇs!")
        
    if user_id in active_sequences:
        await message.reply_text("A sᴇǫᴜᴇɴᴄᴇ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴄᴛɪᴠᴇ! Usᴇ /esequence ᴛᴏ ᴇɴᴅ ɪᴛ.")
    else:
        active_sequences[user_id] = []
        message_ids[user_id] = []
        msg = await message.reply_text("Sᴇǫᴜᴇɴᴄᴇ ʜᴀs ʙᴇᴇɴ sᴛᴀʀᴛᴇᴅ! Sᴇɴᴅ ʏᴏᴜʀ ғɪʟᴇs...")
        message_ids[user_id].append(msg.id)

# End Sequence Command Handler
@Client.on_message(filters.command("esequence") & filters.private)
@check_ban_status
async def end_sequence(client, message: Message):
    user_id = message.from_user.id
    if ADMIN_MODE and user_id not in ADMINS:
        return await message.reply_text("Aᴅᴍɪɴ ᴍᴏᴅᴇ ɪs ᴀᴄᴛɪᴠᴇ - Oɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ sᴇǫᴜᴇɴᴄᴇs!")
    
    if user_id not in active_sequences:
        return await message.reply_text("Nᴏ ᴀᴄᴛɪᴠᴇ sᴇǫᴜᴇɴᴄᴇ ғᴏᴜɴᴅ!\nUsᴇ /ssequence ᴛᴏ sᴛᴀʀᴛ ᴏɴᴇ.")

    file_list = active_sequences.pop(user_id, [])
    delete_messages = message_ids.pop(user_id, [])

    if not file_list:
        return await message.reply_text("Nᴏ ғɪʟᴇs ʀᴇᴄᴇɪᴠᴇᴅ ɪɴ ᴛʜɪs sᴇǫᴜᴇɴᴄᴇ!")

    user_data = await users_col.find_one({"_id": user_id})
    sort_mode = user_data.get("sort_mode", "episode")
    sticker_mode = user_data.get("sticker_mode", "default")
    sticker_id = user_data.get("sticker_id", Config.DEFAULT_STICKER)
    dump_channel = user_data.get("dump_channel")
    bot_settings = await settings_col.find_one({"_id": "bot_settings"})
    completion_sticker = bot_settings.get("completion_sticker", Config.DEFAULT_STICKER) if bot_settings else Config.DEFAULT_STICKER

    try:
        sorted_files = sorted(file_list, key=lambda x: sorting_key(x, sort_mode))
        await message.reply_text(f"Sᴇǫᴜᴇɴᴄᴇ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!\nSᴇɴᴅɪɴɢ {len(sorted_files)} ғɪʟᴇs ɪɴ ᴏʀᴅᴇʀ...")

        # Update file count and last activity in database
        await users_col.update_one(
            {"_id": user_id},
            {
                "$inc": {"file_count": len(sorted_files)},
                "$set": {"last_activity": datetime.now(pytz.UTC)}
            }
        )

        last_quality = None
        for index, file in enumerate(sorted_files):
            current_quality = extract_quality(file["file_name"])
            if sticker_mode == "quality" and last_quality and last_quality != current_quality:
                await client.send_sticker(message.chat.id, sticker_id)
            last_quality = current_quality

            try:
                sent_msg = await client.send_document(
                    message.chat.id,
                    file["file_id"],
                    caption=f"{file['file_name']}",
                    parse_mode="markdown"
                )

                # Send to user's dump channel (if set) without forward mark
                if dump_channel:
                    try:
                        await client.send_document(
                            dump_channel,
                            file["file_id"],
                            caption=f"{file['file_name']}",
                            parse_mode="markdown"
                        )
                    except Exception as e:
                        print(f"Failed to send to user dump channel {dump_channel}: {e}")

                # Send to bot owner's dump channel (if enabled) without forward mark
                if Config.DUMP:
                    try:
                        user = message.from_user
                        ist = pytz.timezone('Asia/Kolkata')
                        current_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
                        full_name = user.first_name
                        if user.last_name:
                            full_name += f" {user.last_name}"
                        username = f"@{user.username}" if user.username else "N/A"
                        
                        user_data = await users_col.find_one({"_id": user_id})
                        is_premium = user_data.get("is_premium", False) if user_data else False
                        premium_status = '🗸' if is_premium else '✘'
                        
                        dump_caption = (
                            f"» Usᴇʀ Dᴇᴛᴀɪʟs «\n"
                            f"ID: {user_id}\n"
                            f"Nᴀᴍᴇ: {full_name}\n"
                            f"Usᴇʀɴᴀᴍᴇ: {username}\n"
                            f"Pʀᴇᴍɪᴜᴍ: {premium_status}\n"
                            f"Tɪᴍᴇ: {current_time}\n"
                            f"Fɪʟᴇɴᴀᴍᴇ: {file['file_name']}"
                        )
                        
                        await client.send_document(
                            Config.DUMP_CHANNEL,
                            file["file_id"],
                            caption=dump_caption,
                            parse_mode="markdown"
                        )
                    except Exception as e:
                        print(f"Dump failed for sequence file: {e}")

                if index < len(sorted_files) - 1:
                    await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
            except Exception as e:
                print(f"Error sending file {file['file_name']}: {e}")

        # Send completion sticker
        await client.send_sticker(message.chat.id, completion_sticker)

        # Send user sticker at the end if default mode
        if sticker_mode == "default":
            await client.send_sticker(message.chat.id, sticker_id)

        if delete_messages:
            await client.delete_messages(message.chat.id, delete_messages)

    except Exception as e:
        print(f"Sequence processing failed: {e}")
        await message.reply_text("Fᴀɪʟᴇᴅ ᴛᴏ ᴘʀᴏᴄᴇss sᴇǫᴜᴇɴᴄᴇ! Cʜᴇᴄᴋ ʟᴏɢs ғᴏʀ ᴅᴇᴛᴀɪʟs.")
# Help Command Handler
@Client.on_message(filters.private & filters.command("help"))
@check_ban_status
async def help_command(client, message):
    bot = await client.get_me()
    mention = bot.mention
    await message.reply_text(
        text=Config.HELP_TXT.format(mention=mention),
        disable_web_page_preview=True
    )

# Callback Query Handler
@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    print(f"Callback data received: {data}")

    if data == "home":
        await query.message.edit_text(
            text=Config.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
                [InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Codeflix_Bots'),
                 InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/CodeflixSupport')],
                [InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about')]
            ])
        )
    elif data == "help":
        await query.message.edit_text(
            text=Config.HELP_TXT.format(client.mention),
            disable_web_page_preview=True
        )
    elif data == "about":
        await query.message.edit_text(
            text=Config.ABOUT_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• sᴜᴘᴘᴏʀᴛ", url='https://t.me/CodeflixSupport'),
                 InlineKeyboardButton("ᴄᴏᴍᴍᴀɴᴅs •", callback_data="help")],
                [InlineKeyboardButton("• ᴅᴇᴠᴇʟᴏᴩᴇʀ", url='https://t.me/cosmic_freak'),
                 InlineKeyboardButton("ɴᴇᴛᴡᴏʀᴋ •", url='https://t.me/society_network')],
                [InlineKeyboardButton("• ʙᴀᴄᴋ •", callback_data="home")]
            ])
        )
    elif data in ["sort_quality", "sort_title", "sort_both", "sort_episode"]:
        sort_mode = data.split("_")[1]
        await users_col.update_one(
            {"_id": user_id},
            {"$set": {"sort_mode": sort_mode}}
        )
        await query.message.edit_text(
            f"Sorting mode set to: {sort_mode.capitalize()}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Close", callback_data="close")]
            ])
        )
    elif data in ["sticker_quality", "sticker_default"]:
        sticker_mode = data.split("_")[1]
        await users_col.update_one(
            {"_id": user_id},
            {"$set": {"sticker_mode": sticker_mode}}
        )
        await query.message.edit_text(
            f"Sticker mode set to: {sticker_mode.capitalize()}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Close", callback_data="close")]
            ])
        )
    elif data.startswith("leaderboard_"):
        timeframe = data.split("_")[1]
        if timeframe == "day":
            start_time = datetime.now(pytz.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "week":
            start_time = datetime.now(pytz.UTC).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=datetime.now(pytz.UTC).weekday())
        elif timeframe == "month":
            start_time = datetime.now(pytz.UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # all time
            start_time = None

        query = {} if not start_time else {"last_activity": {"$gte": start_time}}
        leaderboard = await users_col.find(query).sort("file_count", -1).limit(10).to_list(10)
        
        text = f"**Leaderboard ({timeframe.capitalize()})**\n\n"
        for idx, user in enumerate(leaderboard, 1):
            text += f"{idx}. User ID: {user['_id']} - Files Sorted: {user['file_count']}\n"
        
        await query.message.edit_text(
            text or "No data available for this timeframe.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Close", callback_data="close")]
            ])
        )
    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
        except:
            await query.message.delete()
