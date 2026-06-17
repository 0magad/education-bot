# scripts/install.ps1 — установщик для Windows PowerShell
$ErrorActionPreference = "Stop"
Write-Host "=== Education Bot — Установка ===" -ForegroundColor Yellow

# 1. Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Error "Python не найден. Установите Python 3.10+."; exit 1 }
$ver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$maj, $min = $ver -split '\.' | ForEach-Object { [int]$_ }
if ($maj -lt 3 -or ($maj -eq 3 -and $min -lt 10)) { Write-Error "Требуется Python 3.10+ (найден $ver)"; exit 1 }
Write-Host "Python $ver — OK" -ForegroundColor Green

# 2. Виртуальное окружение
if (-not (Test-Path ".venv")) { python -m venv .venv; Write-Host "Виртуальное окружение создано." }
& .\.venv\Scripts\Activate.ps1

# 3. Зависимости
pip install --upgrade pip -q
pip install -r requirements.txt -q
Write-Host "Зависимости установлены." -ForegroundColor Green

# 4. .env
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host ".env создан." }

# 5. Интерактивные вопросы
$BOT_TOKEN = Read-Host "Введите BOT_TOKEN"
$ORG_NAME  = Read-Host "Введите ORGANIZATION_NAME"
$SUPPORT   = Read-Host "Введите SUPPORT_CONTACT (@username или email)"

function Set-EnvValue($key, $value) {
    $content = Get-Content ".env"
    if ($content -match "^$key=") { $content = $content -replace "^$key=.*", "$key=$value" }
    else { $content += "$key=$value" }
    Set-Content ".env" $content
}
Set-EnvValue "BOT_TOKEN"         $BOT_TOKEN
Set-EnvValue "ORGANIZATION_NAME" $ORG_NAME
Set-EnvValue "SUPPORT_CONTACT"   $SUPPORT
Write-Host ".env обновлён." -ForegroundColor Green

# 6. Init DB
New-Item -ItemType Directory -Force -Path "data" | Out-Null
python -c "import asyncio,sys;sys.path.insert(0,'.');from database import Database;from config import Config;asyncio.run(Database(db_path=Config.DB_PATH).init_db())"
Write-Host "БД инициализирована." -ForegroundColor Green

Write-Host "`n=== Установка завершена! ===" -ForegroundColor Green
Write-Host "Следующие шаги:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python bot.py"
