# Быстрый старт с бесплатным AI-репетитором

## ⚡ За 2 минуты

### Шаг 1: Установите зависимости
```bash
pip install -r requirements.txt
```

### Шаг 2: Получите бесплатный API ключ Groq

1. Откройте [console.groq.com](https://console.groq.com/)
2. Войдите через Google/GitHub
3. Перейдите в [API Keys](https://console.groq.com/keys)
4. Нажмите "Create API Key"
5. Скопируйте ключ (начинается с `gsk_`)

### Шаг 3: Добавьте в `.env`

```env
AI_PROVIDER=groq
GROQ_API_KEY=gsk_ваш_ключ_здесь
```

### Шаг 4: Запустите бота

```bash
python bot.py
```

Готово! 🎉 AI-репетитор работает **бесплатно**!

## Альтернатива: Google Gemini

Если хотите использовать Gemini вместо Groq:

1. Получите ключ на [aistudio.google.com](https://aistudio.google.com/app/apikey)
2. Добавьте в `.env`:
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=ваш_ключ
   ```

## Проверка

Отправьте боту:
- "Что такое фотосинтез?"
- "Реши пример: 25 * 4 + 10"

Бот ответит используя бесплатную модель! 🚀

## Подробности

Полная инструкция: [FREE_AI_SETUP.md](FREE_AI_SETUP.md)
