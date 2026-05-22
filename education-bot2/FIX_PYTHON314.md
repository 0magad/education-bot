# Исправление проблемы с Python 3.14

## Проблема

При использовании Python 3.14 возникает ошибка:
```
AttributeError: 'Updater' object has no attribute '_Updater__polling_cleanup_cb'
```

## Решение

1. **Обновите библиотеку python-telegram-bot до версии 21.0+:**

```bash
pip install --upgrade python-telegram-bot>=21.0
```

2. **Переустановите все зависимости:**

```bash
pip install -r requirements.txt --upgrade
```

## Альтернативное решение

Если проблема сохраняется, можно использовать Python 3.11 или 3.12, которые полностью совместимы с библиотекой:

```bash
# Установка Python 3.12 (рекомендуется)
# Скачайте с python.org и установите

# Затем создайте виртуальное окружение:
python3.12 -m venv venv

# Активируйте его:
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости:
pip install -r requirements.txt
```

## Проверка версии

Убедитесь, что используется правильная версия:

```bash
python --version
pip show python-telegram-bot
```

Должно быть:
- Python: 3.8-3.13 (или 3.14 с обновленной библиотекой)
- python-telegram-bot: >= 21.0






