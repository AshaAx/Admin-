"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 AX Professional Downloader Bot
👑 Owner : @Nobody_ax
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import re
import time
import shutil
import logging
import tempfile

import telebot
import yt_dlp

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# =====================================================
# LOGGING SETUP
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# =====================================================
# SUPPRESS YT-DLP BUG MESSAGE
# =====================================================

yt_dlp.utils.bug_reports_message = lambda: ""

# =====================================================
# BOT TOKEN
# =====================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN environment variable not set!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =====================================================
# CONSTANTS
# =====================================================

MAX_FILE_SIZE_MB   = 48          # Telegram bot API limit is 50MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)"
    r"([A-Za-z0-9_-]+)"
)

TIKTOK_REGEX = re.compile(
    r"(https?://)?"
    r"((www|vm|vt)\.)?"
    r"tiktok\.com/.+"
)

# =====================================================
# REMOVE WEBHOOK
# =====================================================

try:
    bot.remove_webhook()
    logger.info("✅ Webhook removed successfully")
except Exception as e:
    logger.warning(f"Webhook removal warning: {e}")

# =====================================================
# HELPERS
# =====================================================

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋"))
    return kb


def safe_cleanup(temp_dir: str):
    """Remove entire temp directory safely."""
    try:
        if temp_dir and os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        logger.warning(f"Temp cleanup failed: {e}")


def check_file_size(file_path: str) -> bool:
    """Return True if file is within Telegram upload limit."""
    try:
        return os.path.getsize(file_path) <= MAX_FILE_SIZE_BYTES
    except OSError:
        return False


def find_file(directory: str, extension: str) -> str | None:
    """Find first file with given extension inside a directory."""
    for fname in os.listdir(directory):
        if fname.endswith(extension):
            return os.path.join(directory, fname)
    return None


def safe_edit(chat_id: int, msg_id: int, text: str):
    """Edit a message silently (ignore if already deleted)."""
    try:
        bot.edit_message_text(text, chat_id, msg_id)
    except Exception:
        pass


def safe_delete_msg(chat_id: int, msg_id: int):
    """Delete a message silently."""
    try:
        bot.delete_message(chat_id, msg_id)
    except Exception:
        pass

# =====================================================
# DOWNLOAD: AUDIO (YouTube → MP3)
# =====================================================

def download_audio(url: str) -> tuple[str | None, str, str]:
    """
    Download best audio from YouTube and convert to MP3.
    Returns (file_path, title, uploader) or (None, "", "").
    """
    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
        "ffmpeg_location": "/usr/bin",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {"player_client": ["android"]}
        },
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title    = info.get("title", "Unknown")
            uploader = info.get("uploader", "Unknown")

        file_path = find_file(temp_dir, ".mp3")
        if file_path:
            return file_path, title, uploader

        logger.error("MP3 file not found after download.")
        safe_cleanup(temp_dir)
        return None, "", ""

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp audio error: {e}")
        safe_cleanup(temp_dir)
        raise
    except Exception as e:
        logger.error(f"Unexpected audio error: {e}")
        safe_cleanup(temp_dir)
        raise

# =====================================================
# DOWNLOAD: VIDEO (YouTube → MP4)
# =====================================================

def download_video(url: str) -> tuple[str | None, str, str]:
    """
    Download best video ≤720p from YouTube as MP4.
    Returns (file_path, title, uploader) or (None, "", "").
    """
    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": "best[ext=mp4][height<=720]/best[height<=720]/best",
        "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {"player_client": ["android"]}
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title    = info.get("title", "Unknown")
            uploader = info.get("uploader", "Unknown")

        file_path = find_file(temp_dir, ".mp4")
        if file_path:
            return file_path, title, uploader

        logger.error("MP4 file not found after download.")
        safe_cleanup(temp_dir)
        return None, "", ""

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp video error: {e}")
        safe_cleanup(temp_dir)
        raise
    except Exception as e:
        logger.error(f"Unexpected video error: {e}")
        safe_cleanup(temp_dir)
        raise

# =====================================================
# DOWNLOAD: TIKTOK
# =====================================================

def download_tiktok(url: str) -> tuple[str | None, str]:
    """
    Download TikTok video.
    Returns (file_path, uploader) or (None, "").
    """
    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "nocheckcertificate": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            uploader = info.get("uploader", "Unknown")

        file_path = find_file(temp_dir, ".mp4")
        if file_path:
            return file_path, uploader

        logger.error("TikTok MP4 not found after download.")
        safe_cleanup(temp_dir)
        return None, ""

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp TikTok error: {e}")
        safe_cleanup(temp_dir)
        raise
    except Exception as e:
        logger.error(f"Unexpected TikTok error: {e}")
        safe_cleanup(temp_dir)
        raise

# =====================================================
# /start
# =====================================================

@bot.message_handler(commands=["start"])
def cmd_start(message):
    text = (
        "🚀 <b>Welcome To AX Downloader Bot</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🎵 YouTube → MP3\n"
        "🎬 YouTube → Video\n"
        "📱 TikTok → Video\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📌 <b>Commands:</b>\n\n"
        "/song <code>youtube_link</code>\n"
        "/ytvideo <code>youtube_link</code>\n"
        "/ttvideo <code>tiktok_link</code>\n"
        "/ping\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "👑 Owner : @Nobody_ax"
    )
    bot.reply_to(message, text, reply_markup=main_keyboard())

# =====================================================
# COMMAND LIST BUTTON
# =====================================================

@bot.message_handler(func=lambda m: m.text == "𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋")
def cmd_commands_list(message):
    text = (
        "📋 <b>ALL COMMANDS</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🎵 /song <code>youtube_url</code>\n"
        "🎬 /ytvideo <code>youtube_url</code>\n"
        "📱 /ttvideo <code>tiktok_url</code>\n"
        "🏓 /ping\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "👑 Owner : @Nobody_ax"
    )
    bot.reply_to(message, text)

# =====================================================
# /ping
# =====================================================

@bot.message_handler(commands=["ping"])
def cmd_ping(message):
    start = time.monotonic()
    sent  = bot.reply_to(message, "🏓 Pinging...")
    ms    = round((time.monotonic() - start) * 1000)
    bot.edit_message_text(
        f"🏓 <b>Pong!</b>  <code>{ms}ms</code>",
        message.chat.id,
        sent.message_id
    )

# =====================================================
# /song — YouTube → MP3
# =====================================================

@bot.message_handler(commands=["song"])
def cmd_song(message):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage:\n<code>/song youtube_url</code>")
        return

    url = args[1].strip()

    if not YOUTUBE_REGEX.search(url):
        bot.reply_to(message, "❌ Invalid YouTube URL.")
        return

    msg = bot.reply_to(message, "⏳ Downloading audio...")
    temp_dir = None

    try:
        file_path, title, uploader = download_audio(url)
        temp_dir = os.path.dirname(file_path) if file_path else None

        if not file_path:
            safe_edit(message.chat.id, msg.message_id, "❌ Download failed. Try again.")
            return

        if not check_file_size(file_path):
            safe_edit(
                message.chat.id, msg.message_id,
                f"❌ File too large (>{MAX_FILE_SIZE_MB}MB). Telegram limit exceeded."
            )
            return

        safe_edit(message.chat.id, msg.message_id, "⬆️ Uploading audio...")

        caption = (
            f"🎵 <b>{title}</b>\n\n"
            f"📺 Channel : {uploader}\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👑 Owner : @Nobody_ax"
        )

        with open(file_path, "rb") as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                title=title,
                performer=uploader,
                reply_to_message_id=message.message_id
            )

        safe_delete_msg(message.chat.id, msg.message_id)

    except yt_dlp.utils.DownloadError:
        safe_edit(message.chat.id, msg.message_id,
                  "❌ Could not download. The video may be age-restricted, private, or unavailable.")
    except Exception as e:
        logger.exception("song handler error")
        safe_edit(message.chat.id, msg.message_id,
                  f"❌ Error:\n<code>{str(e)[:300]}</code>")
    finally:
        if temp_dir:
            safe_cleanup(temp_dir)

# =====================================================
# /ytvideo — YouTube → MP4
# =====================================================

@bot.message_handler(commands=["ytvideo"])
def cmd_ytvideo(message):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage:\n<code>/ytvideo youtube_url</code>")
        return

    url = args[1].strip()

    if not YOUTUBE_REGEX.search(url):
        bot.reply_to(message, "❌ Invalid YouTube URL.")
        return

    msg = bot.reply_to(message, "⏳ Downloading video...")
    temp_dir = None

    try:
        file_path, title, uploader = download_video(url)
        temp_dir = os.path.dirname(file_path) if file_path else None

        if not file_path:
            safe_edit(message.chat.id, msg.message_id, "❌ Download failed. Try again.")
            return

        if not check_file_size(file_path):
            safe_edit(
                message.chat.id, msg.message_id,
                f"❌ File too large (>{MAX_FILE_SIZE_MB}MB). Try a shorter video."
            )
            return

        safe_edit(message.chat.id, msg.message_id, "⬆️ Uploading video...")

        caption = (
            f"🎬 <b>{title}</b>\n\n"
            f"📺 Channel : {uploader}\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👑 Owner : @Nobody_ax"
        )

        with open(file_path, "rb") as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=caption,
                supports_streaming=True,
                reply_to_message_id=message.message_id
            )

        safe_delete_msg(message.chat.id, msg.message_id)

    except yt_dlp.utils.DownloadError:
        safe_edit(message.chat.id, msg.message_id,
                  "❌ Could not download. The video may be private, age-restricted, or unavailable.")
    except Exception as e:
        logger.exception("ytvideo handler error")
        safe_edit(message.chat.id, msg.message_id,
                  f"❌ Error:\n<code>{str(e)[:300]}</code>")
    finally:
        if temp_dir:
            safe_cleanup(temp_dir)

# =====================================================
# /ttvideo — TikTok → MP4
# =====================================================

@bot.message_handler(commands=["ttvideo"])
def cmd_ttvideo(message):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage:\n<code>/ttvideo tiktok_url</code>")
        return

    url = args[1].strip()

    if not TIKTOK_REGEX.search(url):
        bot.reply_to(message, "❌ Invalid TikTok URL.")
        return

    msg = bot.reply_to(message, "⏳ Downloading TikTok...")
    temp_dir = None

    try:
        file_path, uploader = download_tiktok(url)
        temp_dir = os.path.dirname(file_path) if file_path else None

        if not file_path:
            safe_edit(message.chat.id, msg.message_id, "❌ Download failed. Try again.")
            return

        if not check_file_size(file_path):
            safe_edit(
                message.chat.id, msg.message_id,
                f"❌ File too large (>{MAX_FILE_SIZE_MB}MB). Telegram limit exceeded."
            )
            return

        safe_edit(message.chat.id, msg.message_id, "⬆️ Uploading TikTok...")

        caption = (
            "📱 <b>TikTok Video</b>\n\n"
            f"👤 Creator : @{uploader}\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👑 Owner : @Nobody_ax"
        )

        with open(file_path, "rb") as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=caption,
                supports_streaming=True,
                reply_to_message_id=message.message_id
            )

        safe_delete_msg(message.chat.id, msg.message_id)

    except yt_dlp.utils.DownloadError:
        safe_edit(message.chat.id, msg.message_id,
                  "❌ Could not download. The video may be private or unavailable.")
    except Exception as e:
        logger.exception("ttvideo handler error")
        safe_edit(message.chat.id, msg.message_id,
                  f"❌ Error:\n<code>{str(e)[:300]}</code>")
    finally:
        if temp_dir:
            safe_cleanup(temp_dir)

# =====================================================
# UNKNOWN MESSAGE
# =====================================================

@bot.message_handler(func=lambda m: True)
def cmd_unknown(message):
    bot.reply_to(
        message,
        "⚠️ Unknown command!\nType /start to see available commands."
    )

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    logger.info("🚀 AX Downloader Bot starting...")
    logger.info("👑 Owner : @Nobody_ax")

    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                skip_pending=True
            )
        except Exception as e:
            logger.error(f"Polling error: {e}  — restarting in 5s")
            time.sleep(5)
