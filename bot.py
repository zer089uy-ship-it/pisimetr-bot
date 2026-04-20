#!/usr/bin/env python3
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

async def post_init(application: Application) -> None:
    """Установка команд бота после запуска"""
    await application.bot.set_my_commands([
        BotCommand(cmd, desc) for cmd, desc in COMMANDS.items()
    ])
    logger.info("Бот ПиСиметр (версия pisi) запущен!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Сохраняем пользователя в БД при старте
    db.cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, join_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user.id, user.username, user.first_name, user.last_name, datetime.now().isoformat()))
    db.conn.commit()
    
    await update.message.reply_text(get_welcome_message(user.first_name))

async def pisi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Основная игровая команда /pisi - рост Писи"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Проверяем, можно ли использовать команду
    can_use, wait_seconds = db.can_use(user.id, chat.id)
    
    if not can_use:
        await update.message.reply_text(get_cooldown_message(wait_seconds))
        return
    
    # Добавляем случайные сантиметры
    user_data = db.add_cm(
        user.id, 
        chat.id, 
        user.username, 
        user.first_name, 
        user.last_name
    )
    
    # Получаем позицию в топе
    top_users = db.get_group_top(chat.id, 10)
    position = None
    for i, u in enumerate(top_users, 1):
        if u[0] == user.id:
            position = i
            break
    
    await update.message.reply_text(get_pisi_success(user_data, position))

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /stats - личная статистика Писи"""
    user = update.effective_user
    
    user_stats = db.get_user_stats(user.id)
    
    await update.message.reply_text(get_stats_message(user_stats))

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /top - топ чата по длине Писи"""
    chat = update.effective_chat
    chat_title = chat.title if chat.title else "этом чате"
    
    top_users = db.get_group_top(chat.id, 10)
    
    await update.message.reply_text(get_top_message(top_users, chat_title))

async def global_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /global_top - глобальный топ"""
    global_top_users = db.get_global_top(10)
    
    await update.message.reply_text(get_top_message(global_top_users, "МИРЕ"))

async def group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /group_stats - статистика группы"""
    chat = update.effective_chat
    chat_title = chat.title if chat.title else "Этом чате"
    
    stats = db.get_group_stats(chat.id)
    
    await update.message.reply_text(get_group_stats_message(stats, chat_title))

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствие новых участников"""
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            # Бот добавлен в группу
            await update.message.reply_text(
                "🍆 ПиСиметр активирован! 🍆\n\n"
                "Используйте /pisi раз в час чтобы растить Писю!\n"
                "Каждый раз выпадает РАНДОМ от 0.2 до 5 см!\n\n"
                "/top — топ чата по длине Писи\n"
                "/stats — моя статистика"
            )
        else:
            # Новый участник
            await update.message.reply_text(
                f"👋 Добро пожаловать, {member.first_name}!\n"
                f"Начинай растить свою Писю — используй /pisi! 🍆"
            )

def main() -> None:
    """Запуск бота"""
    if not BOT_TOKEN or BOT_TOKEN == "ВАШ_ТОКЕН_ОТ_BOTFATHER":
        print("❌ Ошибка: Укажите BOT_TOKEN в config.py!")
        print("Получите токен у @BotFather в Telegram")
        return
    
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pisi", pisi))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("top", top))
    application.add_handler(CommandHandler("global_top", global_top))
    application.add_handler(CommandHandler("group_stats", group_stats))
    
    # Обработчик новых участников
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, 
        handle_new_member
    ))
    
    # Запуск бота
    print("🚀 Запуск бота ПиСиметр (версия /pisi с рандомом 0.2-5 см)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
