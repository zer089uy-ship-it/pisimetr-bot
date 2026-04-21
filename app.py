from flask import Flask
import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = "8730625454:AAFBDzXTVcC-aymhrG7Z5XZZ7O4Gm5JJspo"

COMMANDS = {
    "start": "Запустить бота",
    "pisi": "Увеличить Писю",
    "stats": "Моя статистика",
    "top": "Топ чата",
}

from database import db
from messages import *

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"🔥 ПОЛУЧЕНА КОМАНДА /start")
    user = update.effective_user
    await update.message.reply_text(f"✅ Бот работает! Привет, {user.first_name}!")

async def pisi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"🔥 ПОЛУЧЕНА КОМАНДА /pisi")
    await update.message.reply_text("🍆 Команда /pisi получена!")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"🔥 ПОЛУЧЕНА КОМАНДА /stats")
    await update.message.reply_text("📊 Статистика скоро будет")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"🔥 ПОЛУЧЕНА КОМАНДА /top")
    await update.message.reply_text("🏆 Топ скоро будет")

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pisi", pisi))
telegram_app.add_handler(CommandHandler("stats", stats))
telegram_app.add_handler(CommandHandler("top", top))

@app.route('/')
def home():
    return "🍆 ПиСиметр бот работает! 🍆"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    # Запускаем polling в фоновом потоке
    import threading
    def run_polling():
        asyncio.run(telegram_app.run_polling())
    
    threading.Thread(target=run_polling, daemon=True).start()
    
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Flask сервер на порту {port}")
    app.run(host='0.0.0.0', port=port)
