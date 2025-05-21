import re, os, time
from os import environ, getenv

id_pattern = re.compile(r'^.\d+$')

class Config:
    # Bot token from BotFather
    API_ID = os.environ.get("API_ID", "28264594")
    API_HASH = os.environ.get("API_HASH", "94ca8a089020a2290fd29a41f18acb94")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "7932515290:AAErP6vIZw6JuI79RN2pJohjLfnDMCTjSEY")
    USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", "")

    # Database settings
    DB_NAME = os.environ.get("DB_NAME", "Rename")
    DB_URL = os.environ.get("DB_URL", "mongodb+srv://spxsolo:umaid2008@cluster0.7fbux.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    PORT = os.environ.get("PORT", "6970")

    # Bot uptime
    BOT_UPTIME = time.time()

    # Media settings
    START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/223de6d04641c9068251c-31b2b459f088ee3cf6.jpg")
    DEFAULT_STICKER = "CAACAgUAAxkBAAEFBAVoH4qTFGwjwrCkLJPeM0HjglJpYgACXAgAArSfGVXK3kCuYAiK2B4E"
    FORCE_PIC = os.environ.get("FORCE_PIC", "https://telegra.ph/file/27484e767ef1ddd1da72c-162a07065bf8208ed6.jpg")
    PICS = (environ.get('PICS', 'https://telegra.ph/file/27484e767ef1ddd1da72c-162a07065bf8208ed6.jpg https://telegra.ph/file/223de6d04641c9068251c-31b2b459f088ee3cf6.jpg https://telegra.ph/file/e3406c9810b5a3f6dd7bd-fe243b6093dbd55970.jpg')).split()

    # Admin and owner settings
    OWNER_ID = 5585016974
    ADMINS = [int(admins) if id_pattern.search(admins) else admins for admins in os.environ.get('ADMINS', '5585016974 6497757690 7328629001').split()]
    ADMINS = [int(admins) if id_pattern.search(admin) else admins for admins in os.environ.get('ADMINS', '5585016974 6497757690 7328629001').split()]

    # Channel settings
    FORCE_SUB_CHANNELS = os.environ.get('FORCE_SUB_CHANNELS', 'animes_crew, weebxcrew').split(', ')
    LOG_CHANNEL = os.environ.get("LOG_CHANNEL", "-1001868871195")
    DUMP_CHANNEL = os.environ.get("DUMP_CHANNEL", "-1001868871195")
    DUMP = True

    # Admin mode
    ADMIN_MODE = False

class Txt:
    START_TXT = """<b>ʜᴇʏ! {}  

» ɪ ᴀᴍ ᴀᴅᴠᴀɴᴄᴇᴅ ʀᴇɴᴀᴍᴇ ʙᴏᴛ! ᴡʜɪᴄʜ ᴄᴀɴ ᴀᴜᴛᴏʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ғɪʟᴇs ᴡɪᴛʜ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴀɴᴅ ᴛʜᴜᴍʙɴᴀɪʟ ᴀɴᴅ ᴀʟsᴏ sᴇǫᴜᴇɴᴄᴇ ᴛʜᴇᴍ ᴘᴇʀғᴇᴄᴛʟʏ</b>"""
    
    HELP_TXT = """<b>Available commands for {mention}:

» Send files or videos to auto-queue them for processing
» /ssequence - Start a file sequence manually
» /esequence - End and process the sequence
» /setsticker - Set a custom sticker (reply to a sticker)
» /getsticker - View your current sticker
» /delsticker - Reset to default sticker
» /mode - Set sorting mode (quality, title, both, episode)
» /smode - Set sticker display mode (quality, default)
» /setdump - Set your dump channel (e.g., /setdump -1001234567890)
» /getdump - View your dump channel
» /deldump - Remove your dump channel
» /leaderboard - View top users by file count
» /bought - Submit premium payment screenshot (reply to a photo)

Admin commands:
» /users - View total users
» /ban - Ban a user (reply or provide ID)
» /unban - Unban a user (reply or provide ID)
» /banlist - List banned users
» /addadmin - Add an admin (reply or provide ID)
» /deladmin - Remove an admin (reply or provide ID)
» /adminlist - List admins
» /adminmode - Toggle admin mode

Owner commands:
» /setcompletesticker - Set completion sticker (reply to a sticker)</b>"""
    
    ABOUT_TXT = """<b>❍ ᴍʏ ɴᴀᴍᴇ : <a href="https://t.me/codeflix_bots">ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ</a>
❍ ᴅᴇᴠᴇʟᴏᴩᴇʀ : <a href="https://t.me/cosmic_freak">ʏᴀᴛᴏ</a>
❍ ɢɪᴛʜᴜʙ : <a href="https://github.com/cosmic_freak">ʏᴀᴛᴏ</a>
❍ ʟᴀɴɢᴜᴀɢᴇ : <a href="https://www.python.org/">ᴘʏᴛʜᴏɴ</a>
❍ ᴅᴀᴛᴀʙᴀꜱᴇ : <a href="https://www.mongodb.com/">ᴍᴏɴɢᴏ ᴅʙ</a>
❍ ʜᴏꜱᴛᴇᴅ ᴏɴ : <a href="https://t.me/codeflix_bots">ᴠᴘs</a>
❍ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ : <a href="https://t.me/animes_cruise">ᴀɴɪᴍᴇ ᴄʀᴜɪsᴇ</a>

➻ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ғᴏʀ ɢᴇᴛᴛɪɴɢ ʙᴀsɪᴄ ʜᴇʟᴩ ᴀɴᴅ ɪɴғᴏ ᴀʙᴏᴜᴛ ᴍᴇ.</b>"""
