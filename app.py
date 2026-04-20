from flask import Flask, request, jsonify
import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask
app = Flask(__name__)

# Токен бота
BOT_TOKEN = "8730625454:AAFBDzXTVcC-aymhrG7Z5XZZ7O4Gm5JJspo"

# Команды
COMMANDS = {
    "start": "Запустить бота",
    "pisi": "Увеличить Писю (рандом 0.2-5 см, раз в час)",
    "stats": "Моя статистика",
    "top": "Топ чата",
    "group_stats": "Статистика группы"
}

# Импорт базы данных и сообщений
from database import db
from messages import *

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, join_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user.id, user.username, user.first_name, user.last_name, datetime.now().isoformat()))
    db.conn.commit()
    await update.message.reply_text(get_welcome_message(user.first_name))

async def pisi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    
    can_use, wait_seconds = db.can_use(user.id, chat.id)
    if not can_use:
        await update.message.reply_text(get_cooldown_message(wait_seconds))
        return
    
    user_data = db.add_cm(user.id, chat.id, user.username, user.first_name, user.last_name)
    
    top_users = db.get_group_top(chat.id, 10)
    position = None
    for i, u in enumerate(top_users, 1):
        if u[0] == user.id:
            position = i
            break
    
    await update.message.reply_text(get_pisi_success(user_data, position))

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_stats = db.get_user_stats(user.id)
    await update.message.reply_text(get_stats_message(user_stats))

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    chat_title = chat.title if chat.title else "этом чате"
    top_users = db.get_group_top(chat.id, 10)
    await update.message.reply_text(get_top_message(top_users, chat_title))

async def global_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global_top_users = db.get_global_top(10)
    await update.message.reply_text(get_top_message(global_top_users, "МИРЕ"))

async def group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    chat_title = chat.title if chat.title else "Этом чате"
    stats_data = db.get_group_stats(chat.id)
    await update.message.reply_text(get_group_stats_message(stats_data, chat_title))

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text(
                "🍆 ПиСиметр активирован! 🍆\n\nИспользуйте /pisi раз в час!\n/top — топ чата\n/stats — моя статистика"
            )
        else:
            await update.message.reply_text(f"👋 Добро пожаловать, {member.first_name}! Используй /pisi!")

# ========== СОЗДАНИЕ БОТА ==========
telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pisi", pisi))
telegram_app.add_handler(CommandHandler("stats", stats))
telegram_app.add_handler(CommandHandler("top", top))
telegram_app.add_handler(CommandHandler("global_top", global_top))
telegram_app.add_handler(CommandHandler("group_stats", group_stats))
telegram_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))

# ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ (ВАЖНО!)
async def init_app():
    await telegram_app.initialize()
    await telegram_app.start()
    return telegram_app

# ========== WEBHOOK ==========
WEBHOOK_URL = "https://pisimetr-bot.onrender.com/webhook"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        # Используем create_task вместо run для асинхронности
        asyncio.create_task(telegram_app.process_update(update))
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

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    # Установка webhook и команд
    async def setup():
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.bot.set_webhook(WEBHOOK_URL)
        commands_list = [BotCommand(cmd, desc) for cmd, desc in COMMANDS.items()]
        await telegram_app.bot.set_my_commands(commands_list)
        logger.info(f"✅ Webhook: {WEBHOOK_URL}")
        logger.info("✅ Бот готов!")
    
    asyncio.run(setup())
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Flask сервер на порту {port}")
    app.run(host='0.0.0.0', port=port)
