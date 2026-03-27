from flask import Flask
import threading
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is running"

def run():
    app_flask.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

async def start(update, context):
    await update.message.reply_text("هلا فيك 👋")

async def help_command(update, context):
    await update.message.reply_text("ارسل رابط وانا احمله لك 🔥")

async def handle_message(update, context):
    text = update.message.text
    await update.message.reply_text(f"وصلني الرابط: {text}")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    keep_alive()
    application.run_polling()

if __name__ == "__main__":
    main()
