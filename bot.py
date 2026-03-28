import os
import threading
import requests
import yt_dlp

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Flask (تشغيل 24/7)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    threading.Thread(target=run_web, daemon=True).start()

# فك الروابط المختصرة
def resolve_url(url):
    try:
        return requests.get(url, allow_redirects=True).url
    except:
        return url

# تنظيف الملفات
def cleanup():
    for f in os.listdir("."):
        if f.startswith("video."):
            try:
                os.remove(f)
            except:
                pass

# /start (اختياري)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass  # صامت

# استقبال الرابط
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        return

    url = resolve_url(url)

    cleanup()

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "video.%(ext)s",
        "merge_output_format": "mp4",
        "quiet": True,
        "noplaylist": True,
        "retries": 5,
        "fragment_retries": 5,
        "nocheckcertificate": True,
        "geo_bypass": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not filename.endswith(".mp4"):
            os.rename(filename, "video.mp4")
            filename = "video.mp4"

        # إرسال الفيديو مباشرة (صامت)
        try:
            with open(filename, "rb") as f:
                await update.message.reply_video(f)
        except:
            with open(filename, "rb") as f:
                await update.message.reply_document(f)

        os.remove(filename)

    except:
        pass  # صامت بالكامل

# تشغيل البوت
def main():
    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    keep_alive()
    bot.run_polling()

if __name__ == "__main__":
    main()
