import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Flask
app = Flask('')

@app.route('/')
def home():
    return "Bot is running"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    threading.Thread(target=run).start()

# تخزين الرابط مؤقت
user_links = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 أرسل رابط الفيديو")

# لما يرسل رابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.message.from_user.id

    user_links[user_id] = url

    keyboard = [
        [InlineKeyboardButton("⚡ سريع", callback_data="fast")],
        [InlineKeyboardButton("🔥 أفضل جودة", callback_data="best")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("اختر الجودة:", reply_markup=reply_markup)

# لما يضغط زر
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_links.get(user_id)

    if not url:
        await query.edit_message_text("❌ ما فيه رابط")
        return

    if query.data == "fast":
        format_type = "best[ext=mp4]"
    else:
        format_type = "bestvideo+bestaudio"

    await query.edit_message_text("⏳ جاري التحميل...")

    ydl_opts = {
        'format': format_type,
        'outtmpl': 'video.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'retries': 3
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not filename.endswith(".mp4"):
            os.rename(filename, "video.mp4")
            filename = "video.mp4"

        await query.message.reply_video(open(filename, 'rb'))

        os.remove(filename)

    except:
        await query.message.reply_text("❌ فشل التحميل")

# تشغيل
def main():
    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    bot.add_handler(CallbackQueryHandler(button))

    keep_alive()
    bot.run_polling()

if __name__ == "__main__":
    main()
