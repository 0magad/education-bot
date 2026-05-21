# Быстрая настройка Cloudflare Tunnel для Ollama

Это самый простой и безопасный способ подключиться к Ollama из любого места через интернет.

## Что это дает?

- ✅ Бесплатно
- ✅ Автоматическое HTTPS (безопасное соединение)
- ✅ Работает из любого места (даже из другого города)
- ✅ Не нужно настраивать роутер или файрвол
- ✅ Не нужно знать внешний IP адрес

## Шаг 1: Установка Cloudflare Tunnel на компьютере

### Windows:

1. Скачайте `cloudflared.exe` с официального сайта:
   https://github.com/cloudflare/cloudflared/releases/latest
   
2. Распакуйте в папку (например, `C:\cloudflared\`)

3. Откройте PowerShell в этой папке и запустите:
   ```powershell
   .\cloudflared.exe tunnel --url http://localhost:11434
   ```

### Linux:

```bash
# Скачайте и установите
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# Запустите туннель
cloudflared tunnel --url http://localhost:11434
```

### Mac:

```bash
brew install cloudflared
cloudflared tunnel --url http://localhost:11434
```

## Шаг 2: Получите URL

После запуска команды вы увидите что-то вроде:

```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
|  https://xxxxx-xxxxx-xxxxx.trycloudflare.com                                              |
+--------------------------------------------------------------------------------------------+
```

**Скопируйте этот URL!** Это ваш публичный адрес для Ollama.

## Шаг 3: Настройте бота на ноутбуке

В файле `.env` на ноутбуке укажите полученный URL:

```env
OLLAMA_BASE_URL=https://xxxxx-xxxxx-xxxxx.trycloudflare.com
OLLAMA_MODEL=llama3.1
AI_PROVIDER=ollama
```

**Важно:** Используйте `https://` (не `http://`)!

## Шаг 4: Запуск

1. **На компьютере:** 
   - Убедитесь, что Ollama запущен: `ollama serve`
   - Запустите Cloudflare Tunnel (команда из шага 1)
   - **Не закрывайте окно с туннелем!** Оно должно работать пока вы используете бота

2. **На ноутбуке:**
   - Запустите бота: `python bot.py`
   - Бот подключится к Ollama через туннель

## Автозапуск (опционально)

Чтобы туннель запускался автоматически при включении компьютера:

### Windows:

1. Создайте файл `start-tunnel.bat`:
   ```batch
   @echo off
   cd C:\cloudflared
   cloudflared.exe tunnel --url http://localhost:11434
   ```

2. Добавьте его в автозагрузку Windows

### Linux (systemd):

Создайте файл `/etc/systemd/system/cloudflared-tunnel.service`:

```ini
[Unit]
Description=Cloudflare Tunnel for Ollama
After=network.target

[Service]
Type=simple
User=ваш_пользователь
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:11434
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl enable cloudflared-tunnel
sudo systemctl start cloudflared-tunnel
```

## Важные замечания

1. **URL меняется при каждом запуске** (если используете бесплатный режим)
   - Решение: Используйте именованный туннель (требует регистрации в Cloudflare)

2. **Туннель должен работать постоянно** пока вы используете бота
   - Если закрыть окно с туннелем, подключение прервется

3. **Безопасность:**
   - URL содержит случайные символы - его сложно угадать
   - Трафик шифруется через HTTPS
   - Но все равно не публикуйте URL публично!

## Альтернатива: Постоянный туннель

Если нужен постоянный URL (не меняется при перезапуске):

1. Зарегистрируйтесь на cloudflare.com (бесплатно)
2. Создайте именованный туннель через веб-интерфейс
3. Используйте постоянный домен

Подробнее: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
