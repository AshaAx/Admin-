# main.py

import os
import time
import shutil
import tempfile
import telebot
import yt_dlp

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# =====================================================
# BOT CONFIG
# =====================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

# =====================================================
# REMOVE OLD WEBHOOK
# =====================================================

try:
    bot.remove_webhook()
    time.sleep(2)
    print("✅ Webhook Removed")
except Exception as e:
    print(e)

# =====================================================
# KEYBOARD
# =====================================================

def keyboard():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        KeyboardButton("𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋")
    )

    return kb

# =====================================================
# SAFE DELETE
# =====================================================

def cleanup(folder):

    try:
        shutil.rmtree(folder)
    except:
        pass

# =====================================================
# YOUTUBE AUDIO DOWNLOAD
# =====================================================

def yt_audio(url):

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {

        "format": "bestaudio/best",

        "outtmpl": f"{temp_dir}/%(title)s.%(ext)s",

        "quiet": True,

        "noplaylist": True,

        "cookiefile": None,

        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },

        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            title = info.get(
                "title",
                "Unknown"
            )

            uploader = info.get(
                "uploader",
                "Unknown"
            )

        for file in os.listdir(temp_dir):

            if file.endswith(".mp3"):

                return (
                    os.path.join(temp_dir, file),
                    title,
                    uploader,
                    temp_dir
                )

    except Exception as e:

        print(e)

    cleanup(temp_dir)

    return None, None, None, None

# =====================================================
# YOUTUBE VIDEO DOWNLOAD
# =====================================================

def yt_video(url):

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {

        "format": "best[height<=480]",

        "outtmpl": f"{temp_dir}/%(title)s.%(ext)s",

        "quiet": True,

        "merge_output_format": "mp4",

        "noplaylist": True,

        "cookiefile": None,

        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        }
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            title = info.get(
                "title",
                "Unknown"
            )

            uploader = info.get(
                "uploader",
                "Unknown"
            )

        for file in os.listdir(temp_dir):

            if file.endswith(".mp4"):

                return (
                    os.path.join(temp_dir, file),
                    title,
                    uploader,
                    temp_dir
                )

    except Exception as e:

        print(e)

    cleanup(temp_dir)

    return None, None, None, None

# =====================================================
# TIKTOK DOWNLOAD
# =====================================================

def tt_video(url):

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {

        "format": "best",

        "outtmpl": f"{temp_dir}/%(title)s.%(ext)s",

        "quiet": True,

        "merge_output_format": "mp4",

        "noplaylist": True
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            uploader = info.get(
                "uploader",
                "Unknown"
            )

        for file in os.listdir(temp_dir):

            if file.endswith(".mp4"):

                return (
                    os.path.join(temp_dir, file),
                    uploader,
                    temp_dir
                )

    except Exception as e:

        print(e)

    cleanup(temp_dir)

    return None, None, None

# =====================================================
# START
# =====================================================

@bot.message_handler(commands=["start"])
def start(message):

    text = """
🚀 <b>Welcome To AX Downloader Bot</b>

━━━━━━━━━━━━━━━━━━

🎵 Download YouTube Songs
🎬 Download YouTube Videos
📱 Download TikTok Videos

⚡ Fast • Clean • Professional

━━━━━━━━━━━━━━━━━━

📌 Commands:

/song youtube_link
/ytvideo youtube_link
/ttvideo tiktok_link

━━━━━━━━━━━━━━━━━━

👑 Owner : @Nobody_ax
"""

    bot.reply_to(
        message,
        text,
        reply_markup=keyboard()
    )

# =====================================================
# ALL COMMANDS
# =====================================================

@bot.message_handler(
    func=lambda m: m.text == "𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋"
)
def commands(message):

    text = """
⚡ <b>ALL COMMANDS</b>

━━━━━━━━━━━━━━━━━━

🎵 /song youtube_link
➜ Download YouTube MP3

━━━━━━━━━━━━━━━━━━

🎬 /ytvideo youtube_link
➜ Download YouTube Video

━━━━━━━━━━━━━━━━━━

📱 /ttvideo tiktok_link
➜ Download TikTok Video

━━━━━━━━━━━━━━━━━━

🏓 /ping
➜ Check Bot Status

━━━━━━━━━━━━━━━━━━

👑 Owner : @Nobody_ax
"""

    bot.reply_to(message, text)

# =====================================================
# PING
# =====================================================

@bot.message_handler(commands=["ping"])
def ping(message):

    bot.reply_to(
        message,
        "🏓 <b>Bot Online!</b>"
    )

# =====================================================
# SONG
# =====================================================

@bot.message_handler(commands=["song"])
def song(message):

    try:

        args = message.text.split(
            maxsplit=1
        )

        if len(args) < 2:

            bot.reply_to(
                message,
                "⚠️ Usage:\n<code>/song youtube_url</code>"
            )

            return

        url = args[1]

        msg = bot.reply_to(
            message,
            "🔄 Downloading audio..."
        )

        file_path, title, uploader, folder = yt_audio(url)

        if not file_path:

            bot.edit_message_text(
                "❌ Failed to download audio!",
                message.chat.id,
                msg.message_id
            )

            return

        bot.edit_message_text(
            "⬆️ Uploading audio...",
            message.chat.id,
            msg.message_id
        )

        caption = f"""
🎵 <b>{title[:70]}</b>

📺 Channel : {uploader[:40]}

━━━━━━━━━━━━━━━━━━

👑 Owner : @Nobody_ax
"""

        with open(file_path, "rb") as audio:

            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                title=title[:50],
                performer=uploader[:50]
            )

        cleanup(folder)

        bot.delete_message(
            message.chat.id,
            msg.message_id
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n<code>{str(e)[:150]}</code>"
        )

# =====================================================
# YT VIDEO
# =====================================================

@bot.message_handler(commands=["ytvideo"])
def ytvideo(message):

    try:

        args = message.text.split(
            maxsplit=1
        )

        if len(args) < 2:

            bot.reply_to(
                message,
                "⚠️ Usage:\n<code>/ytvideo youtube_url</code>"
            )

            return

        url = args[1]

        msg = bot.reply_to(
            message,
            "🔄 Downloading video..."
        )

        file_path, title, uploader, folder = yt_video(url)

        if not file_path:

            bot.edit_message_text(
                "❌ Failed to download video!",
                message.chat.id,
                msg.message_id
            )

            return

        bot.edit_message_text(
            "⬆️ Uploading video...",
            message.chat.id,
            msg.message_id
        )

        caption = f"""
🎬 <b>{title[:70]}</b>

📺 Channel : {uploader[:40]}

━━━━━━━━━━━━━━━━━━

👑 Owner : @Nobody_ax
"""

        with open(file_path, "rb") as video:

            bot.send_video(
                message.chat.id,
                video,
                caption=caption,
                supports_streaming=True
            )

        cleanup(folder)

        bot.delete_message(
            message.chat.id,
            msg.message_id
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n<code>{str(e)[:150]}</code>"
        )

# =====================================================
# TIKTOK
# =====================================================

@bot.message_handler(commands=["ttvideo"])
def ttvideo(message):

    try:

        args = message.text.split(
            maxsplit=1
        )

        if len(args) < 2:

            bot.reply_to(
                message,
                "⚠️ Usage:\n<code>/ttvideo tiktok_url</code>"
            )

            return

        url = args[1]

        msg = bot.reply_to(
            message,
            "🔄 Downloading TikTok video..."
        )

        file_path, uploader, folder = tt_video(url)

        if not file_path:

            bot.edit_message_text(
                "❌ Failed to download TikTok video!",
                message.chat.id,
                msg.message_id
            )

            return

        bot.edit_message_text(
            "⬆️ Uploading TikTok video...",
            message.chat.id,
            msg.message_id
        )

        caption = f"""
📱 <b>TikTok Video</b>

👤 Creator : @{uploader[:40]}

━━━━━━━━━━━━━━━━━━

👑 Owner : @Nobody_ax
"""

        with open(file_path, "rb") as video:

            bot.send_video(
                message.chat.id,
                video,
                caption=caption,
                supports_streaming=True
            )

        cleanup(folder)

        bot.delete_message(
            message.chat.id,
            msg.message_id
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n<code>{str(e)[:150]}</code>"
        )

# =====================================================
# UNKNOWN
# =====================================================

@bot.message_handler(func=lambda m: True)
def unknown(message):

    bot.reply_to(
        message,
        "⚠️ Unknown command!\nUse /start"
    )

# =====================================================
# RUN BOT
# =====================================================

print("🚀 AX Downloader Bot Running...")
print("👑 Owner : @Nobody_ax")

while True:

    try:

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            skip_pending=True
        )

    except Exception as e:

        print(e)

        time.sleep(5)
