@echo off
title Education Bot — Установка
echo === Education Bot — Установка ===

python --version >nul 2>&1
if errorlevel 1 ( echo ОШИБКА: Python не найден. & pause & exit /b 1 )
echo Python найден — OK

if not exist ".venv" ( python -m venv .venv & echo Виртуальное окружение создано. )
call .venv\Scripts\activate.bat

pip install --upgrade pip -q
pip install -r requirements.txt -q
echo Зависимости установлены.

if not exist ".env" ( copy .env.example .env & echo .env создан. )

set /p BOT_TOKEN="Введите BOT_TOKEN: "
set /p ORG_NAME="Введите ORGANIZATION_NAME: "
set /p SUPPORT="Введите SUPPORT_CONTACT: "

echo BOT_TOKEN=%BOT_TOKEN%>> .env
echo ORGANIZATION_NAME=%ORG_NAME%>> .env
echo SUPPORT_CONTACT=%SUPPORT%>> .env
echo .env обновлён.

if not exist "data" mkdir data
python -c "import asyncio,sys;sys.path.insert(0,'.');from database import Database;from config import Config;asyncio.run(Database(db_path=Config.DB_PATH).init_db())"
echo БД инициализирована.

echo.
echo === Установка завершена! ===
echo Следующие шаги:
echo   .venv\Scripts\activate.bat
echo   python bot.py
pause
