"""
Professional Telegram Downloader Bot
Author: @Nobody_ax
Description: A utility bot for downloading YouTube audio/video and TikTok videos
"""

import os
import re
import tempfile
import time
from typing import Optional, Tuple

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import yt_dlp
import requests

# ============= CONFIGURATION =============
# Get bot token from environment variable (for Railway/Production)
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Stylish emojis for professional look
EMOJIS = {
    'music': '🎵',
    'video': '🎬',
    'tiktok': '📱',
    'download': '⬇️',
    'success': '✅',
    'error': '❌',
    'processing': '🔄',
    'warning': '⚠️',
    'info': 'ℹ️',
    'owner': '👑',
    'command': '⚡',
    'youtube': '📺',
}

# yt-dlp configuration for optimal performance
YDL_OPTS_AUDIO = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}

YDL_OPTS_VIDEO = {
    'format': 'best[height<=720]',  # Limit to 720p for faster downloads
    'quiet': True,
    'no_warnings': True,
    'merge_output_format': 'mp4',
}

# ============= HELPER FUNCTIONS =============

def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
    }
    return "".join(html_escape_table.get(c, c) for c in text)

def download_youtube_audio(url: str) -> Optional[Tuple[str, str, str]]:
    """
    Download YouTube video as MP3 audio
    Returns: (file_path, song_name, channel_name) or None
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            temp_path = tmp_file.name
        
        ydl_opts = YDL_OPTS_AUDIO.copy()
        ydl_opts['outtmpl'] = temp_path.replace('.mp3', '.%(ext)s')
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            song_name = info.get('title', 'Unknown Song')
            channel_name = info.get('channel', 'Unknown Channel')
            
            # Find the actual mp3 file
            actual_file = temp_path.replace('.mp3', '.mp3')
            if os.path.exists(actual_file):
                return actual_file, song_name, channel_name
            return None, None, None
            
    except Exception as e:
        print(f"Audio download error: {e}")
        return None, None, None

def download_youtube_video(url: str) -> Optional[Tuple[str, str, str]]:
    """
    Download YouTube video as MP4
    Returns: (file_path, video_title, channel_name) or None
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            temp_path = tmp_file.name
        
        ydl_opts = YDL_OPTS_VIDEO.copy()
        ydl_opts['outtmpl'] = temp_path.replace('.mp4', '.%(ext)s')
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'Unknown Video')
            channel_name = info.get('channel', 'Unknown Channel')
            
            actual_file = temp_path.replace('.mp4', '.mp4')
            if os.path.exists(actual_file):
                return actual_file, video_title, channel_name
            return None, None, None
            
    except Exception as e:
        print(f"Video download error: {e}")
        return None, None, None

def download_tiktok_video(url: str) -> Optional[Tuple[str, str]]:
    """
    Download TikTok video without watermark
    Returns: (file_path, author) or None
    """
    try:
        # TikTok downloader using yt-dlp (supports watermark removal)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            temp_path = tmp_file.name
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': temp_path.replace('.mp4', '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            author = info.get('uploader', 'Unknown User')
            
            actual_file = temp_path.replace('.mp4', '.mp4')
            if os.path.exists(actual_file):
                return actual_file, author
            return None, None
            
    except Exception as e:
        print(f"TikTok download error: {e}")
        return None, None

def send_processing_message(message, file_type: str):
    """Send a processing message while downloading"""
    emoji = EMOJIS.get(file_type, EMOJIS['processing'])
    processing_msg = bot.reply_to(
        message,
        f"{emoji} Processing your {file_type}...\n⏳ Please wait, this may take a few moments."
    )
    return processing_msg

# ============= COMMAND HANDLERS =============

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command - Send welcome message with keyboard"""
    # Create reply keyboard
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    commands_button = KeyboardButton("𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋")
    markup.add(commands_button)
    
    welcome_text = f"""
{EMOJIS['youtube']}{EMOJIS['music']}{EMOJIS['video']} <b>PROFESSIONAL MEDIA DOWNLOADER</b> {EMOJIS['tiktok']}{EMOJIS['download']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ <b>Bot Name:</b> Ultimate Media Downloader
🎯 <b>Version:</b> 2.0 Professional

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>🌟 Features:</b>
{EMOJIS['music']} YouTube → MP3 Audio Download
{EMOJIS['video']} YouTube → MP4 Video Download  
{EMOJIS['tiktok']} TikTok Video (No Watermark)
{EMOJIS['success']} High Quality Output
{EMOJIS['download']} Fast Processing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>💡 How to Use:</b>
Simply send any command followed by the URL:
<code>/song youtube_url</code>
<code>/ytvideo youtube_url</code>
<code>/ttvideo tiktok_url</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{EMOJIS['owner']} <b>Owner:</b> @Nobody_ax
{EMOJIS['info']} <b>Support:</b> Click the button below for commands

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    bot.reply_to(message, welcome_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋")
def send_commands_list(message):
    """Send all available commands in stylish format"""
    commands_text = f"""
{EMOJIS['command']} <b>AVAILABLE COMMANDS</b> {EMOJIS['command']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{EMOJIS['music']} <b>/song</b> <code>[youtube_url]</code>
➥ Download YouTube video as high-quality MP3
📝 Example: <code>/song https://youtube.com/watch?v=...</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{EMOJIS['video']} <b>/ytvideo</b> <code>[youtube_url]</code>
➥ Download YouTube video as MP4 (720p)
📝 Example: <code>/ytvideo https://youtube.com/watch?v=...</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{EMOJIS['tiktok']} <b>/ttvideo</b> <code>[tiktok_url]</code>
➥ Download TikTok video (No watermark)
📝 Example: <code>/ttvideo https://tiktok.com/@user/video/...</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>⚠️ Notes:</b>
• Maximum file size: 50MB (Telegram limit)
• Processing time depends on file size
• Some TikTok videos may still have watermarks

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{EMOJIS['owner']} <b>Developer:</b> @Nobody_ax
"""
    bot.reply_to(message, commands_text, parse_mode='HTML')

@bot.message_handler(commands=['song'])
def handle_song(message):
    """Handle /song command - Download YouTube audio"""
    try:
        # Extract URL from command
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            bot.reply_to(
                message,
                f"{EMOJIS['warning']} <b>Usage:</b> <code>/song youtube_url</code>\n\nExample: <code>/song https://youtube.com/watch?v=dQw4w9WgXcQ</code>",
                parse_mode='HTML'
            )
            return
        
        url = command_parts[1].strip()
        
        # Validate YouTube URL
        if not ('youtube.com' in url or 'youtu.be' in url):
            bot.reply_to(
                message,
                f"{EMOJIS['error']} <b>Invalid URL!</b>\nPlease provide a valid YouTube URL.",
                parse_mode='HTML'
            )
            return
        
        # Send processing message
        processing_msg = send_processing_message(message, 'audio')
        
        # Download audio
        result = download_youtube_audio(url)
        if not result or not result[0]:
            bot.edit_message_text(
                f"{EMOJIS['error']} <b>Download Failed!</b>\nUnable to process the audio. Please check the URL and try again.",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode='HTML'
            )
            return
        
        file_path, song_name, channel_name = result
        
        # Prepare caption (escape HTML special characters)
        caption = f"""
{EMOJIS['music']} <b>{escape_html(song_name[:100])}</b>

{EMOJIS['youtube']} <b>Channel:</b> {escape_html(channel_name)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{EMOJIS['owner']} <b>Owner:</b> @Nobody_ax
{EMOJIS['download']} <b>Downloaded with:</b> @UltimateMediaBot
"""
        
        # Delete processing message
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # Send audio file
        with open(file_path, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                parse_mode='HTML',
                title=song_name[:50],
                performer=channel_name[:50]
            )
        
        # Clean up temp file
        os.unlink(file_path)
        
    except Exception as e:
        bot.reply_to(
            message,
            f"{EMOJIS['error']} <b>Unexpected Error:</b>\n<code>{escape_html(str(e)[:100])}</code>\n\nPlease try again later.",
            parse_mode='HTML'
        )
        print(f"Song command error: {e}")

@bot.message_handler(commands=['ytvideo'])
def handle_ytvideo(message):
    """Handle /ytvideo command - Download YouTube video"""
    try:
        # Extract URL from command
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            bot.reply_to(
                message,
                f"{EMOJIS['warning']} <b>Usage:</b> <code>/ytvideo youtube_url</code>\n\nExample: <code>/ytvideo https://youtube.com/watch?v=dQw4w9WgXcQ</code>",
                parse_mode='HTML'
            )
            return
        
        url = command_parts[1].strip()
        
        # Validate YouTube URL
        if not ('youtube.com' in url or 'youtu.be' in url):
            bot.reply_to(
                message,
                f"{EMOJIS['error']} <b>Invalid URL!</b>\nPlease provide a valid YouTube URL.",
                parse_mode='HTML'
            )
            return
        
        # Send processing message
        processing_msg = send_processing_message(message, 'video')
        
        # Download video
        result = download_youtube_video(url)
        if not result or not result[0]:
            bot.edit_message_text(
                f"{EMOJIS['error']} <b>Download Failed!</b>\nUnable to process the video. Please check the URL and try again.",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode='HTML'
            )
            return
        
        file_path, video_title, channel_name = result
        
        # Prepare caption (escape HTML special characters)
        caption = f"""
{EMOJIS['video']} <b>{escape_html(video_title[:100])}</b>

{EMOJIS['youtube']} <b>Channel:</b> {escape_html(channel_name)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{EMOJIS['owner']} <b>Owner:</b> @Nobody_ax
{EMOJIS['download']} <b>Downloaded with:</b> @UltimateMediaBot
"""
        
        # Delete processing message
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # Send video file
        with open(file_path, 'rb') as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=caption,
                parse_mode='HTML',
                supports_streaming=True
            )
        
        # Clean up temp file
        os.unlink(file_path)
        
    except Exception as e:
        bot.reply_to(
            message,
            f"{EMOJIS['error']} <b>Unexpected Error:</b>\n<code>{escape_html(str(e)[:100])}</code>\n\nPlease try again later.",
            parse_mode='HTML'
        )
        print(f"Video command error: {e}")

@bot.message_handler(commands=['ttvideo'])
def handle_ttvideo(message):
    """Handle /ttvideo command - Download TikTok video"""
    try:
        # Extract URL from command
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            bot.reply_to(
                message,
                f"{EMOJIS['warning']} <b>Usage:</b> <code>/ttvideo tiktok_url</code>\n\nExample: <code>/ttvideo https://tiktok.com/@user/video/123456789</code>",
                parse_mode='HTML'
            )
            return
        
        url = command_parts[1].strip()
        
        # Validate TikTok URL
        if not ('tiktok.com' in url or 'vt.tiktok.com' in url):
            bot.reply_to(
                message,
                f"{EMOJIS['error']} <b>Invalid URL!</b>\nPlease provide a valid TikTok URL.",
                parse_mode='HTML'
            )
            return
        
        # Send processing message
        processing_msg = send_processing_message(message, 'TikTok video')
        
        # Download video
        result = download_tiktok_video(url)
        if not result or not result[0]:
            bot.edit_message_text(
                f"{EMOJIS['error']} <b>Download Failed!</b>\nUnable to process the TikTok video. The video might be private or unavailable.\n\n{EMOJIS['info']} <b>Note:</b> Some TikTok videos may require login credentials.",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode='HTML'
            )
            return
        
        file_path, author = result
        
        # Prepare caption (escape HTML special characters)
        caption = f"""
{EMOJIS['tiktok']} <b>TikTok Video</b>

{EMOJIS['info']} <b>Author:</b> @{escape_html(author)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{EMOJIS['owner']} <b>Owner:</b> @Nobody_ax
{EMOJIS['download']} <b>Downloaded with:</b> @UltimateMediaBot
"""
        
        # Delete processing message
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # Send video file
        with open(file_path, 'rb') as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=caption,
                parse_mode='HTML',
                supports_streaming=True
            )
        
        # Clean up temp file
        os.unlink(file_path)
        
    except Exception as e:
        bot.reply_to(
            message,
            f"{EMOJIS['error']} <b>Unexpected Error:</b>\n<code>{escape_html(str(e)[:100])}</code>\n\nPlease try again later.",
            parse_mode='HTML'
        )
        print(f"TikTok command error: {e}")

# ============= ERROR HANDLER =============

@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    """Handle unknown messages"""
    bot.reply_to(
        message,
        f"{EMOJIS['warning']} <b>Unknown Command!</b>\n\nUse /start to see available commands or tap the <b>𝘼𝙇𝙇 𝘾𝙤𝙢𝙢𝙖𝙣𝙙'𝙨 - 📋</b> button.\n\n{EMOJIS['owner']} <b>Owner:</b> @Nobody_ax",
        parse_mode='HTML'
    )

# ============= MAIN =============

if __name__ == '__main__':
    print("🚀 Bot is starting...")
    print(f"👑 Owner: @Nobody_ax")
    print("📺 YouTube Downloader Ready")
    print("📱 TikTok Downloader Ready")
    print("✅ Bot is running...")
    
    # Start polling with error handling
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
