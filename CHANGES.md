# Журнал изменений проекта

Документ описывает все изменения, внесённые в проект в рамках реализации Фазы 3
(мультитенантное развёртывание) и улучшений 5.2–5.4.

---

## `config.py`

### Исправление `get_groups_list()`

**Проблема.** Метод возвращал пустую переменную вместо списка групп из `groups.yaml`.

**Исправление.** Добавлена корректная итерация иерархии `groups.yaml`:

```python
groups_config = cls.load_groups_config()
if groups_config:
    result = []
    for category in groups_config.get('groups', {}).values():
        if isinstance(category, dict) and 'items' in category:
            result.extend([item['name'] for item in category.get('items', [])])
    if result:
        return result
```

---

## `organization.yaml`

### Группы и специализации

- Раздел `groups.default` — заменены школьные классы (`1А`, `1Б`…) на реальные названия курсов:
  `VR/AR приложения`, `3D моделирование`, `Веб-разработка`, `Программирование на Python`,
  `Робототехника`, `Графический дизайн`, `Мобильная разработка`, `Кибербезопасность`,
  `Искусственный интеллект`, `Разработка игр`.
- Добавлен `features.tutor.specialization` — список из 10 тем, соответствующих названиям курсов.
  Используется AI-репетитором для формирования системного промпта.

### Новые параметры надёжности

```yaml
features:
  tutor:
    ollama_retries: 2
    ollama_retry_delay: 3
```

### Включённые функции

```yaml
features:
  quick_questions:
    enabled: true
  answer_rating:
    enabled: true
```

---

## `messages.yaml`

Добавлены пять ключей в раздел `tutor:`:

| Ключ | Назначение |
|---|---|
| `quick_explain_prompt` | Запрос темы при нажатии «Объясни тему» |
| `quick_example_prompt` | Запрос темы при нажатии «Дай пример» |
| `quick_check_prompt` | Запрос задачи при нажатии «Проверь решение» |
| `rating_understood` | Ответ бота при оценке «Понял» |
| `rating_not_understood` | Ответ бота при оценке «Не понял» |

---

## `handlers.py`

Файл переписан полностью. Ключевые изменения:

### Вспомогательные функции

```python
def _get_features() -> dict
```
Загружает раздел `features` из `organization.yaml` с перехватом исключений.

```python
def _build_response_keyboard(quick_q_enabled: bool, rating_enabled: bool) -> InlineKeyboardMarkup | None
```
Строит двухрядную клавиатуру:
- Ряд 1 (если `quick_q_enabled`): «Объясни тему», «Дай пример», «Проверь решение»
- Ряд 2 (если `rating_enabled`): «Понял», «Не понял»

### Устранение хардкода строк

Все пять командных обработчиков (`start`, `help`, `class`, `status`, `schedule`, `today`)
переведены на `Config.get_message(key, **kwargs)`. Ни одной строки на русском языке в коде не осталось.

### `handle_message`

- Читает `qq_prefix` из `context.user_data` и при наличии подставляет его перед сообщением пользователя.
- Загружает историю диалога через `db.get_conversation_history()`.
- Вводит флаг `ai_success = False`; переводится в `True` только при успешном ответе AI.
- Клавиатура `reply_markup` формируется и отображается **только** при `ai_success=True`.
- История сохраняется через `db.save_ai_message()` **только** при `ai_success=True`.

### `handle_quick_question_callback`

Новый обработчик кнопок быстрых вопросов (`pattern=r'^qq:'`):
- Сопоставляет `callback_data` с префиксами и промптами из `messages.yaml`.
- Сохраняет префикс в `context.user_data['qq_prefix']` для подстановки в следующем сообщении.
- Отвечает запросом из `messages.yaml`.

### `handle_rating_callback`

Новый обработчик кнопок оценки ответа (`pattern=r'^rating:'`):
- Вызывает `db.log_ai_feedback(user_id, conv_id, feedback_type)`.
- Убирает клавиатуру с предыдущего сообщения через `query.edit_message_reply_markup(reply_markup=None)`.
- Отвечает текстом `rating_understood` или `rating_not_understood` из `messages.yaml`.

### `register_handlers`

Зарегистрированы два новых `CallbackQueryHandler`:
```python
CallbackQueryHandler(handle_quick_question_callback, pattern=r'^qq:')
CallbackQueryHandler(handle_rating_callback,         pattern=r'^rating:')
```

---

## `database.py`

### Новые таблицы

```sql
CREATE TABLE IF NOT EXISTS admin_logs (
    log_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    action    TEXT NOT NULL,
    details   TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_feedback (
    feedback_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    conversation_id INTEGER,
    feedback        TEXT NOT NULL,
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### Новые методы

| Метод | Описание |
|---|---|
| `log_admin_action(action, details)` | Записывает действие администратора в `admin_logs` |
| `log_ai_feedback(user_id, conv_id, feedback)` | Сохраняет оценку ответа AI в `ai_feedback` |
| `get_statistics() -> dict` | Возвращает агрегированную статистику: кол-во пользователей, групп, сообщений, обратной связи |
| `get_last_conversation_id(user_id) -> Optional[int]` | Возвращает `conversation_id` последней записи пользователя |
| `save_ai_message(user_id, message, response)` | Сохраняет пару вопрос/ответ в историю диалога |
| `get_conversation_history(user_id, limit) -> List[Dict]` | Возвращает последние `limit` обменов диалога |

---

## `modules/ai_tutor.py`

### Динамическая специализация

Добавлен `_get_specialization()` — читает `features.tutor.specialization` из `organization.yaml`,
при отсутствии возвращается к константе `TUTOR_SPECIALIZATION`.
`_create_system_prompt()` использует `_get_specialization()` вместо константы.

### История диалога

Добавлен статический метод `_build_messages()`:

```python
@staticmethod
def _build_messages(system_prompt, user_message, history=None) -> list:
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for turn in history:
            messages.append({"role": "user",      "content": turn['message']})
            messages.append({"role": "assistant",  "content": turn['response']})
    messages.append({"role": "user", "content": user_message})
    return messages
```

Все провайдеры (`_call_groq`, `_call_openai`, `_call_ollama`) принимают `history=None`
и используют `_build_messages()`. Gemini строит историю как текстовый блок перед промптом.

### `process_question`

- Новая сигнатура: `(question, user_context=None, history=None, raise_on_error=False)`.
- `raise_on_error=True` приводит к выбрасыванию исключения при неинициализированном AI
  (ранее молча возвращалась ошибка), что позволяет `handlers.py` активировать резервный провайдер.

### Цикл повтора для Ollama

```python
max_retries = int(tutor_cfg.get('ollama_retries', 2)) if self.provider == 'ollama' else 0
retry_delay  = float(tutor_cfg.get('ollama_retry_delay', 3))

for attempt in range(max_retries + 1):
    try:
        answer = await self._call_ollama(...)
        break
    except ConnectionError:
        if attempt < max_retries:
            await asyncio.sleep(retry_delay)
        else:
            raise
```

Параметры (`ollama_retries`, `ollama_retry_delay`) конфигурируются в `organization.yaml`.

---

## `bot.py`

### Инициализация резервного AI

После инициализации основного провайдера добавлена инициализация резервного:

```python
fallback_provider = self.config.FALLBACK_AI_PROVIDER.lower() \
    if self.config.FALLBACK_AI_PROVIDER else None

if fallback_provider and fallback_provider != provider:
    fallback_tutor = AITutor(provider=fallback_provider, ...)
    if fallback_tutor.initialized:
        self.application.bot_data['fallback_ai_tutor'] = fallback_tutor
```

Резервный провайдер активируется в `handle_message` автоматически при недоступности основного.

---

## `table.py`

### Группы из конфига

Удалён хардкод `GROUPS = ['1А', '1Б', ...]`. Заменён динамической загрузкой:

```python
def _load_groups_from_config() -> list:
    try:
        from config import Config
        groups = Config.get_groups_list()
        if groups:
            return groups
    except Exception as e:
        logger.warning(...)
    return []

GROUPS = _load_groups_from_config()
```

Валидация группы: `if GROUPS and group_name not in GROUPS:` — не блокирует при пустом списке.

### Вкладка «📊 Статистика»

Третья вкладка с `QScrollArea`, `stats_label` и кнопкой «Обновить»:
- `refresh_statistics()` — запускает асинхронную загрузку в фоновом потоке.
- `_load_statistics_async()` — вызывает `db.get_statistics()`.
- `_format_statistics(stats: dict) -> str` — форматирует данные в читаемый текст.

### Экспорт в Excel

Кнопка «📤 Экспорт в Excel» на вкладке данных:
- Открывает `QFileDialog` для выбора файла.
- `export_to_excel()` / `_export_async(filepath)` создают xlsx с тремя листами:
  **Учащиеся**, **Расписание**, **Статистика**.
- Автоматическая ширина столбцов через `column_dimensions`.
- Вызывает `db.log_admin_action('export_excel', ...)` по завершении.

### Подтверждение массовых операций

В `load_data_to_database()` добавлен диалог подтверждения.
Поведение управляется параметром `confirm_bulk_actions` в `organization.yaml`.
После успешной загрузки вызывается `db.log_admin_action('load_data', f'users={n}, schedule={m}')`.

---

## `deploy.sh`

### Переносимый `sed`

Добавлена функция `sed_inplace()` для совместимости macOS / Linux:

```bash
sed_inplace() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}
```

Все вызовы `sed -i ''` заменены на `sed_inplace`.

---

## Итог

| Файл | Характер изменений |
|---|---|
| `config.py` | Исправление бага в `get_groups_list()` |
| `organization.yaml` | Реальные группы, специализации, параметры Ollama, флаги функций |
| `messages.yaml` | 5 новых ключей для быстрых вопросов и оценки ответов |
| `handlers.py` | Полный рефакторинг: убран хардкод, добавлены callback-обработчики и история диалога |
| `database.py` | 2 новые таблицы, 6 новых методов |
| `modules/ai_tutor.py` | История диалога, динамическая специализация, retry-логика для Ollama, `raise_on_error` |
| `bot.py` | Инициализация и регистрация резервного AI-провайдера |
| `table.py` | Динамические группы, вкладка статистики, экспорт в Excel, подтверждение операций |
| `deploy.sh` | Кроссплатформенная функция `sed_inplace` |
