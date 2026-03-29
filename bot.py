import os
import threading
import requests
import yt_dlp
import hashlib
import asyncio

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = 799529225

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    threading.Thread(target=run_web, daemon=True).start()

def resolve_url(url):
    try:
        return requests.get(url, allow_redirects=True, timeout=5).url
    except:
        return url

# 🧠 كاش
def cache_name(url):
    return hashlib.md5(url.encode()).hexdigest() + ".mp4"

# 🧹 تنظيف
def cleanup():
    for f in os.listdir("."):
        if f.endswith(".mp4") or f.startswith("video"):
            try:
                os.remove(f)
            except:
                pass

# ⚡ تحميل
async def download(url, filename):
    loop = asyncio.get_event_loop()

    def run():
        ydl_opts = {
            "format": "bv*+ba/b",  # أعلى جودة بدون تحديد
            "outtmpl": filename,
            "merge_output_format": "mp4",
            "quiet": True,
            "noplaylist": True,
            "concurrent_fragment_downloads": 8,
            "retries": 3,
            "fragment_retries": 3,
            "nocheckcertificate": True,
            "geo_bypass": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    return await loop.run_in_executor(None, run)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("🔥 ارسل الرابط وأنا أحمله لك بدون ضغط وبأعلى جودة")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    url = update.message.text.strip()
    if not url.startswith("http"):
        return

    await update.message.reply_text("⏳ جاري التحميل...")

    url = resolve_url(url)
    file = cache_name(url)

    # ⚡ كاش
    if os.path.exists(file):
        with open(file, "rb") as f:
            await update.message.reply_document(f)
        return

    temp_file = "video.mp4"

    try:
        await download(url, temp_file)

        os.rename(temp_file, file)

        # 🚀 إرسال بدون ضغط
        with open(file, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename="video.mp4"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

def main():
    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    keep_alive()
    bot.run_polling()

if __name__ == "__main__":
    main()
