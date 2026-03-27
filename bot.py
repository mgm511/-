import os
import threading
import requests
import yt_dlp

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Flask (لتشغيله 24 ساعة)
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

# حذف الملفات القديمة
def cleanup():
    for f in os.listdir("."):
        if f.startswith("video."):
            try:
                os.remove(f)
            except:
                pass

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 أرسل رابط الفيديو وبحمّله لك بأفضل جودة")

# استقبال الرابط
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("❌ أرسل رابط صحيح")
        return

    url = resolve_url(url)

    await update.message.reply_text("⏳ جاري التحميل...")

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

        # تحويل إلى mp4 إذا مو mp4
        if not filename.endswith(".mp4"):
            os.rename(filename, "video.mp4")
            filename = "video.mp4"

        await update.message.reply_text("📤 جاري الإرسال...")

        with open(filename, "rb") as f:
            await update.message.reply_video(f)

        os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"❌ فشل التحميل:\n{str(e)[:200]}")

# تشغيل
def main():
    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    keep_alive()
    bot.run_polling()

if __name__ == "__main__":
    main()
