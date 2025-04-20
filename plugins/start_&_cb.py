import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helper.database import *
from config import Config, Txt
import logging
from pyrogram.errors import FloodWait, MessageNotModified, ChatAdminRequired
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize MongoDB (already imported as codeflixbots)
db = codeflixbots

# Start Command Handler
@Client.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    user = message.from_user
    await db.add_user(client, message)

    # Initial interactive text and sticker sequence
    m = await message.reply_text("ᴋᴏɴɴɪᴄʜɪᴡᴀ..ɪ'ᴍ ᴋᴀɴᴀᴏ!\nᴡᴀɪᴛ ᴀ ᴍᴏᴍᴇɴᴛ. . .<blockquote>")
    await asyncio.sleep(0.4)
    await m.edit_text("🎊")
    await asyncio.sleep(0.5)
    await m.edit_text("⚡")
    await asyncio.sleep(0.5)
    await m.edit_text("ᴀʀᴀ ᴀʀᴀ!...")
    await asyncio.sleep(0.4)
    await m.delete()

    # Send sticker after the text sequence
    await message.reply_sticker("CAACAgUAAxkBAAECroBmQKMAAQ-Gw4nibWoj_pJou2vP1a4AAlQIAAIzDxlVkNBkTEb1Lc4eBA")

    # Define buttons for the start message
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')
        ],
        [
            InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/FILE_SHARINGBOTS'),
            InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/ahss_help_zone')
        ],
        [
            InlineKeyboardButton('• ᴀʙᴏᴜᴛ• ', callback_data='about')
        ]
    ])

    # Send start message with or without picture
    if Config.START_PIC:
        await message.reply_photo(
            Config.START_PIC,
            caption=Txt.START_TXT.format(user.mention),
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            text=Txt.START_TXT.format(user.mention),
            reply_markup=buttons,
            disable_web_page_preview=True
        )

# Help Command Handler
@Client.on_message(filters.private & filters.command("help"))
async def help_command(client, message):
    bot = await client.get_me()
    mention = bot.mention

    await message.reply_text(
        text=Txt.HELP_TXT.format(mention=mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("• ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ғᴏʀᴍᴀᴛ •", callback_data='file_names')],
            [InlineKeyboardButton('• ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='thumbnail'), InlineKeyboardButton('ᴄᴀᴘᴛɪᴏɴ •', callback_data='caption')],
            [InlineKeyboardButton('• ᴍᴇᴛᴀᴅᴀᴛᴀ', callback_data='meta'), InlineKeyboardButton('ᴅᴏɴᴀᴛᴇ •', callback_data='donate')],
            [InlineKeyboardButton('• ʜᴏᴍᴇ', callback_data='home')]
        ])
    )

# Donation Command Handler
@Client.on_message(filters.command("donate"))
async def donation(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="help"), InlineKeyboardButton(text="ᴏᴡɴᴇʀ", url='https://t.me/proobito')]
    ])
    yt = await message.reply_photo(photo='https://envs.sh/ZsI.png?DpE8x=1', caption=Txt.DONATE_TXT, reply_markup=buttons)
    await asyncio.sleep(300)
    await yt.delete()
    await message.delete()

# Premium Command Handler
@Client.on_message(filters.command("premium"))
async def getpremium(bot, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/proobito"), InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ])
    yt = await message.reply_photo(photo='https://envs.sh/ZsI.png?DpE8x=1', caption=Txt.PREMIUM_TXT, reply_markup=buttons)
    await asyncio.sleep(300)
    await yt.delete()
    await message.delete()

# Plan Command Handler
@Client.on_message(filters.command("plan"))
async def premium(bot, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("sᴇɴᴅ ss", url="https://t.me/proobito"), InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ])
    yt = await message.reply_photo(photo='https://envs.sh/ZsI.png?DpE8x=1', caption=Txt.PREPLANS_TXT, reply_markup=buttons)
    await asyncio.sleep(300)
    await yt.delete()
    await message.delete()

# Bought Command Handler
@Client.on_message(filters.command("bought") & filters.private)
async def bought(client, message):
    msg = await message.reply('Wait im checking...')
    replied = message.reply_to_message

    if not replied:
        await msg.edit("<b>Please reply with the screenshot of your payment for the premium purchase to proceed.\n\nFor example, first upload your screenshot, then reply to it using the '/bought' command</b>")
    elif replied.photo:
        await client.send_photo(
            chat_id=Config.LOG_CHANNEL,
            photo=replied.photo.file_id,
            caption=f'<b>User - {message.from_user.mention}\nUser id - <code>{message.from_user.id}</code>\nUsername - <code>{message.from_user.username}</code>\nName - <code>{message.from_user.first_name}</code></b>',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Close", callback_data="close_data")]
            ])
        )
        await msg.edit_text('<b>Your screenshot has been sent to Admins</b>')

# Extraction Command Handler
@Client.on_message(filters.command("extraction") & filters.private)
async def extraction_command(client: Client, message: Message) -> None:
    try:
        keyboard = [
            [InlineKeyboardButton("ғɪʟᴇɴᴀᴍᴇ", callback_data="filename")],
            [InlineKeyboardButton("ғɪʟᴇᴄᴀᴘᴛɪᴏɴ", callback_data="filecaption")]
        ]
        await message.reply_text(
            "⚙️ Select the extraction method:<blockquote>",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logging.info(f"Sent extraction options to user {message.from_user.id}")
    except ChatAdminRequired:
        logging.error(f"ChatAdminRequired in extraction_command")
        await message.reply_text("Error: Bot lacks admin rights.")
    except Exception as e:
        logging.error(f"Error in extraction_command: {e}")
        await message.reply_text("Error: Failed to send options.")

# Clear Command Handler
user_tasks = {}  # Track user tasks globally
# Callback Query Handler (Merged for all commands)
@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    logging.info(f"Callback data received: {data}")

    # Handle /extraction callbacks
    if data in ["• ғɪʟᴇɴᴀᴍᴇ", "ғɪʟᴇᴄᴀᴘᴛɪᴏɴ •"]:
        try:
            choice = data
            updated_keyboard = [
                [InlineKeyboardButton("ғɪʟᴇɴᴀᴍᴇ ✅" if choice == "filename" else "Filename", callback_data="filename")],
                [InlineKeyboardButton("ғɪʟᴇᴄᴀᴘᴛɪᴏɴ ✅" if choice == "filecaption" else "Filecaption", callback_data="filecaption")]
            ]

            try:
                await query.message.edit_reply_markup(InlineKeyboardMarkup(updated_keyboard))
                logging.info(f"Updated keyboard for user {user_id}")
            except MessageNotModified:
                logging.debug(f"Keyboard unchanged for user {user_id}")
            except ChatAdminRequired:
                logging.error(f"ChatAdminRequired for keyboard update")
                await query.message.reply_text("Error: Bot lacks admin rights.")
                await query.answer("Bot needs admin rights!", show_alert=True)
                return
            except Exception as e:
                logging.error(f"Keyboard update failed for user {user_id}: {e}")
                await query.message.reply_text("➪ Error: Couldn't update buttons.<blockquote>")
                return

            success = await db.set_user_choice(user_id, choice)
            if not success:
                logging.error(f"Failed to save choice '{choice}' for user {user_id}")
                await query.message.reply_text("➪ Error: Couldn't save your choice.<blockquote>")
                await query.answer("➪ Database error!<blockquote>", show_alert=True)
                return

            await query.message.reply_text(
                f"Please send the file to rename using its {choice}."
            )
            await query.answer("➪ Option selected!")
        except ChatAdminRequired:
            logging.error(f"ChatAdminRequired in callback")
            await query.message.reply_text("›› Error: Bot lacks admin rights.<blockquote>")
            await query.answer("›› Bot needs admin rights!<blockquote>", show_alert=True)
        except Exception as e:
            logging.error(f"Callback error for user {user_id}: {e}")
            await query.message.reply_text("➪ Error: Something went wrong.<blockquote>")
            await query.answer("››Error occurred!<blockquote>", show_alert=True)

    # Handle other callbacks (home, help, etc.)
    elif data == "home":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
                [InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/FILE_SHARINGBOTS'), InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/CodeflixSupport')],
                [InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about'), InlineKeyboardButton('sᴏᴜʀᴄᴇ •', callback_data='source')]
            ])
        )
    elif data == "caption":
        await query.message.edit_text(
            text=Txt.CAPTION_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• sᴜᴘᴘᴏʀᴛ", url='https://t.me/ahss_help_zone'), InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "help":
        await query.message.edit_text(
            text=Txt.HELP_TXT.format((await client.get_me()).mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ғᴏʀᴍᴀᴛ •", callback_data='file_names')],
                [InlineKeyboardButton('• ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='thumbnail'), InlineKeyboardButton('ᴄᴀᴘᴛɪᴏɴ •', callback_data='caption')],
                [InlineKeyboardButton('• ᴍᴇᴛᴀᴅᴀᴛᴀ', callback_data='meta'), InlineKeyboardButton('ᴅᴏɴᴀᴛᴇ •', callback_data='donate')],
                [InlineKeyboardButton('• ʜᴏᴍᴇ', callback_data='home')]
            ])
        )
    elif data == "meta":
        await query.message.edit_text(
            text=Txt.SEND_METADATA,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "donate":
        await query.message.edit_text(
            text=Txt.DONATE_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="help"), InlineKeyboardButton("ᴏᴡɴᴇʀ •", url='https://t.me/i_killed_my_clan')]
            ])
        )
    elif data == "file_names":
        format_template = await db.get_format_template(user_id)
        await query.message.edit_text(
            text=Txt.FILE_NAME_TXT.format(format_template=format_template),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "thumbnail":
        await query.message.edit_caption(
            caption=Txt.THUMBNAIL_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "metadatax":
        await query.message.edit_caption(
            caption=Txt.SEND_METADATA,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "source":
        await query.message.edit_caption(
            caption=Txt.SOURCE_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="home")]
            ])
        )
    elif data == "premiumx":
        await query.message.edit_caption(
            caption=Txt.PREMIUM_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="help"), InlineKeyboardButton("ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •", url='https://t.me/proobito')]
            ])
        )
    elif data == "plans":
        await query.message.edit_caption(
            caption=Txt.PREPLANS_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •", url='https://t.me/proobito')]
            ])
        )
    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• sᴜᴘᴘᴏʀᴛ", url='https://t.me/ahss_help_zone'), InlineKeyboardButton("ᴄᴏᴍᴍᴀɴᴅs •", callback_data="help")],
                [InlineKeyboardButton("• ᴅᴇᴠᴇʟᴏᴘᴇʀ", url='https://t.me/cosmic_awaken'), InlineKeyboardButton("ɴᴇᴛᴡᴏʀᴋ •", url='https://t.me/society_network')],
                [InlineKeyboardButton("• ʙᴀᴄᴋ •", callback_data="home")]
            ])
        )
    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
            await query.message.continue_propagation()
        except:
            await query.message.delete()
            await query.message.continue_propagation()

@Client.on_message(filters.command("clear") & filters.private)
async def clear_tasks(client, message):
    user_id = message.from_user.id
    if user_id not in user_tasks or not user_tasks[user_id]:
        await message.reply_text("›› No active tasks to clear!<blockquote>")
        return
    
    try:
        for task in user_tasks[user_id]:
            if not task.done():
                task.cancel()
        user_tasks[user_id] = []
        await message.reply_text("➪ All your tasks have been cleared!<blockquote>")
        logger.info(f"›› Cleared all tasks for user {user_id}<blockquote>")
    except Exception as e:
        logger.error(f"Error clearing tasks for user {user_id}: {e}")
        await message.reply_text(f"Failed to clear tasks: {str(e)}")

@Client.on_message(filters.command("upscale") & filters.private & filters.photo)
async def upscale_photo(client, message):
    user_id = message.from_user.id
    input_path = f"temp/{user_id}_input.jpg"
    output_path = f"temp/{user_id}_upscaled.jpg"
    
    os.makedirs("temp", exist_ok=True)
    
    try:
        # Download the photo
        await message.reply_text("›› Downloading your photo...<blockquote>")
        await client.download_media(message.photo, file_name=input_path)
        
        # Upscale the image
        await message.reply_text("›› Upscaling your photo...<blockquote>")
        img = cv2.imread(input_path)
        if img is None:
            raise ValueError("Failed to load image<blockquote>")
        
        height, width = img.shape[:2]
        new_width = int(width * 2)
        new_height = int(height * 2)
        upscaled = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        cv2.imwrite(output_path, upscaled, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        
        # Send upscaled photo
        await message.reply_text("›› Uploading upscaled photo...<blockquote>")
        await client.send_photo(
            chat_id=message.chat.id,
            photo=output_path,
            caption="Upscaled photo"
        )
        logger.info(f"›› Upscaled photo sent to user {user_id}<blockquote>")
    
    except Exception as e:
        logger.error(f"Upscale error for user {user_id}<blockquote>: {e}")
        await message.reply_text(f"Error upscaling photo<blockquote>: {str(e)}")
    
    finally:
        # Cleanup
        for path in (input_path, output_path):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.error(f"Error removing {path}: {e}")


        
