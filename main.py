"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 AX Professional Downloader Bot
👑 Owner : @Nobody_ax
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Features:
• YouTube → MP3
• YouTube → Video
• TikTok → Video
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import time
import tempfile
import telebot
import yt_dlp

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# =====================================================
# BOT TOKEN
# =====================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =====================================================
# REMOVE WEBHOOK
# =====================================================

try:
    bot.remove_webhook()
    time.sleep(1)
    print("✅ Old webhook removed")
except:
    pass

# =====================================================
# EMOJIS
# =====================================================

EMOJI = {
    "music": "🎵",
    "video": "🎬",
    "tt": "📱",
    "done": "✅",
    "error": "❌",
    "loading": "🔄",
    "owner": "👑",
    "warn": "⚠️",
    "rocket": "🚀",
    "download": "⬇️"
}

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

def safe_delete(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except:
        pass

# =====================================================
# DOWNLOAD YOUTUBE AUDIO
# =====================================================

def download_audio(url):

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{temp_dir}/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        title = info.get("title", "Unknown")
        channel = info.get("uploader", "Unknown")

        for file in os.listdir(temp_dir):
            if file.endswith(".mp3"):
                return (
                    os.path.join(temp_dir, file),
                    title,
                    channel
                )

    return None, None, None

# =====================================================
# DOWNLOAD YOUTUBE VIDEO
# =====================================================

def download_video(url):

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": "best[height<=480]",
        "outtmpl": f"{temp_dir}/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        title = info.get("title", "Unknown")
        channel = info.get("uploader", "Unknown")

        for file in os.listdir(temp_dir):
            if file.endswith(".mp4"):
                return (
                    os.path.join(temp_dir, file),
                    title,
                    channel
                )

    return None, None, None

# =====================================================
# DOWNLOAD TIKTOK VIDEO
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

        author = info.get("uploader", "Unknown")

        for file in os.listdir(temp_dir):
            if file.endswith(".mp4"):
                return (
                    os.path.join(temp_dir, file),
                    author
                )

    return None, None

# =====================================================
# START COMMAND
# =====================================================

@bot.message_handler(commands=["start"])
def start(message):

    text = f"""
🚀 <b>Welcome To AX Downloader Bot</b>

━━━━━━━━━━━━━━━━━━

🎵 Download YouTube Songs
🎬 Download YouTube Videos
📱 Download TikTok Videos

⚡ Fast • Simple • Professional

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
        reply_markup=main_keyboard()
    )

# =====================================================
# COMMAND LIST BUTTON
# =====================================================

@bot.message_handler(func=lambda m: m.text == "𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋")
def all_commands(message):

    text = f"""
⚡ <b>ALL COMMANDS</b>

━━━━━━━━━━━━━━━━━━

🎵 <b>/song</b> youtube_link
➜ Download YouTube as MP3

━━━━━━━━━━━━━━━━━━

🎬 <b>/ytvideo</b> youtube_link
➜ Download YouTube video

━━━━━━━━━━━━━━━━━━

📱 <b>/ttvideo</b> tiktok_link
➜ Download TikTok video

━━━━━━━━━━━━━━━━━━

🏓 <b>/ping</b>
➜ Check bot online status

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
# SONG COMMAND
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

        if "youtube.com" not in url and "youtu.be" not in url:
            bot.reply_to(
                message,
                "❌ Invalid YouTube URL!"
            )
            return

        msg = bot.reply_to(
            message,
            "🔄 Downloading audio..."
        )

        file_path, title, channel = download_audio(url)

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
🎵 <b>{title[:80]}</b>

📺 Channel : {channel[:50]}

━━━━━━━━━━━━━━━━━━

👑 Owner : @Nobody_ax
"""

        with open(file_path, "rb") as audio:

            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                title=title[:50],
                performer=channel[:50]
            )

        safe_delete(file_path)

        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n<code>{str(e)[:150]}</code>"
        )

# =====================================================
# YOUTUBE VIDEO COMMAND
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

        if "youtube.com" not in url and "youtu.be" not in url:
            bot.reply_to(
                message,
                "❌ Invalid YouTube URL!"
            )
            return

        msg = bot.reply_to(
            message,
            "🔄 Downloading video..."
        )

        file_path, title, channel = download_video(url)

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
🎬 <b>{title[:80]}</b>

📺 Channel : {channel[:50]}

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

        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n<code>{str(e)[:150]}</code>"
        )

# =====================================================
# TIKTOK COMMAND
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

        if "tiktok.com" not in url:
            bot.reply_to(
                message,
                "❌ Invalid TikTok URL!"
            )
            return

        msg = bot.reply_to(
            message,
            "🔄 Downloading TikTok video..."
        )

        file_path, author = download_tiktok(url)

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

👤 Creator : @{author[:50]}

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

        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n<code>{str(e)[:150]}</code>"
        )

# =====================================================
# UNKNOWN MESSAGE
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

print("🚀 AX Downloader Bot Started...")
print("👑 Owner : @Nobody_ax")

while True:

    try:

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:

        print(f"Error: {e}")

        time.sleep(5)
