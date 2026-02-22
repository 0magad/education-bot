# Работа с SQLite напрямую

## Вариант 1: Использовать скрипт load_data.py (РЕКОМЕНДУЕТСЯ)

Это проще - просто отредактируйте `load_data.py` и запустите:
```bash
python load_data.py
```

Бот автоматически создаст базу данных и таблицы при первом запуске.

---

## Вариант 2: Работа напрямую с SQLite

Если хотите работать через SQLite консоль:

### Шаг 1: Создать/открыть базу данных

В консоли SQLite:
```sql
.open data/bot.db
```

Если папки `data` нет, создайте её сначала или используйте:
```sql
.open bot.db
```

### Шаг 2: Создать таблицы

```sql
-- Таблица пользователей (ученики)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    class_level INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Таблица расписания занятий
CREATE TABLE IF NOT EXISTS schedule (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    class_level INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    lesson_time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subject, class_level, day_of_week, lesson_time)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_schedule_class_day 
ON schedule(class_level, day_of_week);

CREATE INDEX IF NOT EXISTS idx_schedule_day 
ON schedule(day_of_week);
```

### Шаг 3: Добавить учеников

```sql
INSERT OR REPLACE INTO users 
(user_id, class_level, full_name, username, first_name, last_name, updated_at)
VALUES 
(6218121239, 8, 'Иванов Иван Иванович', 'Rkelmx', 'Иван', 'Иванов', datetime('now')),
(987654321, 8, 'Петров Петр Петрович', 'petrov', 'Петр', 'Петров', datetime('now'));
```

### Шаг 4: Добавить расписание

```sql
INSERT OR IGNORE INTO schedule 
(subject, class_level, day_of_week, lesson_time)
VALUES 
('Математика', 8, 'вторник', '14:00'),
('Физика', 8, 'вторник', '16:30'),
('Математика', 8, 'среда', '10:00'),
('Химия', 8, 'среда', '12:00');
```

### Шаг 5: Проверить данные

```sql
-- Посмотреть всех учеников
SELECT * FROM users;

-- Посмотреть расписание для 8 класса на вторник
SELECT * FROM schedule WHERE class_level = 8 AND day_of_week = 'вторник';

-- Посмотреть всех учеников 8 класса
SELECT user_id, full_name, class_level FROM users WHERE class_level = 8;
```

---

## Полный пример сессии SQLite

```sql
-- Открыть базу данных
.open data/bot.db

-- Создать таблицы (если еще не созданы)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    class_level INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS schedule (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    class_level INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    lesson_time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subject, class_level, day_of_week, lesson_time)
);

-- Добавить ученика
INSERT OR REPLACE INTO users 
(user_id, class_level, full_name, username, first_name, last_name, updated_at)
VALUES 
(6218121239, 8, 'Иванов Иван Иванович', 'Rkelmx', 'Иван', 'Иванов', datetime('now'));

-- Добавить расписание
INSERT OR IGNORE INTO schedule 
(subject, class_level, day_of_week, lesson_time)
VALUES 
('Математика', 8, 'вторник', '14:00'),
('Физика', 8, 'вторник', '16:30');

-- Проверить
SELECT * FROM users;
SELECT * FROM schedule;
```

---

## Рекомендация

**Используйте `load_data.py`** - это проще и безопаснее:
1. Откройте `load_data.py`
2. Замените данные на свои
3. Запустите: `python load_data.py`

Бот автоматически создаст все таблицы при первом запуске!




