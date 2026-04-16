# DEPLOYMENT_EXAMPLES.md — Примеры конфигов и быстрые старты

## 📋 Содержание

1. [Примеры .env](#примеры-env)
2. [Примеры organization.yaml](#примеры-organizationyaml)
3. [Сценарии развертывания](#сценарии-развертывания)
4. [Быстрая шпаргалка](#быстрая-шпаргалка)

---

## Примеры .env

### Пример 1: Школа с Ollama (локально)

```env
# .env для локального запуска с Ollama

# === Основное ===
BOT_TOKEN=5087969535:AAGmZ7p9-K_t2E3kPqRsT6uVwXyZa1BcDeFgHiJkL
ORGANIZATION_NAME=Школа №1
ORGANIZATION_DESCRIPTION=Средняя общеобразовательная школа №1
SUPPORT_CONTACT=@school_support

# === AI: Ollama (локально) ===
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# === БД ===
DB_PATH=data/bot.db
DB_PATH_ANALYTICS=data/analytics.db

# === Логирование ===
LOG_LEVEL=INFO
```

### Пример 2: Центр дополнительного образования с Groq

```env
# .env для облачного запуска с Groq

# === Основное ===
BOT_TOKEN=5087969535:AAGmZ7p9-K_t2E3kPqRsT6uVwXyZa1BcDeFgHiJkL
ORGANIZATION_NAME=Центр развития "Умный класс"
ORGANIZATION_DESCRIPTION=Центр дополнительного образования для детей
SUPPORT_CONTACT=@umc_support
LOGO_PATH=assets/umc_logo.png

# === AI: Groq (облако, быстро, бесплатно) ===
AI_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === БД ===
DB_PATH=data/bot.db
DB_PATH_ANALYTICS=

# === Резервный провайдер ===
FALLBACK_AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === Логирование ===
LOG_LEVEL=INFO
```

### Пример 3: Компания с OpenAI

```env
# .env для корпоративного использования с OpenAI (платно)

# === Основное ===
BOT_TOKEN=5087969535:AAGmZ7p9-K_t2E3kPqRsT6uVwXyZa1BcDeFgHiJkL
ORGANIZATION_NAME=TechCorp
ORGANIZATION_DESCRIPTION=Учебный отдел компании TechCorp
SUPPORT_CONTACT=@techcorp_training

# === AI: OpenAI (облако, лучшее качество, платно) ===
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AI_MODEL=gpt-4

# === Резервный провайдер ===
FALLBACK_AI_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === БД ===
DB_PATH=data/bot.db

# === Логирование ===
LOG_LEVEL=WARNING  # Меньше логов в продакшене
```

### Пример 4: Университет с несколькими БД (мульти-факультет)

```env
# .env для большого учреждения с несколькими БД

# === Основное ===
BOT_TOKEN=5087969535:AAGmZ7p9-K_t2E3kPqRsT6uVwXyZa1BcDeFgHiJkL
ORGANIZATION_NAME=Московский Государственный Университет
ORGANIZATION_DESCRIPTION=МГУ имени М.В. Ломоносова
SUPPORT_CONTACT=@msu_support

# === AI: Groq ===
AI_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === Несколько БД для разных факультетов ===
DB_PATH=data/bot.db                      # Основная БД
DB_PATH_ANALYTICS=data/analytics.db      # Аналитика
# Дополнительно в коде можно переключать:
# DB_FACULTY_1=data/faculty_1.db
# DB_FACULTY_2=data/faculty_2.db

# === Логирование ===
LOG_LEVEL=DEBUG  # Детальное логирование для отладки
```

---

## Примеры organization.yaml

### Пример 1: Школа

```yaml
# organization.yaml для школы

organization:
  name: "Школа №1"
  description: "Средняя общеобразовательная школа №1 города Москва"
  support_contact: "@school1_support"
  logo_path: "assets/school1_logo.png"
  abbreviation: "СОШ1"
  region: "Москва"
  website: "https://school1.edu.ru"

groups:
  default:
    - "1A"
    - "1B"
    - "1В"
    - "2A"
    - "2B"
    - "2В"
    - "3A"
    - "3B"
    - "3В"
    - "4A"
    - "4B"
    - "4В"

branding:
  primary_color: "#1F77E4"
  secondary_color: "#25C6DA"
  emoji: "🎓"
  greeting_phrase: "Добро пожаловать в"

schedule:
  reminder_advance_minutes: 30
  enable_broadcasts: true

features:
  tutor:
    enabled: true
    context_messages: 10
  scheduler:
    enabled: true
  reference:
    enabled: true

version: "1.0"
```

### Пример 2: Центр дополнительного образования

```yaml
# organization.yaml для центра доп. образования

organization:
  name: "Центр развития \"Умный класс\""
  description: "Центр дополнительного образования для детей 5-16 лет"
  support_contact: "@smartclass_help"
  logo_path: "assets/smartclass_logo.png"
  abbreviation: "УК"
  region: "СПб"
  website: "https://smartclass.local"

groups:
  default:
    - "Группа 1 (5-6 лет)"
    - "Группа 2 (7-8 лет)"
    - "Группа 3 (9-10 лет)"
    - "Группа 4 (11-12 лет)"
    - "Группа 5 (13-14 лет)"
    - "Группа 6 (15-16 лет)"

branding:
  primary_color: "#FF6B6B"
  secondary_color: "#4ECDC4"
  emoji: "🚀"
  greeting_phrase: "Привет в"

schedule:
  reminder_advance_minutes: 60
  enable_broadcasts: true

features:
  tutor:
    enabled: true
    context_messages: 5
  scheduler:
    enabled: true
  reference:
    enabled: true
  quick_questions:
    enabled: true
    questions:
      - "Объясни тему"
      - "Дай пример"
      - "Проверь решение"

version: "1.0"
```

### Пример 3: Компания (обучение сотрудников)

```yaml
# organization.yaml для компании

organization:
  name: "TechCorp University"
  description: "Корпоративный университет для сотрудников TechCorp"
  support_contact: "@techcorp_training"
  logo_path: "assets/techcorp_logo.png"
  abbreviation: "TCU"
  region: "Silicon Valley"
  website: "https://university.techcorp.com"

groups:
  default:
    - "Новые сотрудники"
    - "Middle Engineers"
    - "Senior Engineers"
    - "Tech Leads"
    - "Management"

branding:
  primary_color: "#000000"
  secondary_color: "#00FF00"
  emoji: "💻"
  greeting_phrase: "Добро пожаловать в"

schedule:
  reminder_advance_minutes: 15
  enable_broadcasts: false  # Без рассылок в компании

features:
  tutor:
    enabled: true
    context_messages: 20  # Больше контекста для взрослых
  scheduler:
    enabled: true
  reference:
    enabled: true
  answer_rating:
    enabled: true  # Оценка ответов для отслеживания качества

admin:
  confirm_bulk_actions: true
  enable_action_logging: true

version: "1.0"
```

---

## Сценарии развертывания

### Сценарий 1: Быстрый старт на Windows

```powershell
# 1. Скачиваем проект (архив с GitHub)
# 2. Распаковываем в папку chatbot
# 3. Открываем PowerShell в папке chatbot
# 4. Запускаем скрипт развертывания

.\deploy.ps1

# 5. При запросе вводим:
#    - Название организации: Школа №1
#    - Токен бота: получен от @BotFather

# 6. Скрипт сам установит всё необходимое
# 7. Редактируем .env для добавления API ключей (если нужны)
# 8. Запускаем бота

python bot.py

# ✓ Готово!
```

### Сценарий 2: Развертывание на Linux сервере

```bash
# Подключаемся по SSH
ssh user@your_server.com

# Клонируем репозиторий
git clone https://github.com/yourname/chatbot.git
cd chatbot

# Даём права на скрипт
chmod +x deploy.sh

# Запускаем развертывание
./deploy.sh

# Вводим данные организации
# Скрипт всё установит и инициализирует

# Отредактируем .env для продакшена
nano .env

# Запускаем бота в фоне (или через systemd)
nohup python bot.py > bot.log 2>&1 &

# Мониторим логи
tail -f bot.log
```

### Сценарий 3: Docker контейнер

```dockerfile
# Dockerfile для развертывания в Docker

FROM python:3.11-slim

WORKDIR /app

# Копируем файлы проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Переменные окружения из .env будут переданы при запуске
ENV PYTHONUNBUFFERED=1

# Инициализируем БД и запускаем бота
CMD ["python", "bot.py"]
```

Запуск в Docker:

```bash
# Создаём образ
docker build -t chatbot:latest .

# Запускаем контейнер с переменными окружения
docker run -d \
  --name chatbot \
  -e BOT_TOKEN="your_token" \
  -e ORGANIZATION_NAME="Школа №1" \
  -e AI_PROVIDER="groq" \
  -e GROQ_API_KEY="your_key" \
  -v chatbot_data:/app/data \
  chatbot:latest

# Смотрим логи
docker logs -f chatbot

# Останавливаем
docker stop chatbot
```

### Сценарий 4: Несколько организаций на одном сервере

```bash
# Структура проекта для нескольких организаций

/serverapps/
├── chatbot_school1/          # Первая организация
│   ├── data/
│   ├── bot.py
│   ├── .env
│   └── organization.yaml
│
├── chatbot_school2/          # Вторая организация
│   ├── data/
│   ├── bot.py
│   ├── .env
│   └── organization.yaml
│
└── chatbot_college/          # Третья организация
    ├── data/
    ├── bot.py
    ├── .env
    └── organization.yaml

# Запуск всех ботов через supervisor или systemd

# systemd сервис для школы 1:
# /etc/systemd/system/chatbot-school1.service

[Unit]
Description=ChatBot for School 1
After=network.target

[Service]
Type=simple
User=chatbot
WorkingDirectory=/serverapps/chatbot_school1
Environment="PATH=/serverapps/chatbot_school1/venv/bin"
ExecStart=/serverapps/chatbot_school1/venv/bin/python bot.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# Дальше по аналогии для школы 2, коллежа и т.д.
```

---

## Быстрая шпаргалка

### Команды для администратора

```bash
# === ИНИЦИАЛИЗАЦИЯ ===

# Создать venv
python3 -m venv venv

# Активировать venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows

# Установить зависимости
pip install -r requirements.txt

# Инициализировать организацию
python init_organization.py --name "Организация" --token "токен"


# === ЗАПУСК БОТА ===

# Обычный запуск
python bot.py

# С логами в файл
python bot.py > bot.log 2>&1 &

# В фоне (Linux)
nohup python bot.py > bot.log 2>&1 &

# С отладкой
LOG_LEVEL=DEBUG python bot.py


# === АДМИНИСТРИРОВАНИЕ ===

# Загрузить данные
python admin_loader.py

# Проверить здоровье бота
python health_check.py

# Экспортировать аналитику
python -c "from admin_loader_excel import ExcelExporter; import asyncio; asyncio.run(ExcelExporter().export_all())"

# Создать резервную копию
python -c "from database import Database; import asyncio; db = Database(); asyncio.run(db.backup())"


# === ОТЛАДКА ===

# Проверить конфиг
python -c "from config import Config; print(Config.get_organization_name())"

# Проверить БД
python -c "from database import Database; import asyncio; db = Database(); asyncio.run(db.init_db())"

# Проверить AI
python -c "from modules.ai_tutor import AITutor; ai = AITutor(); print('OK' if ai.initialized else 'Error')"


# === МОНИТОРИНГ ===

# Следить за логами
tail -f data/logs/bot.log

# Посчитать сообщений в БД
sqlite3 data/bot.db "SELECT COUNT(*) FROM messages;"

# Остановить бота
pkill -f "python bot.py"  # Linux/macOS
taskkill /IM python.exe /F  # Windows
```

### Переменные окружения

| Переменная | Обязательная | Пример |
|-----------|-----------|---------|
| `BOT_TOKEN` | ✅ | `5087969535:AAGmZ7p...` |
| `ORGANIZATION_NAME` | ✅ | `Школа №1` |
| `AI_PROVIDER` | ❌ | `ollama`, `groq`, `openai` |
| `GROQ_API_KEY` | ❌ | `gsk_xxx...` |
| `OLLAMA_BASE_URL` | ❌ | `http://localhost:11434` |
| `OLLAMA_MODEL` | ❌ | `llama3.1` |
| `DB_PATH` | ❌ | `data/bot.db` |
| `LOG_LEVEL` | ❌ | `INFO`, `DEBUG`, `WARNING` |

### Структура проекта

```
chatbot/
├── 📄 bot.py                    Основной скрипт бота
├── 📄 config.py                 Конфигурация + загрузка YAML
├── 📄 database.py               Работа с БД (SQLite)
├── 📄 handlers.py               Обработчики команд/сообщений
├── 📄 scheduler.py              Планировщик расписания
│
├── 📄 admin_loader.py           GUI админ-интерфейс
├── 📄 admin_loader_excel.py     Загрузка из Excel
├── 📄 init_organization.py      Инициализация организации
├── 📄 health_check.py           Проверка здоровья бота
│
├── ⚙️ .env                       Переменные окружения (не в git!)
├── 📋 organization.yaml         Конфиг организации (TASK 3.1)
├── 💬 messages.yaml             Все сообщения бота (TASK 3.3)
├── 👥 groups.yaml               Список групп (TASK 3.2)
├── 📦 requirements.txt           Зависимости Python
│
├── 🚀 deploy.sh                 Скрипт развертывания (Linux/macOS)
├── 🚀 deploy.ps1                Скрипт развертывания (Windows)
├── 📚 DEPLOYMENT.md             Полная инструкция (ВЫ ЗДЕСЬ)
├── 📚 ADVANCED_FEATURES.md      Продвинутые функции
│
├── 📁 modules/                  Модули бота
│   ├── ai_tutor.py              ИИ-репетитор
│   ├── planner.py               Планировщик
│   └── reference.py             Справочник знаний
│
├── 📁 data/                     Данные организации
│   ├── bot.db                   Основная БД (SQLite)
│   ├── backups/                 Резервные копии
│   └── logs/                    Логи приложения
│
└── 📁 assets/                   Медиафайлы
    └── logo.png                 Логотип организации
```

---

**Последнее обновление**: April 16, 2026
