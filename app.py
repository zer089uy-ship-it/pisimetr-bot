from flask import Flask, request, jsonify
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
    logger.info(f"🔥 ПОЛУЧЕНА КОМАНДА /start от {update.effective_user.first_name}")
    try:
        user = update.effective_user
        await update.message.reply_text(f"✅ Бот работает! Привет, {user.first_name}!")
        logger.info("✅ Ответ отправлен")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

async def pisi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"🔥 ПОЛУЧЕНА КОМАНДА /pisi от {update.effective_user.first_name}")
    try:
        await update.message.reply_text("🍆 Команда /pisi получена! Добавляю сантиметры...")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"🔥 ПОЛУЧЕНА КОМАНДА /stats")
    await update.message.reply_text("📊 Статистика: 0 см")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"🔥 ПОЛУЧЕНА КОМАНДА /top")
    await update.message.reply_text("🏆 Топ пока пуст")

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pisi", pisi))
telegram_app.add_handler(CommandHandler("stats", stats))
telegram_app.add_handler(CommandHandler("top", top))

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

loop.run_until_complete(telegram_app.initialize())
loop.run_until_complete(telegram_app.start())

WEBHOOK_URL = "https://pisimetr-bot.onrender.com/webhook"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/')
def home():
    return "🍆 ПиСиметр бот работает! 🍆"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    async def setup():
        await telegram_app.bot.set_webhook(WEBHOOK_URL)
        commands_list = [BotCommand(cmd, desc) for cmd, desc in COMMANDS.items()]
        await telegram_app.bot.set_my_commands(commands_list)
        logger.info(f"✅ Webhook: {WEBHOOK_URL}")
        logger.info("✅ Бот готов!")
    
    loop.run_until_complete(setup())
    
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Flask сервер на порту {port}")
    app.run(host='0.0.0.0', port=port)
