from flask import Flask, request, jsonify
import threading
import os
import logging
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, COMMANDS
from database import db
from messages import *

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаём Flask приложение
app = Flask(__name__)

# Глобальная переменная для бота
telegram_app = None

# --- Обработчики команд бота (те же, что в bot.py) ---
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
    
    user_data = db.add_cm(
        user.id, 
        chat.id, 
        user.username, 
        user.first_name, 
        user.last_name
    )
    
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
    stats = db.get_group_stats(chat.id)
    await update.message.reply_text(get_group_stats_message(stats, chat_title))

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text(
                "🍆 ПиСиметр активирован! 🍆\n\n"
                "Используйте /pisi раз в час чтобы растить Писю!\n"
                "Каждый раз выпадает РАНДОМ от 0.2 до 5 см!\n\n"
                "/top — топ чата по длине Писи\n"
                "/stats — моя статистика"
            )
        else:
            await update.message.reply_text(
                f"👋 Добро пожаловать, {member.first_name}!\n"
                f"Начинай растить свою Писю — используй /pisi! 🍆"
            )

def run_telegram_bot():
    """Запускает Telegram бота в отдельном потоке"""
    global telegram_app
    
    # Создаём приложение
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация команд
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("pisi", pisi))
    telegram_app.add_handler(CommandHandler("stats", stats))
    telegram_app.add_handler(CommandHandler("top", top))
    telegram_app.add_handler(CommandHandler("global_top", global_top))
    telegram_app.add_handler(CommandHandler("group_stats", group_stats))
    telegram_app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, 
        handle_new_member
    ))
    
    # Установка команд в меню бота
    async def set_commands():
        await telegram_app.bot.set_my_commands([
            BotCommand(cmd, desc) for cmd, desc in COMMANDS.items()
        ])
        logger.info("Команды бота установлены")
    
    # Запускаем в цикле событий
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(set_commands())
    
    # Запускаем polling
    logger.info("Telegram бот запущен и ждёт команды!")
    telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)

# --- Flask маршруты для Render ---
@app.route('/')
def home():
    """Главная страница — проверка что сервер работает"""
    return "🍆 ПиСиметр бот работает! 🍆"

@app.route('/health')
def health():
    """Health check для Render — чтобы сервис не отключался"""
    return "OK", 200

# --- Запуск ---
if __name__ == '__main__':
    # Запускаем Telegram бота в отдельном потоке
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер (Render требует порт из переменной PORT)
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Flask сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)