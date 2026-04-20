import os

# Простое чтение токена
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Команды бота
COMMANDS = {
    "start": "Запустить бота",
    "pisi": "Увеличить Писю (рандом 0.2-5 см, раз в час)",
    "stats": "Моя статистика (общая длина Писи)",
    "top": "Топ участников чата по длине Писи",
    "group_stats": "Статистика группы"
}

# Для отладки - напечатаем в лог (удалишь потом)
print(f"DEBUG: BOT_TOKEN = {'SET' if BOT_TOKEN else 'NOT SET'}")
