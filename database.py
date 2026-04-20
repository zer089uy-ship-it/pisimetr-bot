import sqlite3
from datetime import datetime, timedelta
import threading
import random

class Database:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        self.conn = sqlite3.connect('pisimetr.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                total_cm REAL DEFAULT 0.0,
                total_uses INTEGER DEFAULT 0,
                last_growth REAL DEFAULT 0.0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица групповой статистики
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                total_cm REAL DEFAULT 0.0,
                total_uses INTEGER DEFAULT 0,
                last_growth REAL DEFAULT 0.0,
                UNIQUE(chat_id, user_id)
            )
        ''')
        
        # Таблица для хранения времени следующего использования
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                next_available TIMESTAMP,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        
        self.conn.commit()
    
    def get_random_cm(self) -> float:
        """Генерирует случайное число от 0.2 до 5 с округлением до 1 знака"""
        return round(random.uniform(0.2, 5.0), 1)
    
    def can_use(self, user_id: int, chat_id: int) -> tuple:
        """Проверяет, может ли пользователь использовать команду. Возвращает (можно, время_ожидания_в_секундах)"""
        self.cursor.execute(
            "SELECT next_available FROM cooldowns WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id)
        )
        result = self.cursor.fetchone()
        
        if not result:
            return True, 0
        
        next_available = datetime.fromisoformat(result[0])
        if datetime.now() >= next_available:
            return True, 0
        
        wait_seconds = int((next_available - datetime.now()).total_seconds())
        return False, wait_seconds
    
    def add_cm(self, user_id: int, chat_id: int, username: str, first_name: str, last_name: str = "") -> dict:
        """Добавляет случайное количество сантиметров пользователю"""
        now = datetime.now()
        next_hour = now + timedelta(hours=1)
        
        # Генерируем случайное количество сантиметров
        growth_cm = self.get_random_cm()
        
        # Обновляем или создаем запись в cooldowns
        self.cursor.execute('''
            INSERT INTO cooldowns (user_id, chat_id, next_available)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, chat_id) 
            DO UPDATE SET next_available = excluded.next_available
        ''', (user_id, chat_id, next_hour.isoformat()))
        
        # Получаем текущие значения пользователя
        self.cursor.execute(
            "SELECT total_cm, total_uses FROM users WHERE user_id = ?",
            (user_id,)
        )
        user_current = self.cursor.fetchone()
        
        new_total_cm = (user_current[0] if user_current else 0) + growth_cm
        new_total_uses = (user_current[1] if user_current else 0) + 1
        
        # Обновляем глобальную статистику пользователя
        self.cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, total_cm, total_uses, last_growth, join_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                total_cm = total_cm + excluded.total_cm - total_cm,
                total_uses = total_uses + 1,
                last_growth = excluded.last_growth,
                username = COALESCE(excluded.username, username),
                first_name = COALESCE(excluded.first_name, first_name)
        ''', (user_id, username, first_name, last_name, growth_cm, 1, growth_cm, now.isoformat()))
        
        # Обновляем групповую статистику
        self.cursor.execute('''
            INSERT INTO group_stats (chat_id, user_id, total_cm, total_uses, last_growth)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                total_cm = total_cm + excluded.total_cm,
                total_uses = total_uses + 1,
                last_growth = excluded.last_growth
        ''', (chat_id, user_id, growth_cm, 1, growth_cm))
        
        # Получаем обновленные данные для ответа
        self.cursor.execute(
            "SELECT total_cm, total_uses FROM users WHERE user_id = ?",
            (user_id,)
        )
        user_data = self.cursor.fetchone()
        
        self.cursor.execute(
            "SELECT total_cm FROM group_stats WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        )
        group_cm = self.cursor.fetchone()
        
        self.conn.commit()
        
        return {
            "growth_cm": growth_cm,
            "total_cm": round(user_data[0], 1) if user_data else growth_cm,
            "total_uses": user_data[1] if user_data else 1,
            "group_cm": round(group_cm[0], 1) if group_cm else growth_cm
        }
    
    def get_user_stats(self, user_id: int) -> dict:
        """Получает глобальную статистику пользователя"""
        self.cursor.execute(
            "SELECT total_cm, total_uses, join_date, last_growth FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = self.cursor.fetchone()
        
        if result:
            return {
                "total_cm": round(result[0], 1),
                "total_uses": result[1],
                "join_date": result[2],
                "last_growth": round(result[3], 1) if result[3] else 0
            }
        return {"total_cm": 0.0, "total_uses": 0, "join_date": None, "last_growth": 0.0}
    
    def get_group_top(self, chat_id: int, limit: int = 10) -> list:
        """Получает топ пользователей в группе по сантиметрам"""
        self.cursor.execute('''
            SELECT gs.user_id, gs.total_cm, gs.total_uses, u.username, u.first_name, u.last_name
            FROM group_stats gs
            LEFT JOIN users u ON gs.user_id = u.user_id
            WHERE gs.chat_id = ?
            ORDER BY gs.total_cm DESC
            LIMIT ?
        ''', (chat_id, limit))
        
        return self.cursor.fetchall()
    
    def get_global_top(self, limit: int = 10) -> list:
        """Получает глобальный топ пользователей по сантиметрам"""
        self.cursor.execute('''
            SELECT user_id, total_cm, total_uses, username, first_name, last_name
            FROM users
            ORDER BY total_cm DESC
            LIMIT ?
        ''', (limit,))
        
        return self.cursor.fetchall()
    
    def get_group_stats(self, chat_id: int) -> dict:
        """Получает общую статистику группы"""
        self.cursor.execute(
            "SELECT COUNT(*), SUM(total_cm), SUM(total_uses) FROM group_stats WHERE chat_id = ?",
            (chat_id,)
        )
        result = self.cursor.fetchone()
        
        return {
            "total_users": result[0] if result[0] else 0,
            "total_cm": round(result[1], 1) if result[1] else 0.0,
            "total_uses": result[2] if result[2] else 0
        }
    
    def close(self):
        self.conn.close()

# Создаем глобальный экземпляр
db = Database()