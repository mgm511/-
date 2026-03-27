import os
import threading
import requests
import yt_dlp

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Flask for Render
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

def keep_alive():
    threading.Thread(target=run_web, daemon=True).start()

# تخزين الروابط مؤقتًا
user_links = {}

def resolve_url(url: str) -> str:
    try:
        r = requests.get(url, allow_redirects=True, timeout=15)
        return r.url or url
    except Exception:
        return url

def cleanup_files():
    for name in os.listdir("."):
        if name.startswith("video."):
            try:
                os.remove(name)
            except Exception:
                pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 هلا فيك\n"
        "أرسل رابط فيديو من تيك توك / انستا / يوتيوب / تويتر\n"
        "وبأحمله لك.\n\n"
        "بعد إرسال الرابط اختر:\n"
        "⚡ سريع\n"
        "🔥 أفضل جودة"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أرسل الرابط فقط.\n"
        "إذا الرابط مختصر أنا بحاول أفكه تلقائيًا.\n"
        "بعض المواقع قد تفرض قيودًا أو تمنع التحميل أحيانًا."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    user_id = update.message.from_user.id

    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ أرسل رابط صحيح يبدأ بـ http أو https")
        return

    user_links[user_id] = url

    keyboard = [
        [InlineKeyboardButton("⚡ سريع", callback_data="fast")],
        [InlineKeyboardButton("🔥 أفضل جودة", callback_data="best")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("اختر طريقة التحميل:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_links.get(user_id)

    if not url:
        await query.edit_message_text("❌ ما لقيت الرابط. أرسله مرة ثانية.")
        return

    url = resolve_url(url)

    if query.data == "fast":
        format_type = "best[ext=mp4]/best"
    else:
        format_type = "bestvideo+bestaudio/best"

    await query.edit_message_text("⏳ جاري التحميل...")

    cleanup_files()

    ydl_opts = {
        "format": format_type,
        "outtmpl": "video.%(ext)s",
        "merge_output_format": "mp4",
        "quiet": True,
        "noplaylist": True,
        "retries": 5,
        "fragment_retries": 5,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "geo_bypass": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            )
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                await query.message.reply_text("❌ ما قدرت أجيب بيانات المقطع")
                return

            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            # أحيانًا يدمج إلى mp4 باسم مختلف
            for name in os.listdir("."):
                if name.startswith("video.") and os.path.isfile(name):
                    filename = name
                    break

        if not os.path.exists(filename):
            await query.message.reply_text("❌ تم التحميل لكن ما لقيت الملف النهائي")
            return

        if not filename.endswith(".mp4"):
            new_name = "video.mp4"
            os.rename(filename, new_name)
            filename = new_name

        await query.message.reply_text("📤 جاري الإرسال...")

        with open(filename, "rb") as f:
            await query.message.reply_video(video=f)

        try:
            os.remove(filename)
        except Exception:
            pass

    except Exception as e:
        await query.message.reply_text(f"❌ فشل التحميل:\n{str(e)[:200]}")

def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", help_command))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    bot.add_handler(CallbackQueryHandler(button))

    keep_alive()
    bot.run_polling()

if __name__ == "__main__":
    main()
