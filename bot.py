import os
import threading
import requests
import yt_dlp
import hashlib
import asyncio

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = 799529225

# 🌐 Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    threading.Thread(target=run_web, daemon=True).start()

# 🔗 حل الرابط
def resolve_url(url):
    try:
        return requests.get(url, allow_redirects=True, timeout=10).url
    except:
        return url

# 🧠 اسم الملف
def cache_name(url):
    return hashlib.md5(url.encode()).hexdigest() + ".mp4"

# ⚡ تحميل
async def download(url, filename):
    loop = asyncio.get_running_loop()

    def run():
        ydl_opts = {
            "format": "bv*+ba/b",
            "outtmpl": filename,
            "merge_output_format": "mp4",
            "quiet": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    await loop.run_in_executor(None, run)

# 🚀 start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("🔥 ارسل الرابط")

# 📥 استقبال
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    if not url.startswith("http"):
        return

    await update.message.reply_text("⏳ جاري التحميل...")

    url = resolve_url(url)
    file = cache_name(url)
    temp = f"temp_{file}"

    try:
        await download(url, temp)

        if os.path.exists(temp):
            os.rename(temp, file)

        with open(file, "rb") as f:
            await update.message.reply_document(f, filename="video.mp4")

    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

def main():
    if not TOKEN:
        raise ValueError("❌ حط التوكن")

    keep_alive()

    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("✅ شغال")
    bot.run_polling()

if __name__ == "__main__":
    main()