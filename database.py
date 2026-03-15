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
            # ────────────────────────────────────────────────
            # НОВОЕ: Таблица мероприятий (Фаза 2)
            # ────────────────────────────────────────────────
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    source      TEXT    NOT NULL,
                    title       TEXT    NOT NULL,
                    description TEXT,
                    url         TEXT    NOT NULL UNIQUE,  -- UNIQUE для дедупликации
                    date_start  TEXT,
                    date_end    TEXT,
                    topics_json TEXT    DEFAULT '[]',     -- JSON: ["python", "вебинар"]
                    created_at  TEXT    DEFAULT (datetime('now')),
                    notified_at TEXT    DEFAULT NULL      -- NULL = ещё не разослано
                )
            ''')

            await cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_notify
                ON events (notified_at, date_start)
            ''')

            # ────────────────────────────────────────────────
            # НОВОЕ: Таблица тем групп (Фаза 2)
            # ────────────────────────────────────────────────
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_topics (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name    TEXT    NOT NULL UNIQUE,
                    keywords_json TEXT    DEFAULT '[]'   -- JSON: ["python", "программирование"]
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
            normalized_data = [
                (group_name, day_of_week.lower(), lesson_time)
                for group_name, day_of_week, lesson_time in data
            ]
            await cursor.executemany('''
                INSERT INTO schedule (group_name, day_of_week, lesson_time)
                VALUES (?, ?, ?)
            ''', normalized_data)
            await self.conn.commit()
            logger.info(f"Загружено новых записей расписания: {len(normalized_data)}")
            
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
            
    async def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            await self.conn.close()
            logger.info("Соединение с базой данных закрыто")

    async def add_event(self, event: dict) -> bool:
        """
        Сохраняет мероприятие в БД.
        Возвращает True если добавлено, False если дубликат (url уже есть).
        Использует INSERT OR IGNORE — при совпадении url просто пропускает.
        """
        import json
        from urllib.parse import urlparse, urlencode, parse_qsl

        # Очищаем URL от UTM-меток для надёжной дедупликации
        url = event.get('url', '')
        parsed = urlparse(url)
        clean_params = [(k, v) for k, v in parse_qsl(parsed.query)
                        if not k.startswith('utm_')]
        clean_url = parsed._replace(query=urlencode(clean_params)).geturl().rstrip('/')

        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                INSERT OR IGNORE INTO events
                    (source, title, description, url, date_start, date_end, topics_json)
                VALUES
                    (:source, :title, :description, :url,
                     :date_start, :date_end, :topics_json)
            ''', {
                'source': event.get('source', ''),
                'title': event.get('title', ''),
                'description': event.get('description', ''),
                'url': clean_url,
                'date_start': event.get('date_start'),
                'date_end': event.get('date_end'),
                'topics_json': json.dumps(
                    event.get('topics', []), ensure_ascii=False
                ),
            })
            await self.conn.commit()
            return cursor.rowcount > 0  # True = добавлено, False = дубликат


    async def get_unnotified_events(self) -> List[Dict]:
        """
        Возвращает предстоящие мероприятия, которые ещё не были разосланы.
        notified_at IS NULL — значит рассылка ещё не делалась.
        """
        import json
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                SELECT id, title, description, url, date_start, topics_json
                FROM events
                WHERE notified_at IS NULL
                    AND (date_start IS NULL
                        OR date_start > datetime('now'))
                ORDER BY date_start ASC
                ''')
            rows = await cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'url': row['url'],
                'date_start': row['date_start'],
                'topics': json.loads(row['topics_json'] or '[]'),
             })
        return result


    async def mark_event_notified(self, event_id: int):
        """
        Проставляет время рассылки. После этого событие не попадёт
        в get_unnotified_events() — повторной отправки не будет.
        Вызывать ПОСЛЕ успешной отправки уведомлений.
        """
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                UPDATE events
                SET notified_at = datetime('now')
                WHERE id = ?
            ''', (event_id,))
            await self.conn.commit()


    async def upsert_group_topics(self, group_name: str, keywords: list):
        """
        Добавляет группу или обновляет её ключевые слова.
        ON CONFLICT ... DO UPDATE — безопасно вызывать повторно.
        Именно так работают все upsert-операции в SQLite.
        """
        import json
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
                INSERT INTO group_topics (group_name, keywords_json)
                VALUES (:group_name, :keywords_json)
                ON CONFLICT(group_name) DO UPDATE
                    SET keywords_json = excluded.keywords_json
            ''', {
                'group_name': group_name,
                'keywords_json': json.dumps(keywords, ensure_ascii=False),
            })
            await self.conn.commit()


    async def find_matching_groups(self, event_topics: list) -> List[str]:
        """
        По темам события возвращает список групп, которым оно релевантно.
        Сравнение без учёта регистра: 'Python' == 'python'.

        Пример: event_topics = ['python', 'вебинар']
        Вернёт: ['Пайтон для начинающих']
        """
        import json
        if not event_topics:
            return []

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                'SELECT group_name, keywords_json FROM group_topics'
            )
            rows = await cursor.fetchall()

        # Множество тем события в нижнем регистре
        event_set = {t.lower() for t in event_topics}
        matched = []

        for row in rows:
            keywords = json.loads(row['keywords_json'] or '[]')
            group_set = {k.lower() for k in keywords}
            # Если есть хоть одно общее слово — группа получит уведомление
            if event_set & group_set:
                matched.append(row['group_name'])

        return matched



