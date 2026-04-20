def format_time(seconds: int) -> str:
    """Форматирует секунды в читаемый вид"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours} ч {minutes} мин"
    elif minutes > 0:
        return f"{minutes} мин {secs} сек"
    else:
        return f"{secs} сек"

def get_welcome_message(first_name: str) -> str:
    return f"""
🍆 Привет, {first_name}!

Добро пожаловать в ПиСиметр — игру для чатов, где каждый может растить свою Писю!

⚡ Как играть:
• Используй /pisi раз в час
• Каждый раз ты получаешь РАНДОМНУЮ ПРИБАВКУ от 0.2 до 5 см
• Соревнуйся с другими участниками

📊 Команды:
/stats - моя статистика (общая длина Писи)
/top - топ чата по длине Писи
/group_stats - статистика группы

Погнали! 🚀
"""

def get_pisi_success(user_data: dict, group_top_position: int = None) -> str:
    # Эмодзи в зависимости от размера прибавки
    if user_data['growth_cm'] >= 4:
        growth_emoji = "💥💦 ОГО! МОЩНЫЙ РОСТ! 💦💥"
    elif user_data['growth_cm'] >= 3:
        growth_emoji = "🔥 Неплохая прибавка! 🔥"
    elif user_data['growth_cm'] >= 1.5:
        growth_emoji = "📈 Хороший рост! 📈"
    elif user_data['growth_cm'] >= 0.5:
        growth_emoji = "🌱 Маленький, но рост 🌱"
    else:
        growth_emoji = "😅 Ну хоть что-то... 😅"
    
    text = f"""
🍆 РЕЗУЛЬТАТ ТВОЕЙ ПИСИ

{growth_emoji}
📏 Прибавка: +{user_data['growth_cm']} см

📊 Твоя ПИСЯ теперь:
• В этом чате: {user_data['group_cm']} см
• Всего во всех чатах: {user_data['total_cm']} см
• Количество ростов: {user_data['total_uses']}

"""
    if group_top_position:
        if group_top_position == 1:
            text += f"\n👑 ТЫ ПЕРВЫЙ В ТОПЕ ЧАТА! 👑"
        elif group_top_position == 2:
            text += f"\n🥈 Ты на 2 месте в топе чата!"
        elif group_top_position == 3:
            text += f"\n🥉 Ты на 3 месте в топе чата!"
        else:
            text += f"\n🏆 Ты на {group_top_position}-м месте в топе чата!"
    
    text += "\n\n⏰ Следующий рост Писи возможен через 1 час"
    return text

def get_cooldown_message(wait_seconds: int) -> str:
    return f"""
⏳ Пися ещё не готова к новому росту!

Следующее использование /pisi будет доступно через:
{format_time(wait_seconds)}

Подрастай позже! 🌟
"""

def get_stats_message(user_stats: dict) -> str:
    if user_stats["total_cm"] == 0.0:
        return "📭 У тебя пока нет Писи!\n\nИспользуй /pisi чтобы начать рост!"
    
    # Визуализация длины Писи
    cm = user_stats["total_cm"]
    if cm >= 30:
        pipe = "🍆" + "=" * int(min(cm / 2, 20)) + "💪 САМОРОДОК!"
    elif cm >= 15:
        pipe = "🍆" + "=" * int(cm / 1.5)
    elif cm >= 8:
        pipe = "🍆" + "=" * int(cm)
    else:
        pipe = "🌱" * int(cm) if cm < 5 else "🍆" + "=" * int(cm/2)
    
    return f"""
📊 ТВОЯ СТАТИСТИКА ПИСИ

{pipe}

📏 Общая длина: {user_stats['total_cm']} см
🔄 Всего использований /pisi: {user_stats['total_uses']}
📈 Последний рост: +{user_stats['last_growth']} см
📅 Дата первого роста: {user_stats['join_date'][:10] if user_stats['join_date'] else 'сегодня'}

Продолжай растить! 💪🍆
"""

def get_top_message(users: list, chat_title: str = "этом чате") -> str:
    if not users:
        return f"📭 В {chat_title} пока нет участников с Писей\n\nБудь первым — используй /pisi!"
    
    text = f"🏆 ТОП ПИСЬ В {chat_title.upper()} 🏆\n\n"
    
    for i, user in enumerate(users, 1):
        user_id, total_cm, total_uses, username, first_name, last_name = user
        name = username if username else (first_name if first_name else f"User_{user_id}")
        
        # Эмодзи в зависимости от места
        if i == 1:
            medal = "👑🥇 "
            if total_cm >= 20:
                medal = "👑🍆💪 "
        elif i == 2:
            medal = "🥈 "
        elif i == 3:
            medal = "🥉 "
        else:
            medal = f"{i}. "
        
        # Визуализация длины
        if total_cm >= 15:
            visual = "🍆🍆🍆"
        elif total_cm >= 8:
            visual = "🍆🍆"
        elif total_cm >= 3:
            visual = "🍆"
        else:
            visual = "🌱"
        
        text += f"{medal}{name} — {total_cm} см {visual}\n"
    
    return text

def get_group_stats_message(stats: dict, chat_title: str) -> str:
    avg_cm = stats['total_cm'] / stats['total_users'] if stats['total_users'] > 0 else 0
    
    return f"""
📊 СТАТИСТИКА ПИСЬ В ЧАТЕ «{chat_title}»

👥 Участников с Писей: {stats['total_users']}
📏 Общая длина всех пись: {stats['total_cm']} см
🔄 Всего использований /pisi: {stats['total_uses']}
⭐ Средняя длина Писи: {round(avg_cm, 1)} см

Используй /top чтобы увидеть лидеров!
"""
