# deploy.ps1 — скрипт развертывания бота для Windows
# TASK 3.5: Автоматическое развертывание под новую организацию
# Использование: .\deploy.ps1 (запустить PowerShell как администратор)

# === Проверка выполнения скриптов ===
if ((Get-ExecutionPolicy) -eq "Restricted") {
    Write-Host "Для запуска скрипта нужны права. Выполняем Set-ExecutionPolicy..." -ForegroundColor Yellow
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
}

# === Функции для вывода ===
function Write-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "========================================`n" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

# === Шаг 1: Предварительные проверки ===
Write-Header "🚀 РАЗВЕРТЫВАНИЕ CHATBOT"

Write-Info "Проверка предварительных условий..."

# Проверка Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "Python не установлен"
    Write-Host "Установите Python 3.9+ с https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}
Write-Success "Python найден"

# Проверка bot.py
if (-not (Test-Path "bot.py")) {
    Write-Error-Custom "bot.py не найден в текущей директории"
    Write-Host "Убедитесь, что вы находитесь в корневой папке проекта" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}
Write-Success "Проект найден"

# === Шаг 2: Получить информацию от пользователя ===
Write-Header "📝 ИНФОРМАЦИЯ ОБ ОРГАНИЗАЦИИ"

$ORG_NAME = Read-Host "Введите название организации (например, 'Школа No1')"

if ([string]::IsNullOrWhiteSpace($ORG_NAME)) {
    Write-Error-Custom "Название не может быть пустым"
    exit 1
}

Write-Info "Организация: $ORG_NAME"

$BOT_TOKEN = Read-Host "Введите токен Telegram бота (от @BotFather)"

if ([string]::IsNullOrWhiteSpace($BOT_TOKEN)) {
    Write-Error-Custom "Токен не может быть пустым"
    exit 1
}

Write-Success "Токен получен"

# === Шаг 3: Создание виртуального окружения ===
Write-Header "🐍 ВИРТУАЛЬНОЕ ОКРУЖЕНИЕ"

if (-not (Test-Path "venv")) {
    Write-Info "Создание виртуального окружения (это может занять минуту)..."
    python -m venv venv
    Write-Success "Виртуальное окружение создано"
} else {
    Write-Info "Виртуальное окружение уже существует"
}

# Активация venv
& ".\venv\Scripts\Activate.ps1"
Write-Success "Виртуальное окружение активировано"

# === Шаг 4: Установка зависимостей ===
Write-Header "📦 УСТАНОВКА ЗАВИСИМОСТЕЙ"

Write-Info "Обновление pip..."
python -m pip install --upgrade pip | Out-Null
Write-Success "Pip обновлён"

Write-Info "Установка зависимостей (это может занять пару минут)..."
pip install -r requirements.txt

Write-Success "Зависимости установлены"

# === Шаг 5: Создание .env файла ===
Write-Header "⚙️ КОНФИГУРАЦИЯ"

if (-not (Test-Path ".env")) {
    Write-Info "Создание файла .env..."
    
    if (Test-Path "_env.example") {
        Copy-Item "_env.example" ".env"
        
        # Обновляем значения (простой способ для Windows)
        $envContent = Get-Content ".env" -Raw
        $envContent = $envContent -replace 'BOT_TOKEN=.*', "BOT_TOKEN=$BOT_TOKEN"
        $envContent = $envContent -replace 'ORGANIZATION_NAME=.*', "ORGANIZATION_NAME=$ORG_NAME"
        Set-Content ".env" $envContent
    } else {
        # Создаём с нуля
        @"
BOT_TOKEN=$BOT_TOKEN
ORGANIZATION_NAME=$ORG_NAME
ORGANIZATION_DESCRIPTION=Образовательное учреждение
SUPPORT_CONTACT=@support
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
DB_PATH=data/bot.db
LOG_LEVEL=INFO
"@ | Set-Content ".env"
    }
    
    Write-Success "Файл .env создан"
} else {
    Write-Warning-Custom ".env файл уже существует"
    $updateEnv = Read-Host "Обновить значения? (y/n)"
    
    if ($updateEnv -eq 'y') {
        $envContent = Get-Content ".env" -Raw
        $envContent = $envContent -replace 'BOT_TOKEN=.*', "BOT_TOKEN=$BOT_TOKEN"
        $envContent = $envContent -replace 'ORGANIZATION_NAME=.*', "ORGANIZATION_NAME=$ORG_NAME"
        Set-Content ".env" $envContent
        Write-Success "Значения .env обновлены"
    }
}

# === Шаг 6: Инициализация организации ===
Write-Header "🏢 ИНИЦИАЛИЗАЦИЯ ОРГАНИЗАЦИИ"

if (Test-Path "init_organization.py") {
    Write-Info "Запуск инициализации организации..."
    python init_organization.py --name "$ORG_NAME" --token "$BOT_TOKEN"
} else {
    Write-Warning-Custom "Файл инициализации не найден"
}

# === Шаг 7: Инициализация БД ===
Write-Header "🗄️ БАЗА ДАННЫХ"

Write-Info "Инициализация базы данных..."
python -c @"
import asyncio
from database import Database

async def init():
    db = Database()
    await db.init_db()
    print('DB initialized')

try:
    asyncio.run(init())
except Exception as e:
    print(f'Warning: {e}')
"@ 2>&1 | Out-Null

Write-Success "База данных инициализирована"

# === Финальное сообщение ===
Write-Header "✅ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО"

Write-Host ""
Write-Info "Организация '$ORG_NAME' успешно развёрнута!"
Write-Host ""
Write-Host "📋 СЛЕДУЮЩИЕ ШАГИ:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 📝 ОТРЕДАКТИРУЙТЕ КОНФИГИ:"
Write-Host "   - .env: добавьте API ключи, если используете Groq/Gemini/OpenAI"
Write-Host "   - organization.yaml: настройте контакт поддержки и другие параметры"
Write-Host ""
Write-Host "2. 🤖 ВЫБЕРИТЕ AI ПРОВАЙДЕР (в файле .env):"
Write-Host "   - OLLAMA (локально): требует установки ollama.ai"
Write-Host "   - GROQ (бесплатно): требует GROQ_API_KEY"
Write-Host "   - GEMINI (бесплатно): требует GEMINI_API_KEY"
Write-Host ""
Write-Host "3. 📥 ЗАГРУЗИТЕ ДАННЫЕ:"
Write-Host "   - python admin_loader.py    # Запуск админ-интерфейса"
Write-Host ""
Write-Host "4. 🚀 ЗАПУСТИТЕ БОТА:"
Write-Host "   - python bot.py"
Write-Host ""
Write-Host "📚 ПОЛНАЯ ДОКУМЕНТАЦИЯ: DEPLOYMENT.md" -ForegroundColor Yellow
Write-Host "💬 ПОДДЕРЖКА: обратитесь к администратору проекта" -ForegroundColor Yellow
Write-Host ""
Write-Success "Бот готов к запуску!"

Write-Host ""
Read-Host "Нажмите Enter для завершения"
