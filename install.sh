#!/usr/bin/env bash
# scripts/install.sh — установщик для Linux/macOS
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
echo -e "${YELLOW}=== Education Bot — Установка ===${NC}"

# 1. Проверка Python >= 3.10
PY=$(command -v python3 || command -v python)
[ -z "$PY" ] && { echo -e "${RED}Python не найден. Установите Python 3.10+${NC}"; exit 1; }
PY_VER=$($PY -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR=$(echo "$PY_VER" | cut -d. -f1); MINOR=$(echo "$PY_VER" | cut -d. -f2)
([ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ])) && {
    echo -e "${RED}Требуется Python 3.10+ (найден $PY_VER)${NC}"; exit 1; }
echo -e "${GREEN}Python $PY_VER — OK${NC}"

# 2. Виртуальное окружение
[ ! -d ".venv" ] && $PY -m venv .venv && echo "Виртуальное окружение создано."
source .venv/bin/activate

# 3. Зависимости
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}Зависимости установлены.${NC}"

# 4. .env
[ ! -f ".env" ] && cp .env.example .env && echo ".env создан из .env.example"

# 5. Интерактивные вопросы
echo ""
read -rp "Введите BOT_TOKEN: " BOT_TOKEN
read -rp "Введите ORGANIZATION_NAME: " ORG_NAME
read -rp "Введите SUPPORT_CONTACT (@username или email): " SUPPORT

set_env() {
    K=$1; V=$2
    grep -q "^${K}=" .env 2>/dev/null \
        && sed -i.bak "s|^${K}=.*|${K}=${V}|" .env \
        || echo "${K}=${V}" >> .env
}
set_env "BOT_TOKEN" "$BOT_TOKEN"
set_env "ORGANIZATION_NAME" "$ORG_NAME"
set_env "SUPPORT_CONTACT" "$SUPPORT"
echo -e "${GREEN}.env обновлён.${NC}"

# 6. Инициализация БД
mkdir -p data
$PY -c "
import asyncio, sys
sys.path.insert(0, '.')
from database import Database
from config import Config
async def init():
    db = Database(db_path=Config.DB_PATH)
    await db.init_db()
asyncio.run(init())
" && echo -e "${GREEN}БД инициализирована.${NC}" || echo -e "${YELLOW}БД init пропущен.${NC}"

echo ""
echo -e "${GREEN}=== Установка завершена! ===${NC}"
echo "Следующие шаги:"
echo "  source .venv/bin/activate"
echo "  python bot.py"
