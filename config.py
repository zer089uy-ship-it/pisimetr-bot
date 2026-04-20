import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    # Запасной вариант - токен прямо в коде (только для Render!)
    BOT_TOKEN = "8730625454:AAFBDzXTVcC-aymhrG7Z5XZZ7O4Gm5JJspo"

COMMANDS = {
    "start": "Запустить бота",
    "pisi": "Увеличить Писю (рандом 0.2-5 см, раз в час)",
    "stats": "Моя статистика",
    "top": "Топ чата",
    "group_stats": "Статистика группы"
}

print(f"TOKEN LOADED: {BOT_TOKEN[:10]}...")
