import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified, ChatAdminRequired
from config import Config
from helper.database import Database
from helper.texts import Txt
from helper.utils import send_log

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
app = Client(
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Initialize database
db = Database(Config.DB_URL, Config.DB_NAME)

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    logger.info(f"Start command received from user {message.from_user.id}")
    await db.add_user(client, message)
    await message.reply_text(
        text=Txt.START_TXT.format(message.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
            [InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/FILE_SHARINGBOTS'),
             InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/CodeflixSupport')],
            [InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about'),
             InlineKeyboardButton('sᴏᴜʀᴄᴇ •', callback_data='source')]
        ])
    )

# Help command
@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    logger.info(f"Help command received from user {message.from_user.id}")
    await message.reply_text(
        text=Txt.HELP_TXT.format((await client.get_me()).mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("• ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ғᴏʀᴍᴀᴛ •", callback_data='file_names')],
            [InlineKeyboardButton('• ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='thumbnail'),
             InlineKeyboardButton('ᴄᴀᴘᴛɪᴏɴ •', callback_data='caption')],
            [InlineKeyboardButton('• ᴍᴇᴛᴀᴅᴀᴛᴀ', callback_data='meta'),
             InlineKeyboardButton('ᴅᴏɴᴀᴛᴇ •', callback_data='donate')],
            [InlineKeyboardButton('• ʜᴏᴍᴇ', callback_data='home')]
        ])
    )

# About command
@app.on_message(filters.command("about") & filters.private)
async def about_command(client, message):
    logger.info(f"About command received from user {message.from_user.id}")
    await message.reply_text(
        text=Txt.ABOUT_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("• sᴜᴘᴘᴏʀᴛ", url='https://t.me/ahss_help_zone'),
             InlineKeyboardButton("ᴄᴏᴍᴍᴀɴᴅs •", callback_data="help")],
            [InlineKeyboardButton("• ᴅᴇᴠᴇʟᴏᴘᴇʀ", url='https://t.me/cosmic_awaken'),
             InlineKeyboardButton("ɴᴇᴛᴡᴏʀᴋ •", url='https://t.me/society_network')],
            [InlineKeyboardButton("• ʙᴀᴄᴋ •", callback_data="home")]
        ])
    )

# Extraction command
@app.on_message(filters.command("extraction") & filters.private)
async def extraction_command(client, message):
    logger.info(f"Extraction command received from user {message.from_user.id}")
    await message.reply_text(
        text="➪ Please select an option to extract metadata from:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ғɪʟᴇɴᴀᴍᴇ", callback_data="filename")],
            [InlineKeyboardButton("ғɪʟᴇᴄᴀᴘᴛɪᴏɴ", callback_data="filecaption")]
        ])
    )

# Autorename command
@app.on_message(filters.command("autorename") & filters.private)
async def autorename_command(client, message):
    logger.info(f"Autorename command received from user {message.from_user.id}")
    if len(message.command) < 2:
        await message.reply_text(
            text=Txt.FILE_NAME_TXT.format(format_template=await db.get_format_template(message.from_user.id)),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    else:
        format_template = " ".join(message.command[1:])
        try:
            await db.set_format_template(message.from_user.id, format_template)
            await message.reply_text(
                f"➪ Autorename format set to:\n\n`{format_template}`\n\nSend a file to rename!"
            )
        except Exception as e:
            logger.error(f"Error setting format template for user {message.from_user.id}: {e}")
            await message.reply_text("➪ Error: Couldn't set the format template.")

# Thumbnail command
@app.on_message(filters.command("thumbnail") & filters.private)
async def thumbnail_command(client, message):
    logger.info(f"Thumbnail command received from user {message.from_user.id}")
    await message.reply_text(
        text=Txt.THUMBNAIL_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close")]
        ])
    )

# Caption command
@app.on_message(filters.command("caption") & filters.private)
async def caption_command(client, message):
    logger.info(f"Caption command received from user {message.from_user.id}")
    if len(message.command) < 2:
        await message.reply_text(
            text=Txt.CAPTION_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    else:
        caption = " ".join(message.command[1:])
        try:
            await db.set_caption(message.from_user.id, caption)
            await message.reply_text(f"➪ Caption set to:\n\n`{caption}`")
        except Exception as e:
            logger.error(f"Error setting caption for user {message.from_user.id}: {e}")
            await message.reply_text("➪ Error: Couldn't set the caption.")

# Metadata command
@app.on_message(filters.command("metadata") & filters.private)
async def metadata_command(client, message):
    logger.info(f"Metadata command received from user {message.from_user.id}")
    await message.reply_text(
        text=Txt.SEND_METADATA,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close")]
        ])
    )

# Callback query handler
@app.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    logger.info(f"Callback data received: {data}")

    # Handle /extraction callbacks
    if data in ["filename", "filecaption"]:
        try:
            choice = data
            updated_keyboard = [
                [InlineKeyboardButton("ғɪʟᴇɴᴀᴍᴇ ✅" if choice == "filename" else "ғɪʟᴇɴᴀᴍᴇ", callback_data="filename")],
                [InlineKeyboardButton("ғɪʟᴇᴄᴀᴘᴛɪᴏɴ ✅" if choice == "filecaption" else "ғɪʟᴇᴄᴀᴘᴛɪᴏɴ", callback_data="filecaption")]
            ]

            try:
                await query.message.edit_reply_markup(InlineKeyboardMarkup(updated_keyboard))
                logger.info(f"Updated keyboard for user {user_id}")
            except MessageNotModified:
                logger.debug(f"Keyboard unchanged for user {user_id}")
            except ChatAdminRequired:
                logger.error(f"ChatAdminRequired for keyboard update")
                await query.message.reply_text("Error: Bot lacks admin rights.")
                await query.answer("Bot needs admin rights!", show_alert=True)
                return
            except Exception as e:
                logger.error(f"Keyboard update failed for user {user_id}: {e}")
                await query.message.reply_text("➪ Error: Couldn't update buttons.")
                return

            success = await db.set_user_choice(user_id, choice)
            if not success:
                logger.error(f"Failed to save choice '{choice}' for user {user_id}")
                await query.message.reply_text("➪ Error: Couldn't save your choice.")
                await query.answer("Database error!", show_alert=True)
                return

            await query.message.reply_text(
                f"Please send the file to rename using its {choice}."
            )
            await query.answer("Option selected!")
        except ChatAdminRequired:
            logger.error(f"ChatAdminRequired in callback")
            await query.message.reply_text("Error: Bot lacks admin rights.")
            await query.answer("Bot needs admin rights!", show_alert=True)
        except Exception as e:
            logger.error(f"Callback error for user {user_id}: {e}")
            await query.message.reply_text("➪ Error: Something went wrong.")
            await query.answer("Error occurred!", show_alert=True)

    # Handle other callbacks
    elif data == "home":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
                [InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/FILE_SHARINGBOTS'),
                 InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/CodeflixSupport')],
                [InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about'),
                 InlineKeyboardButton('sᴏᴜʀᴄᴇ •', callback_data='source')]
            ])
        )
    elif data == "caption":
        await query.message.edit_text(
            text=Txt.CAPTION_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• sᴜᴘᴘᴏʀᴛ", url='https://t.me/ahss_help_zone'),
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "help":
        await query.message.edit_text(
            text=Txt.HELP_TXT.format((await client.get_me()).mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ғᴏʀᴍᴀᴛ •", callback_data='file_names')],
                [InlineKeyboardButton('• ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='thumbnail'),
                 InlineKeyboardButton('ᴄᴀᴘᴛɪᴏɴ •', callback_data='caption')],
                [InlineKeyboardButton('• ᴍᴇᴛᴀᴅᴀᴛᴀ', callback_data='meta'),
                 InlineKeyboardButton('ᴅᴏɴᴀᴛᴇ •', callback_data='donate')],
                [InlineKeyboardButton('• ʜᴏᴍᴇ', callback_data='home')]
            ])
        )
    elif data == "meta":
        await query.message.edit_text(
            text=Txt.SEND_METADATA,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"),
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "donate":
        await query.message.edit_text(
            text=Txt.DONATE_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="help"),
                 InlineKeyboardButton("ᴏᴡɴᴇʀ •", url='https://t.me/i_killed_my_clan')]
            ])
        )
    elif data == "file_names":
        format_template = await db.get_format_template(user_id)
        await query.message.edit_text(
            text=Txt.FILE_NAME_TXT.format(format_template=format_template),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"),
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "thumbnail":
        await query.message.edit_caption(
            caption=Txt.THUMBNAIL_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"),
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "metadatax":
        await query.message.edit_caption(
            caption=Txt.SEND_METADATA,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"),
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ])
        )
    elif data == "source":
        await query.message.edit_caption(
            caption=Txt.SOURCE_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"),
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="home")]
            ])
        )
    elif data == "premiumx":
        await query.message.edit_caption(
            caption=Txt.PREMIUM_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="help"),
                 InlineKeyboardButton("ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •", url='https://t.me/proobito')]
            ])
        )
    elif data == "plans":
        await query.message.edit_caption(
            caption=Txt.PREPLANS_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"),
                 InlineKeyboardButton("ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •", url='https://t.me/proobito')]
            ])
        )
    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• sᴜᴘᴘᴏʀᴛ", url='https://t.me/ahss_help_zone'),
                 InlineKeyboardButton("ᴄᴏᴍᴍᴀɴᴅs •", callback_data="help")],
                [InlineKeyboardButton("• ᴅᴇᴠᴇʟᴏᴘᴇʀ", url='https://t.me/cosmic_awaken'),
                 InlineKeyboardButton("ɴᴇᴛᴡᴏʀᴋ •", url='https://t.me/society_network')],
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

# Run the bot
if __name__ == "__main__":
    logger.info("Starting Tessia Bot...")
    app.run()
