"""
Модуль для работы с базой данных
"""
import aiosqlite
import logging
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str = 'data/bot.db'):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None
        
    async def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        # Создаем директорию для БД, если её нет
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        
        await self._create_tables()
        logger.info(f"База данных инициализирована: {self.db_path}")
        
    async def _create_tables(self):
        """Создание таблиц в базе данных"""
        async with self.conn.cursor() as cursor:
            # Проверяем и обновляем таблицу users, если нужно
            await cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            ''')
            users_table_exists = await cursor.fetchone()
            
            if users_table_exists:
                # Проверяем, есть ли поле full_name
                await cursor.execute('PRAGMA table_info(users)')
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'full_name' not in column_names:
                    logger.info("Добавляю поле full_name в таблицу users...")
                    await cursor.execute('ALTER TABLE users ADD COLUMN full_name TEXT')

                if 'group_name' not in column_names:
                    logger.info("Добавляю поле group_name в таблицу users...")
                    await cursor.execute('ALTER TABLE users ADD COLUMN group_name TEXT')
            
            # Таблица пользователей (ученики)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    full_name TEXT,
                    class_level INTEGER,
                    group_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Таблица для отслеживания последней отправки сообщения
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_reminders (
                    user_id INTEGER PRIMARY KEY,
                    last_reminder_time TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица для планировщика (для будущего использования)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TIMESTAMP,
                    completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица для истории взаимодействий с AI (для будущего использования)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message TEXT,
                    response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Проверяем, существует ли таблица schedule со старой структурой
            await cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schedule'
            ''')
            table_exists = await cursor.fetchone()
            
            if table_exists:
                # Проверяем структуру таблицы
                await cursor.execute('PRAGMA table_info(schedule)')
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Пересоздаем расписание, если это старая структура (класс/предмет) или какая-то промежуточная версия
                needs_recreate = (
                    'group_name' not in column_names
                    or 'subject' in column_names
                    or 'class_level' in column_names
                    or ('lesson_date' in column_names and 'day_of_week' not in column_names)
                )
                if needs_recreate:
                    logger.info("Обнаружена старая структура таблицы schedule. Пересоздаю таблицу...")
                    await cursor.execute('DROP INDEX IF EXISTS idx_schedule_class_day')
                    await cursor.execute('DROP INDEX IF EXISTS idx_schedule_day')
                    await cursor.execute('DROP INDEX IF EXISTS idx_schedule_group_day')
                    await cursor.execute('DROP INDEX IF EXISTS idx_schedule_group')
                    await cursor.execute('DROP TABLE IF EXISTS schedule')
                    await self.conn.commit()
            
            # Таблица расписания занятий (по дням недели и группам)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule (
                    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT NOT NULL,
                    day_of_week TEXT NOT NULL,
                    lesson_time TIME NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(group_name, day_of_week, lesson_time)
                )
            ''')
            
            # Индекс для быстрого поиска по группе и дню недели
            await cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_schedule_group_day 
                ON schedule(group_name, day_of_week)
            ''')
            
            # Индекс для поиска по дню недели
            await cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_schedule_day 
                ON schedule(day_of_week)
            ''')
            
            # Таблица логов действий администратора (5.3)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица обратной связи по ответам AI (5.2)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_feedback (
                    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    conversation_id INTEGER,
                    feedback TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            await self.conn.commit()

    async def add_user(self, user_id: int, username: str = None,
                       first_name: str = None, last_name: str = None,
                       full_name: str = None, group_name: str = None, class_level: int = None):
        """Добавление нового пользователя"""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, full_name, group_name, class_level, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, full_name, group_name, class_level, datetime.now()))
            await self.conn.commit()
            
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        async with self.conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
            
    async def get_all_active_users(self) -> List[Dict]:
        """Получение списка всех активных пользователей"""
        async with self.conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM users WHERE is_active = 1')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def update_last_reminder(self, user_id: int):
        """Обновление времени последнего напоминания"""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                INSERT OR REPLACE INTO user_reminders (user_id, last_reminder_time)
                VALUES (?, ?)
            ''', (user_id, datetime.now()))
            await self.conn.commit()
            
    async def get_last_reminder_time(self, user_id: int) -> Optional[datetime]:
        """Получение времени последнего напоминания"""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                SELECT last_reminder_time FROM user_reminders WHERE user_id = ?
            ''', (user_id,))
            row = await cursor.fetchone()
            if row and row['last_reminder_time']:
                return datetime.fromisoformat(row['last_reminder_time'])
            return None
            
    # Методы для работы с расписанием (новая структура)
    async def get_schedule_by_group_and_day(self, group_name: str, day_of_week: str) -> List[Dict]:
        """
        Получение расписания для группы на определенный день недели
        
        Args:
            group_name: Название группы
            day_of_week: День недели (понедельник, вторник, среда, четверг, пятница, суббота, воскресенье)
            
        Returns:
            Список занятий для группы на указанный день
        """
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                SELECT * FROM schedule 
                WHERE group_name = ? AND day_of_week = ?
                ORDER BY lesson_time
            ''', (group_name, day_of_week.lower()))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def get_students_by_group(self, group_name: str) -> List[Dict]:
        """
        Получение всех учащихся определенной группы
        
        Args:
            group_name: Название группы
            
        Returns:
            Список учащихся группы
        """
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                SELECT user_id, group_name, full_name, first_name, last_name, username
                FROM users 
                WHERE group_name = ? AND is_active = 1
                ORDER BY full_name, first_name
            ''', (group_name,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def get_today_schedule_by_groups(self) -> Dict[str, List[Dict]]:
        """
        Получение расписания на сегодня для всех групп
        
        Returns:
            Словарь {group_name: [занятия]}
        """
        from datetime import datetime
        # Получаем день недели на русском
        days_ru = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
        today_weekday = datetime.now().weekday()  # 0 = понедельник
        today_day = days_ru[today_weekday]
        
        # Получаем все группы
        async with self.conn.cursor() as cursor:
            await cursor.execute('SELECT DISTINCT group_name FROM users WHERE is_active = 1 AND group_name IS NOT NULL AND group_name != ""')
            groups = await cursor.fetchall()
        
        result = {}
        for group_row in groups:
            group_name = group_row['group_name']
            schedule = await self.get_schedule_by_group_and_day(group_name, today_day)
            if schedule:
                result[group_name] = schedule
                
        return result
            
    async def add_schedule_entry(self, group_name: str, day_of_week: str, lesson_time: str) -> int:
        """
        Добавление записи в расписание
        
        Args:
            group_name: Название группы
            day_of_week: День недели (понедельник, вторник, и т.д.)
            lesson_time: Время в формате HH:MM
            
        Returns:
            ID созданной записи
        """
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                INSERT OR IGNORE INTO schedule (group_name, day_of_week, lesson_time)
                VALUES (?, ?, ?)
            ''', (group_name, day_of_week.lower(), lesson_time))
            await self.conn.commit()
            return cursor.lastrowid
            
    async def get_user_schedule(self, user_id: int) -> List[Dict]:
        """
        Получение расписания пользователя на основе его группы
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список занятий для группы пользователя на текущую неделю
        """
        user = await self.get_user(user_id)
        if not user or not user.get('group_name'):
            return []
            
        from datetime import datetime
        days_ru = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
        
        result = []
        for day in days_ru:
            schedule = await self.get_schedule_by_group_and_day(user['group_name'], day)
            result.extend(schedule)
            
        return result
            
    # Методы для загрузки данных (для администраторов)
    async def bulk_add_schedule(self, data: List[tuple]):
        """
        Массовое добавление занятий в расписание.
        ВАЖНО: расписание считается «истиной» в Excel/CSV.
        При каждом запуске старое расписание ПОЛНОСТЬЮ заменяется новым.
        
        Args:
            data: Список кортежей (group_name, day_of_week, lesson_time)
                  Пример: [('Основы веб-программирования', 'вторник', '14:00')]
        """
        async with self.conn.cursor() as cursor:
            # Полностью очищаем расписание перед загрузкой новых данных,
            # чтобы все изменения в Excel/CSV сразу отражались в боте.
            await cursor.execute('DELETE FROM schedule')
            deleted = cursor.rowcount
            if deleted:
                logger.info(f"Очищено старых записей расписания: {deleted}")

            # Загружаем актуальные данные
            await cursor.executemany('''
                INSERT INTO schedule (group_name, day_of_week, lesson_time)
                VALUES (?, ?, ?)
            ''', data)
            await self.conn.commit()
            logger.info(f"Загружено новых записей расписания: {len(data)}")
            
    async def bulk_add_users(self, data: List[tuple]):
        """
        Массовое добавление пользователей
        
        Args:
            data: Список кортежей (user_id, group_name, full_name, username, first_name, last_name)
                  Пример: [(123456789, 'Основы веб-программирования', 'Иванов Иван Иванович', 'ivanov', 'Иван', 'Иванов')]
        """
        async with self.conn.cursor() as cursor:
            await cursor.executemany('''
                INSERT OR REPLACE INTO users 
                (user_id, group_name, full_name, username, first_name, last_name, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', [(row[0], row[1], row[2], row[3] if len(row) > 3 else None,
                   row[4] if len(row) > 4 else None, row[5] if len(row) > 5 else None, datetime.now()) 
                  for row in data])
            await self.conn.commit()

    # --- Совместимость со старой API ---
    async def get_schedule_by_class_and_day(self, class_level: int, day_of_week: str) -> List[Dict]:
        """Совместимость: раньше расписание было по классу. Теперь используйте get_schedule_by_group_and_day."""
        return []

    async def get_students_by_class(self, class_level: int) -> List[Dict]:
        """Совместимость: раньше учащиеся были по классу. Теперь используйте get_students_by_group."""
        return []

    async def get_today_schedule_by_classes(self) -> Dict[int, List[Dict]]:
        """Совместимость: раньше расписание было по классам. Теперь используйте get_today_schedule_by_groups."""
        return {}

    async def get_users_by_subject(self, subject: str) -> List[Dict]:
        """Совместимость: раньше выборка шла по предмету. Теперь subject == group_name."""
        return await self.get_students_by_group(subject)
            
    async def log_admin_action(self, action: str, details: str = None):
        """Логирование действия администратора (5.3)"""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                INSERT INTO admin_logs (action, details) VALUES (?, ?)
            ''', (action, details))
            await self.conn.commit()

    async def log_ai_feedback(self, user_id: int, conversation_id: int, feedback: str):
        """Сохранение оценки пользователем ответа AI (5.2)"""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                INSERT INTO ai_feedback (user_id, conversation_id, feedback)
                VALUES (?, ?, ?)
            ''', (user_id, conversation_id, feedback))
            await self.conn.commit()

    async def get_statistics(self) -> dict:
        """Получение статистики для вкладки «Аналитика» (5.3)"""
        stats: dict = {}
        async with self.conn.cursor() as cursor:
            # Всего активных пользователей
            await cursor.execute('SELECT COUNT(*) as cnt FROM users WHERE is_active = 1')
            stats['total_users'] = (await cursor.fetchone())['cnt']

            # Пользователи по группам
            await cursor.execute('''
                SELECT group_name, COUNT(*) as cnt FROM users
                WHERE is_active = 1 AND group_name IS NOT NULL AND group_name != ""
                GROUP BY group_name ORDER BY group_name
            ''')
            stats['users_by_group'] = {row['group_name']: row['cnt'] for row in await cursor.fetchall()}

            # Записей расписания
            await cursor.execute('SELECT COUNT(*) as cnt FROM schedule')
            stats['schedule_records'] = (await cursor.fetchone())['cnt']

            # Всего запросов к AI
            await cursor.execute('SELECT COUNT(*) as cnt FROM ai_conversations')
            stats['ai_queries'] = (await cursor.fetchone())['cnt']

            # Последняя загрузка данных
            await cursor.execute('''
                SELECT timestamp FROM admin_logs
                WHERE action LIKE '%load%' ORDER BY timestamp DESC LIMIT 1
            ''')
            row = await cursor.fetchone()
            stats['last_load'] = row['timestamp'] if row else None

            # Оценки ответов AI
            await cursor.execute('''
                SELECT feedback, COUNT(*) as cnt FROM ai_feedback GROUP BY feedback
            ''')
            feedback_rows = await cursor.fetchall()
            stats['ai_feedback'] = {row['feedback']: row['cnt'] for row in feedback_rows}

        return stats

    async def get_last_conversation_id(self, user_id: int) -> Optional[int]:
        """Получить ID последнего диалога пользователя"""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                SELECT conversation_id FROM ai_conversations
                WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1
            ''', (user_id,))
            row = await cursor.fetchone()
            return row['conversation_id'] if row else None

    async def save_ai_message(self, user_id: int, message: str, response: str):
        """Сохранение сообщения пользователя и ответа AI в историю диалога"""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                INSERT INTO ai_conversations (user_id, message, response)
                VALUES (?, ?, ?)
            ''', (user_id, message, response))
            await self.conn.commit()

    async def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получение последних N пар (сообщение / ответ) из истории диалога пользователя.
        Возвращает в хронологическом порядке (сначала старые)."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                SELECT message, response FROM ai_conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            rows = await cursor.fetchall()
        # Разворачиваем: получили DESC, нужен ASC для промпта
        return [dict(row) for row in reversed(rows)]

    async def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            await self.conn.close()
            logger.info("Соединение с базой данных закрыто")



