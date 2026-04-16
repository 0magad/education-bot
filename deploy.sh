#!/bin/bash

# deploy.sh — скрипт развертывания бота для новой организации
# TASK 3.5: Автоматическое развертывание под новую организацию
# Использование: chmod +x deploy.sh && ./deploy.sh

set -e  # Выход при первой ошибке

# Кросс-платформенный sed (macOS требует '' после -i, Linux — нет)
sed_inplace() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# === Шаг 1: Предварительные проверки ===
print_header "🚀 РАЗВЕРТЫВАНИЕ CHATBOT"

print_info "Проверка предварительных условий..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 не установлен"
    echo "Установите Python 3.9 или выше: https://www.python.org/downloads/"
    exit 1
fi
print_success "Python 3 найден"

# Проверка git (опционально)
if ! command -v git &> /dev/null; then
    print_warning "Git не установлен (опционально)"
else
    print_success "Git найден"
fi

# Проверка текущей директории
if [ ! -f "bot.py" ]; then
    print_error "bot.py не найден в текущей директории"
    echo "Убедитесь, что вы находитесь в корневой папке проекта"
    exit 1
fi
print_success "Проект найден"

# === Шаг 2: Получить информацию от пользователя ===
print_header "📝 ИНФОРМАЦИЯ ОБ ОРГАНИЗАЦИИ"

read -p "Введите название организации (например, 'Школа №1'): " ORG_NAME

if [ -z "$ORG_NAME" ]; then
    print_error "Название не может быть пустым"
    exit 1
fi

print_info "Организация: $ORG_NAME"

read -p "Введите токен Telegram бота (от @BotFather): " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    print_error "Токен не может быть пустым"
    exit 1
fi

if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
    print_warning "Токен имеет необычный формат, но продолжаем"
fi

print_success "Токен получен"

# === Шаг 3: Создание виртуального окружения ===
print_header "🐍 ВИРТУАЛЬНОЕ ОКРУЖЕНИЕ"

if [ ! -d "venv" ]; then
    print_info "Создание виртуального окружения..."
    python3 -m venv venv
    print_success "Виртуальное окружение создано"
else
    print_info "Виртуальное окружение уже существует"
fi

# Активация venv
source venv/bin/activate
print_success "Виртуальное окружение активировано"

# === Шаг 4: Установка зависимостей ===
print_header "📦 УСТАНОВКА ЗАВИСИМОСТЕЙ"

print_info "Обновление pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "Pip обновлён"

print_info "Установка зависимостей (это может занять несколько минут)..."
pip install -r requirements.txt

print_success "Зависимости установлены"

# === Шаг 5: Создание .env файла ===
print_header "⚙️ КОНФИГУРАЦИЯ"

if [ ! -f ".env" ]; then
    print_info "Создание файла .env..."
    
    # Копируем шаблон
    if [ -f "_env.example" ]; then
        cp _env.example .env
        sed_inplace "s/BOT_TOKEN=.*/BOT_TOKEN=$BOT_TOKEN/" .env
        sed_inplace "s/ORGANIZATION_NAME=.*/ORGANIZATION_NAME=$ORG_NAME/" .env
    else
        # Создаём с нуля
        cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ORGANIZATION_NAME=$ORG_NAME
ORGANIZATION_DESCRIPTION=Образовательное учреждение
SUPPORT_CONTACT=@support
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
DB_PATH=data/bot.db
LOG_LEVEL=INFO
EOF
    fi
    
    print_success "Файл .env создан"
else
    print_warning ".env файл уже существует"
    read -p "Обновить значения? (y/n): " UPDATE_ENV
    
    if [ "$UPDATE_ENV" = "y" ]; then
        sed_inplace "s/BOT_TOKEN=.*/BOT_TOKEN=$BOT_TOKEN/" .env
        sed_inplace "s/ORGANIZATION_NAME=.*/ORGANIZATION_NAME=$ORG_NAME/" .env
        print_success "Значения .env обновлены"
    fi
fi

# === Шаг 6: Инициализация организации ===
print_header "🏢 ИНИЦИАЛИЗАЦИЯ ОРГАНИЗАЦИИ"

if command -v python3 &> /dev/null && [ -f "init_organization.py" ]; then
    print_info "Запуск инициализации организации..."
    python3 init_organization.py --name "$ORG_NAME" --token "$BOT_TOKEN"
else
    print_warning "Инициализацию организации нужно провести вручную"
fi

# === Шаг 7: Инициализация БД ===
print_header "🗄️ БАЗОВАЯ ДАННЫХ"

print_info "Инициализация базы данных..."
python3 -c "
import asyncio
from database import Database

async def init():
    db = Database()
    await db.init_db()
    print('✓ БД инициализирована')

asyncio.run(init())
" || print_warning "Инициализация БД может требовать дополнительной настройки"

# === Показ финального сообщения ===
print_header "✅ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО"

echo ""
print_info "Организация '$ORG_NAME' успешно развёрнута!"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. 📝 ОТРЕДАКТИРУЙТЕ КОНФИГИ:"
echo "   - .env: добавьте API ключи, если используете Groq/Gemini/OpenAI"
echo "   - organization.yaml: настройте контакт поддержки и другие параметры"
echo ""
echo "2. 🤖 ВЫБЕРИТЕ AI ПРОВАЙДЕР (в файле .env):"
echo "   - OLLAMA (локально): требует установки ollama.ai"
echo "   - GROQ (бесплатно): требует GROQ_API_KEY"
echo "   - GEMINI (бесплатно): требует GEMINI_API_KEY"
echo ""
echo "3. 📥 ЗАГРУЗИТЕ ДАННЫЕ (в админ-приложении):"
echo "   - python admin_loader.py    # Запуск админ-интерфейса"
echo ""
echo "4. 🚀 ЗАПУСТИТЕ БОТА:"
echo "   - python bot.py"
echo ""
echo "📚 ПОЛНАЯ ДОКУМЕНТАЦИЯ: DEPLOYMENT.md"
echo "💬 ПОДДЕРЖКА: обратитесь к администратору проекта"
echo ""
print_success "Бот готов к запуску!"
