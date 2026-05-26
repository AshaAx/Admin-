"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 AX Professional Downloader Bot
👑 Owner : @Nobody_ax
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import time
import tempfile
import telebot
import yt_dlp

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# =====================================================
# FIX YT-DLP BUG MESSAGE
# =====================================================

yt_dlp.utils.bug_reports_message = lambda: ""

# =====================================================
# BOT TOKEN
# =====================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =====================================================
# REMOVE WEBHOOK
# =====================================================

try:
    bot.remove_webhook()
    print("✅ Webhook Removed")
except Exception as e:
    print(e)

# =====================================================
# KEYBOARD
# =====================================================

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋"))
    return kb

# =====================================================
# SAFE DELETE
# =====================================================

def safe_delete(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass

# =====================================================
# DOWNLOAD AUDIO
# =====================================================

def download_audio(url):

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": f"{temp_dir}/%(title)s.%(ext)s",
        "ffmpeg_location": "/usr/bin",
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        title = info.get("title", "Unknown")
        uploader = info.get("uploader", "Unknown")

        for file in os.listdir(temp_dir):

            if file.endswith(".mp3"):

                return (
                    os.path.join(temp_dir, file),
                    title,
                    uploader
                )

    return None, None, None

# =====================================================
# DOWNLOAD YOUTUBE VIDEO
# =====================================================

def download_video(url):

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": "best[ext=mp4][height<=720]",
        "outtmpl": f"{temp_dir}/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        title = info.get("title", "Unknown")
        uploader = info.get("uploader", "Unknown")

        for file in os.listdir(temp_dir):

            if file.endswith(".mp4"):

                return (
                    os.path.join(temp_dir, file),
                    title,
                    uploader
                )

    return None, None, None

# =====================================================
# DOWNLOAD TIKTOK
# =====================================================

def download_tiktok(url):

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": "best",
        "outtmpl": f"{temp_dir}/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        uploader = info.get("uploader", "Unknown")

        for file in os.listdir(temp_dir):

            if file.endswith(".mp4"):

                return (
                    os.path.join(temp_dir, file),
                    uploader
                )

    return None, None

# =====================================================
# START
# =====================================================

@bot.message_handler(commands=["start"])
def start(message):

    text = """
🚀 <b>Welcome To AX Downloader Bot</b>

━━━━━━━━━━━━━━━━━━

🎵 YouTube → MP3
🎬 YouTube → Video
📱 TikTok → Video

━━━━━━━━━━━━━━━━━━

📌 Commands:

/song youtube_link
/ytvideo youtube_link
/ttvideo tiktok_link
/ping

━━━━━━━━━━━━━━━━━━

👑 Owner : @Nobody_ax
"""

    bot.reply_to(
        message,
        text,
        reply_markup=main_keyboard()
    )

# =====================================================
# COMMAND LIST
# =====================================================

@bot.message_handler(func=lambda m: m.text == "𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋")
def commands_list(message):

    text = """
📋 <b>ALL COMMANDS</b>

━━━━━━━━━━━━━━━━━━

🎵 /song youtube_url
🎬 /ytvideo youtube_url
📱 /ttvideo tiktok_url
🏓 /ping

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
        "🏓 <b>Bot Online & Working!</b>"
    )

# =====================================================
# SONG
# =====================================================

@bot.message_handler(commands=["song"])
def song(message):

    try:

        args = message.text.split(maxsplit=1)

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

        file_path, title, uploader = download_audio(url)

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
🎵 <b>{title}</b>

📺 Channel : {uploader}

━━━━━━━━━━━━━━━━━━

👑 Owner : @Nobody_ax
"""

        with open(file_path, "rb") as audio:

            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                title=title,
                performer=uploader
            )

        safe_delete(file_path)

        bot.delete_message(
            message.chat.id,
            msg.message_id
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n<code>{str(e)[:300]}</code>"
        )

# =====================================================
# YT VIDEO
# =====================================================

@bot.message_handler(commands=["ytvideo"])
def ytvideo(message):

    try:

        args = message.text.split(maxsplit=1)

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

        file_path, title, uploader = download_video(url)

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
🎬 <b>{title}</b>

📺 Channel : {uploader}

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

        safe_delete(file_path)

        bot.delete_message(
            message.chat.id,
            msg.message_id
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n<code>{str(e)[:300]}</code>"
        )

# =====================================================
# TIKTOK
# =====================================================

@bot.message_handler(commands=["ttvideo"])
def ttvideo(message):

    try:

        args = message.text.split(maxsplit=1)

        if len(args) < 2:

            bot.reply_to(
                message,
                "⚠️ Usage:\n<code>/ttvideo tiktok_url</code>"
            )
            return

        url = args[1]

        msg = bot.reply_to(
            message,
            "🔄 Downloading TikTok..."
        )

        file_path, uploader = download_tiktok(url)

        if not file_path:

            bot.edit_message_text(
                "❌ Failed to download TikTok video!",
                message.chat.id,
                msg.message_id
            )
            return

        bot.edit_message_text(
            "⬆️ Uploading TikTok...",
            message.chat.id,
            msg.message_id
        )

        caption = f"""
📱 <b>TikTok Video</b>

👤 Creator : @{uploader}

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

        safe_delete(file_path)

        bot.delete_message(
            message.chat.id,
            msg.message_id
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n<code>{str(e)[:300]}</code>"
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
# RUN
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
