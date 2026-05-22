# DEPLOYMENT.md — Развертывание ChatBot для новой организации

## 📋 Оглавление

1. [Обзор](#обзор)
2. [Требования](#требования)
3. [Быстрый старт (30-60 минут)](#быстрый-старт)
4. [Подробное развертывание](#подробное-развертывание)
5. [Настройка AI](#настройка-ai)
6. [Загрузка данных](#загрузка-данных)
7. [Первый запуск](#первый-запуск)
8. [Администрирование](#администрирование)
9. [Решение проблем](#решение-проблем)
10. [FAQ](#faq)

---

## Обзор

### Что такое ChatBot?

ChatBot — это Telegram бот с ИИ-репетитором для образовательных учреждений. Каждое учреждение может развернуть свой экземпляр бота с:

- ✅ Своим названием и брендингом
- ✅ Своими группами (классами)
- ✅ Своим расписанием
- ✅ Своим ИИ-ассистентом
- ✅ Своей базой данных

### Время развертывания

- ⚡ **Быстро** (30 минут): использование готовых скриптов + Ollama локально
- 📦 **Стандартно** (60 минут): установка вручную + выбор AI провайдера
- 🔧 **Полно** (2+ часа): полная настройка всех компонент + тестирование

---

## Требования

### Для сервера

- **ОС**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.9 или выше
- **Память**: 2+ ГБ (для Ollama — 4+ ГБ)
- **Диск**: 500 МБ + место для БД (в зависимости от объема учащихся)

### Для Telegram бота

1. Telegram аккаунт (@username)
2. BotFather в Telegram для создания бота

### API ключи (выберите один)

- **Ollama** (локально, бесплатно) — никаких ключей
- **Groq** — бесплатный GROQ_API_KEY
- **Google Gemini** — бесплатный GEMINI_API_KEY
- **OpenAI** — платный OPENAI_API_KEY

---

## Быстрый старт

### Для Linux / macOS

```bash
# 1. Клонируем или распаковываем проект
git clone <repo_url> chatbot
cd chatbot

# 2. Даём права на выполнение и запускаем скрипт
chmod +x deploy.sh
./deploy.sh

# 3. Следуем инструкциям в скрипте
# Введите название организации и токен бота
```

### Для Windows

```powershell
# 1. Клонируем или распаковываем проект
git clone <repo_url> chatbot
cd chatbot

# 2. Запускаем PowerShell скрипт
.\deploy.ps1

# 3. Следуем инструкциям в скрипте
# Введите название организации и токен бота
```

### Что делает скрипт?

✅ Проверяет наличие Python 3  
✅ Создает виртуальное окружение (venv)  
✅ Устанавливает зависимости из requirements.txt  
✅ Создает файл .env с вашими данными  
✅ Инициализирует базу данных  
✅ Создает конфиги организации (organization.yaml, messages.yaml)  

---

## Подробное развертывание

### Шаг 1: Создание Telegram бота

1. Откройте Telegram и найдите **@BotFather**
2. Отправьте команду `/newbot`
3. Введите название бота (например: "Школа №1 - ИИ помощник")
4. Введите username бота (должен заканчиваться на `_bot`)
5. Получите **токен в формате**: `1234567890:ABCDEFGHIJKlmnopqrstuvwxyz`
6. (Опционально) Отправьте `/setdefault_administrator` для настройки админа

**⚠️ Важно**: Конфиdenциально храните токен! Не публикуйте его в GitHub.

### Шаг 2: Подготовка сервера

#### Linux / macOS

```bash
# Обновляем пакеты
sudo apt-get update && sudo apt-get upgrade  # Для Ubuntu/Debian
brew update                                  # Для macOS

# Устанавливаем Python 3.9+
sudo apt-get install python3-pip python3-venv  # Ubuntu/Debian
brew install python3                           # macOS

# Проверяем версию
python3 --version  # Должно быть 3.9+
```

#### Windows

1. Скачайте Python с https://www.python.org/downloads/
2. При установке **обязательно** отметьте `Add Python to PATH`
3. Откройте PowerShell и проверьте:

```powershell
python --version  # Должно быть 3.9+
```

### Шаг 3: Клонирование/распаковка проекта

#### Если у вас git:

```bash
git clone <repository_url> chatbot
cd chatbot
git checkout main  # или нужная ветка
```

#### Если архив:

```bash
unzip chatbot.zip
cd chatbot
```

### Шаг 4: Создание .env файла

```bash
# Linux / macOS
cp _env.example .env

# Windows
copy _env.example .env
```

Отредактируйте `.env`:

```env
# === ОБЯЗАТЕЛЬНО ===
BOT_TOKEN=1234567890:ABCDEFGHIJKlmnopqrstuvwxyz
ORGANIZATION_NAME=Школа №1

# === AI Провайдер (выберите один) ===
# Вариант 1: Ollama (локально, бесплатно)
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Вариант 2: Groq (облако, бесплатно)
# AI_PROVIDER=groq
# GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxx

# === Опционально ===
ORGANIZATION_DESCRIPTION=Образовательный центр
SUPPORT_CONTACT=@support_username
DB_PATH=data/bot.db
LOG_LEVEL=INFO
```

### Шаг 5: Виртуальное окружение и зависимости

```bash
# === Создание venv ===
python3 -m venv venv

# === Активация venv ===
# Linux / macOS:
source venv/bin/activate

# Windows:
.\venv\Scripts\Activate.ps1

# === Установка зависимостей ===
pip install -r requirements.txt

# Это займет 2-5 минут в зависимости от интернета
```

### Шаг 6: Инициализация организации

```bash
# Автоматическая инициализация
python init_organization.py --name "Школа №1" --token "1234567890:ABC..."

# Или интерактивно
python init_organization.py
```

Это создаст:
- ✓ Папки (data/, assets/, logs/)
- ✓ organization.yaml с конфигом вашей организации
- ✓ messages.yaml с текстами бота
- ✓ groups.yaml с группами (классами)
- ✓ Резервную копию БД

### Шаг 7: Проверка установки

```bash
# Проверяем, что всё установилось правильно
python -c "from telegram.ext import Application; print('✓ python-telegram-bot работает')"
python -c "import yaml; print('✓ PyYAML работает')"
python -c "from config import Config; print('✓ Config работает')"
```

---

## Настройка AI

### Вариант 1: Ollama (локально, бесплатно) ⭐ РЕКОМЕНДУЕТСЯ

**Плюсы**: Полная приватность, нет интернета, бесплатно
**Минусы**: Требует мощный компьютер (4+ ГБ ОЗУ)

#### Установка Ollama

1. Посетите https://ollama.ai
2. Скачайте и установите на свой компьютер
3. Откройте терминал и запустите:

```bash
ollama serve
# Должно вывести: "Listening on 127.0.0.1:11434"
```

4. В другом терминале загрузите модель:

```bash
ollama pull llama3.1
# или другая модель:
# ollama pull mistral
# ollama pull neural-chat
```

5. Проверьте в .env:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

### Вариант 2: Groq (облако, бесплатно)

**Плюсы**: Легко установить, очень быстро, бесплатно  
**Минусы**: Требует интернет, есть лимиты на запросы

#### Инструкция

1. Перейдите на https://console.groq.com
2. Зарегистрируйтесь (бесплатно)
3. Создайте API ключ в разделе "API Keys"
4. Скопируйте ключ (формат: `gsk_xxxxxxxxxx`)
5. Добавьте в .env:

```env
AI_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxx
```

6. Проверьте (ключ установлен правильно):

```bash
python -c "from modules.ai_tutor import AITutor; ai = AITutor(provider='groq'); print('✓ Groq подключен')"
```

### Вариант 3: Google Gemini (облако, бесплатно)

1. Перейдите на https://aistudio.google.com
2. Нажмите "Get API key"
3. Создайте ключ (бесплатно, без карты)
4. Добавьте в .env:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy_xxxxxxxxxx
```

### Вариант 4: OpenAI (облако, платно)

1. Перейдите на https://platform.openai.com
2. Создайте аккаунт и добавьте платежный способ
3. Создайте API ключ в разделе "API Keys"
4. Добавьте в .env:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
```

### Резервный провайдер (опционально)

Если основной AI недоступен, бот будет использовать резервный:

```env
AI_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxx
FALLBACK_AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy_xxxxx
```

---

## Загрузка данных

### Структура Excel файлов

Создайте два Excel файла:

#### 1. Учащиеся (students.xlsx)

| ID  | ФИ            | Группа | Telegram ID |
|-----|---------------|--------|-------------|
| 1   | Иван Петров   | 1A     | 123456789   |
| 2   | Мария Сидорова| 1A     | 987654321   |
| 3   | Петр Иванов   | 1B     | 555555555   |

#### 2. Расписание (schedule.xlsx)

| Дата       | Время  | Группа | Предмет     | Кабинет |
|------------|--------|--------|-------------|---------|
| 2024-01-15 | 09:00  | 1A     | Математика  | 101     |
| 2024-01-15 | 10:00  | 1A     | Русский язык| 102     |
| 2024-01-15 | 09:00  | 1B     | История     | 201     |

### Загрузка через администраторское приложение

```bash
# Запустить админ-приложение
python admin_loader.py

# Откроется GUI интерфейс
# 1. Выберите файл students.xlsx
# 2. Нажмите "Load Students"
# 3. Выберите файл schedule.xlsx
# 4. Нажмите "Load Schedule"
```

### Загрузка через командную строку

```bash
python admin_loader.py --file students.xlsx --type students
python admin_loader.py --file schedule.xlsx --type schedule
```

---

## Первый запуск

### Запуск бота

```bash
# Убедитесь, что venv активирован
# Linux / macOS:
source venv/bin/activate

# Windows:
.\venv\Scripts\Activate.ps1

# Запустите бота
python bot.py

# Должны увидеть:
# "Bot started successfully"
# "Listening for messages..."
```

### Тестирование в Telegram

1. Откройте Telegram
2. Найдите вашего бота по username
3. Нажмите "Start"
4. Должны увидеть приветствие:

```
Привет, [Ваше имя]! 👋

Добро пожаловать в Школа №1! Я ваш AI-ассистент.

Я могу помочь тебе:
• 📚 Учиться с помощью контекстного AI-репетитора
• 📅 Планировать свои занятия
• 📖 Использовать справочник знаний

Используй /help для списка команд.
```

5. Попробуйте команды:

```
/help          — список команд
/status        — информация о пользователе
/today         — расписание на сегодня
/schedule      — расписание на неделю
```

6. Напишите вопрос AI:

```
Как решить квадратное уравнение?
```

Бот должен ответить через ИИ.

---

## Администрирование

### Структура файлов

```
chatbot/
├── bot.py              — основной скрипт бота
├── config.py           — конфигурация (с поддержкой YAML)
├── database.py         — работа с БД
├── handlers.py         — обработчики команд
├── admin_loader.py     — загрузка данных (GUI)
├── admin_loader_excel.py — загрузка Excel файлов
│
├── organization.yaml   — конфиг организации (TASK 3.1)
├── messages.yaml       — тексты бота (TASK 3.3)
├── groups.yaml         — список групп (TASK 3.2)
│
├── data/               — данные организации
│   ├── bot.db          — основная БД
│   ├── analytics.db    — аналитика (опционально)
│   ├── backups/        — резервные копии
│   └── logs/           — логи действий
│
├── modules/            — модули бота
│   ├── ai_tutor.py    — ИИ-репетитор
│   ├── planner.py     — планировщик расписания
│   └── reference.py   — справочник знаний
│
└── assets/             — медиафайлы
    └── logo.png        — логотип организации
```

### Настройка конфигов

#### organization.yaml

```yaml
organization:
  name: "Школа №1"
  description: "Образовательное учреждение"
  support_contact: "@support_username"
  logo_path: "assets/logo.png"

groups:
  default:
    - "1A"
    - "1B"
    - "2A"
    # ...
```

#### messages.yaml

```yaml
main:
  welcome: "Привет, {first_name}! Добро пожаловать в {organization_name}!"
  help: "Доступные команды {organization_name}: ..."
```

#### .env

Все переменные окружения в одном файле.

### Резервное копирование

```bash
# Автоматическое резервное копирование при запуске
python bot.py
# Создаст: data/backups/bot_backup_YYYY-MM-DD_HH-MM-SS.db

# Ручное создание резервной копии
python -c "from database import Database; import asyncio; db = Database(); asyncio.run(db.backup())"
```

### Просмотр логов

```bash
# Все логи в файле (если LOG_LEVEL=INFO)
tail -f data/logs/bot.log

# Или в консоли при запуске
python bot.py  # Выводит логи в консоль
```

---

## Решение проблем

### 💥 Ошибка: "BOT_TOKEN не установлен"

```
ValueError: BOT_TOKEN не установлен в переменных окружения
```

**Решение**:
- Проверьте, что файл `.env` существует
- Проверьте, что BOT_TOKEN заполнен (не пустой)
- Перезапустите скрипт

```bash
grep BOT_TOKEN .env  # Должно вывести: BOT_TOKEN=1234567890:ABC...
```

### 💥 Ошибка: "ModuleNotFoundError: No module named 'telegram'"

```
ModuleNotFoundError: No module named 'telegram'
```

**Решение**: Не установлены зависимости или venv не активирован

```bash
# Активируйте venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows

# Установите зависимости
pip install -r requirements.txt
```

### 💥 AI-репетитор не отвечает

**Для Ollama**:
```bash
# Проверьте, что Ollama запущен
curl http://localhost:11434/api/tags  # Должно вернуть список моделей

# Если не работает, перезапустите Ollama
ollama serve

# Убедитесь, что модель загружена
ollama list  # Должна показать llama3.1 (или вашу модель)
```

**Для Groq/Gemini**:
```bash
# Проверьте API ключ в .env
grep GROQ_API_KEY .env  # Не должно быть пустым

# Тестируйте ключ
python -c "from modules.ai_tutor import AITutor; ai = AITutor(provider='groq'); print(ai.initialized)"
```

### 💥 Ошибка: "Address already in use"

```
OSError: [Errno 48] Address already in use
```

**Решение**: Другой процесс использует порт 11434 (для Ollama)

```bash
# Найдите процесс
lsof -i :11434  # Linux/macOS
netstat -ano | findstr :11434  # Windows

# Остановите его
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Перезапустите
ollama serve
```

### 💥 Бот не получает сообщения

**Причины**:
1. BOT_TOKEN неправильный
2. Бот не запущен (`python bot.py`)
3. Сервер заблокирован брандмауэром (для вебхуков)

**Решение**:
```bash
# Проверьте токен в Telegram через @BotFather
# Перезапустите бота
python bot.py

# Проверьте в логах
tail -f data/logs/bot.log
```

---

## FAQ

### ❓ Можно ли использовать один бот для нескольких организаций?

**Ответ**: Нет, каждая организация = отдельный бот со своим токеном, БД и конфигами. Это сделано для:
- 🔒 Безопасности (разделение данных)
- 🎯 Кастомизации (свой брендинг, логика)
- 📊 Аналитики (отдельная статистика)

Если нужна одна система для многих организаций — обратитесь к разработчиком для мульти-тенанта архитектуры.

### ❓ Сколько учащихся может вмещать бот?

**Ответ**: Теоретически — неограниченно (SQLite может работать с миллионами записей). На практике:
- ✅ До 10,000 учащихся — нет проблем
- ⚠️ 10,000–100,000 — нужна оптимизация БД и индексы
- ❌ Свыше 100,000 — рекомендуется PostgreSQL вместо SQLite

### ❓ Как обновить версию бота?

**Ответ**:
```bash
# 1. Создайте резервную копию БД
cp data/bot.db data/backups/bot_backup_before_update.db

# 2. Загрузите свежую версию
git pull origin main

# 3. Обновите зависимости
pip install -r requirements.txt --upgrade

# 4. Перезапустите бота
python bot.py
```

### ❓ Как удалить бота или сбросить данные?

**Ответ**:
```bash
# ⚠️ Осторожно! Это удалит все данные

# Удалить БД
rm data/bot.db

# Пересоздать пустую БД
python -c "from database import Database; import asyncio; db = Database(); asyncio.run(db.init_db())"

# Или удалить всю папку data
rm -rf data/
mkdir -p data/backups data/logs
```

### ❓ Как сделать бота доступным 24/7?

**Ответ**: Запустите бота на сервере (не на локальном компьютере):

**Вариант 1: Облачные платформы** (рекомендуется)
- Heroku (простой, но медленный)
- PythonAnywhere
- Replit
- DigitalOcean
- AWS/GCP/Azure

**Вариант 2: VPS сервер**
```bash
# На VPS сервере
git clone <repo_url>
cd chatbot
./deploy.sh
python bot.py  # запустить в фоне через tmux/screen
```

**Вариант 3: Docker**
```bash
docker build -t chatbot .
docker run -d chatbot python bot.py
```

### ❓ Как настроить SSL сертификат для вебхуков?

**Ответ**: По умолчанию бот использует polling (проверка сообщений), не требующий SSL. Для вебхуков (перехвата) нужен SSL — следуйте инструкциям в `QUICK_START_NEW.md`.

### ❓ Как добавить свою команду в бота?

**Ответ**: Отредактируйте [handlers.py](handlers.py):

```python
# В функции register_handlers()
app.add_handler(CommandHandler('mycmd', handler_my_command))

async def handler_my_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Моя команда"""
    await update.message.reply_text("Привет от моей команды!")
```

### ❓ Поддерживается ли работа с группами в Telegram?

**Ответ**: Нет, пока бот работает только с личными сообщениями (DM). Поддержка групп планируется в будущих версиях.

---

## Контакты и поддержка

📚 **Документация**: [README.md](README.md)  
🐛 **Баг-репорты**: GitHub Issues  
💬 **Вопросы**: Обратитесь в SUPPORT_CONTACT из .env  
🚀 **Новые идеи**: GitHub Discussions  

---

## История версий

### v1.0 (2024)
- ✅ Первая версия бота
- ✅ Поддержка YAML конфигов (TASK 3.1-3.3)
- ✅ Скрипты развертывания (TASK 3.5)
- ✅ Полная документация (TASK 3.6)

---

**Документ актуален на April 16, 2026**

Последнее обновление: DEPLOYMENT.md
