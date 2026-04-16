# ADVANCED_FEATURES.md — Продвинутые функции администрирования и аналитики

## 📋 Содержание

1. [Администрирование](#администрирование)
2. [Аналитика](#аналитика)
3. [Мониторинг](#мониторинг)
4. [Оптимизация](#оптимизация)
5. [Безопасность](#безопасность)

---

## Администрирование

### TASK 5.3: Администрирование и аналитика

#### Логирование действий администратора

Все действия админов логируются в `data/logs/admin_actions.log`:

```python
# В admin_loader.py логируются:
# - Кто загрузил данные (дата/время)
# - Какие таблицы обновлены
# - Количество добавленных/изменённых записей
# - Ошибки при загрузке

# Пример логирования
logger.info(f"Admin action: Loaded {count} students from {filename}")
logger.warning(f"Admin action: Failed to load {failed_count} records")
```

#### Просмотр логов

```bash
# Все логи администратора
cat data/logs/admin_actions.log

# Последние 20 строк
tail -20 data/logs/admin_actions.log

# Поиск по администратору
grep "loaded" data/logs/admin_actions.log

# Мониторинг в реальном времени
tail -f data/logs/admin_actions.log
```

#### Экспорт в Excel

```bash
# Команда для экспорта текущих таблиц в Excel
python -c "
from admin_loader_excel import ExcelExporter
import asyncio

async def export():
    exporter = ExcelExporter()
    await exporter.export_students('exported_students.xlsx')
    await exporter.export_schedule('exported_schedule.xlsx')
    print('✓ Экспорт завершён')

asyncio.run(export())
"
```

#### Подтверждение перед массовыми операциями

Добавьте в admin_loader.py:

```python
import asyncio

async def prompt_confirmation(action: str, count: int) -> bool:
    '''Запросить подтверждение перед массовой операцией'''
    
    print(f"\n⚠️  Вы собираетесь выполнить действие на {count} записях")
    print(f"Действие: {action}")
    print("\nЭто может быть необратимо!")
    
    response = input("\nПродолжить? (y/n): ").strip().lower()
    return response == 'y'

# Использование
if await prompt_confirmation("Удалить всех студентов", student_count):
    await delete_all_students()
    logger.info(f"Deleted all {student_count} students")
else:
    print("Операция отменена")
```

---

## Аналитика

### TASK 5.3: Простая аналитика в приложении

#### Статистика в table.py

Добавьте вкладку "Статистика":

```python
# В table.py добавить вкладку
class StatisticsTab(QWidget):
    '''Вкладка со статистикой'''
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Статистика по группам
        groups_label = QLabel("👥 Пользователей по группам:")
        groups_table = self._create_groups_stats_table()
        
        # Статистика расписания
        schedule_label = QLabel("📅 Записей расписания: {}".format(
            self._count_schedule_records()
        ))
        
        # Последняя синхронизация
        sync_label = QLabel(f"🔄 Последняя синхронизация: {self._last_sync_time()}")
        
        # Активность пользователей
        activity_label = QLabel("📈 Активность:")
        activity_table = self._create_activity_table()
        
        layout.addWidget(groups_label)
        layout.addWidget(groups_table)
        layout.addSpacing(20)
        layout.addWidget(schedule_label)
        layout.addWidget(sync_label)
        layout.addSpacing(20)
        layout.addWidget(activity_label)
        layout.addWidget(activity_table)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _create_groups_stats_table(self) -> QTableWidget:
        '''Таблица со статистикой по группам'''
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Группа", "Пользователей", "%"])
        
        # Заполнить данные из БД
        async def load_stats():
            db = Database()
            stats = await db.get_group_statistics()
            return stats
        
        # async to sync
        stats = asyncio.run(load_stats())
        
        for i, (group, count, percentage) in enumerate(stats):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(group))
            table.setItem(i, 1, QTableWidgetItem(str(count)))
            table.setItem(i, 2, QTableWidgetItem(f"{percentage:.1f}%"))
        
        return table
    
    def _count_schedule_records(self) -> int:
        '''Количество записей расписания'''
        # Запрос к БД
        return 150  # Пример
    
    def _last_sync_time(self) -> str:
        '''Время последней синхронизации'''
        # Прочитать из логов или БД
        return "2024-01-15 14:30:45"
    
    def _create_activity_table(self) -> QTableWidget:
        '''Таблица активности'''
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Дата", "Сообщений", "Запросов к AI"])
        # Заполнить данные
        return table
```

#### Сбор аналитики в боте

```python
# В handlers.py добавить сбор метрик

class AnalyticsCollector:
    '''Сбор аналитики использования бота'''
    
    def __init__(self, db: Database):
        self.db = db
        self.stats = {
            'messages_total': 0,
            'ai_queries': 0,
            'schedule_requests': 0,
            'users_active': 0,
            'errors': 0
        }
    
    async def log_message(self, user_id: int, text: str):
        '''Логировать сообщение пользователя'''
        await self.db.log_analytics({
            'user_id': user_id,
            'event_type': 'message',
            'content': text,
            'timestamp': datetime.now()
        })
        self.stats['messages_total'] += 1
    
    async def log_ai_query(self, user_id: int, query: str, response: str):
        '''Логировать запрос к AI'''
        await self.db.log_analytics({
            'user_id': user_id,
            'event_type': 'ai_query',
            'query': query,
            'response': response,
            'timestamp': datetime.now()
        })
        self.stats['ai_queries'] += 1
    
    async def get_statistics(self, start_date, end_date) -> dict:
        '''Получить статистику за период'''
        return await self.db.get_analytics(start_date, end_date)
```

#### Экспорт аналитики

```python
# Экспорт статистики в CSV
import csv
from datetime import datetime

async def export_analytics_csv():
    '''Экспортировать аналитику в CSV'''
    db = Database()
    
    stats = await db.get_analytics(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )
    
    with open('analytics_export.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'event_type', 'count'])
        writer.writeheader()
        
        for stat in stats:
            writer.writerow({
                'date': stat['date'],
                'event_type': stat['event_type'],
                'count': stat['count']
            })
    
    print("✓ Аналитика экспортирована в analytics_export.csv")
```

---

## Мониторинг

### Мониторинг здоровья бота

```python
# health_check.py — проверка здоровья бота

import asyncio
from datetime import datetime
from config import Config
from database import Database
from modules.ai_tutor import AITutor

class HealthChecker:
    '''Проверка здоровья компонент бота'''
    
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.results = {}
    
    async def check_all(self) -> dict:
        '''Запустить все проверки'''
        print("🔍 Проверка здоровья бота...\n")
        
        self.results['database'] = await self.check_database()
        self.results['ai_provider'] = await self.check_ai()
        self.results['requirements'] = await self.check_requirements()
        self.results['disk_space'] = await self.check_disk_space()
        
        self._print_results()
        return self.results
    
    async def check_database(self) -> dict:
        '''Проверить базу данных'''
        try:
            await self.db.init_db()
            
            # Проверить количество записей
            users = await self.db.execute_query("SELECT COUNT(*) FROM users")
            
            return {
                'status': 'OK',
                'users': users[0][0] if users else 0,
                'message': 'БД работает нормально'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Ошибка БД: {str(e)}'
            }
    
    async def check_ai(self) -> dict:
        '''Проверить AI провайдер'''
        try:
            ai = AITutor(
                provider=self.config.AI_PROVIDER,
                api_key=self.config.GROQ_API_KEY or self.config.AI_API_KEY
            )
            
            if not ai.initialized:
                return {
                    'status': 'WARNING',
                    'provider': self.config.AI_PROVIDER,
                    'message': f'Провайдер {self.config.AI_PROVIDER} не инициализирован'
                }
            
            # Тестовый запрос
            response = await ai.ask("Test query")
            
            if response:
                return {
                    'status': 'OK',
                    'provider': self.config.AI_PROVIDER,
                    'message': 'AI провайдер работает'
                }
            else:
                return {
                    'status': 'ERROR',
                    'provider': self.config.AI_PROVIDER,
                    'message': 'AI возвращает пустой ответ'
                }
        
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Ошибка AI: {str(e)}'
            }
    
    async def check_requirements(self) -> dict:
        '''Проверить установленные пакеты'''
        required = [
            'telegram',
            'dotenv',
            'aiosqlite',
            'openpyxl',
            'pandas',
            'pyyaml'
        ]
        
        missing = []
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if not missing:
            return {
                'status': 'OK',
                'message': 'Все зависимости установлены'
            }
        else:
            return {
                'status': 'ERROR',
                'missing': missing,
                'message': f'Отсутствуют п пакеты: {", ".join(missing)}'
            }
    
    async def check_disk_space(self) -> dict:
        '''Проверить свободное место на диске'''
        import shutil
        
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024**3)
        
        status = 'OK'
        if free_gb < 1:
            status = 'ERROR'
        elif free_gb < 5:
            status = 'WARNING'
        
        return {
            'status': status,
            'free_gb': round(free_gb, 2),
            'message': f'Свободно: {free_gb:.2f} ГБ'
        }
    
    def _print_results(self):
        '''Вывести результаты'''
        print("📊 Результаты проверки:\n")
        
        for component, result in self.results.items():
            status = result['status']
            icon = '✅' if status == 'OK' else '⚠️' if status == 'WARNING' else '❌'
            message = result.get('message', '')
            
            print(f"{icon} {component.upper()}: {message}")
            
            if 'provider' in result:
                print(f"   Провайдер: {result['provider']}")
            if 'users' in result:
                print(f"   Пользователей: {result['users']}")
            if 'missing' in result:
                print(f"   Отсутствуют: {', '.join(result['missing'])}")
            if 'free_gb' in result:
                print(f"   Свободно: {result['free_gb']} ГБ")
            
            print()

# Использование
if __name__ == '__main__':
    async def main():
        checker = HealthChecker()
        await checker.check_all()
    
    asyncio.run(main())
```

Запуск проверки здоровья:

```bash
python -c "from health_check import HealthChecker; import asyncio; asyncio.run(HealthChecker().check_all())"
```

---

## Оптимизация

### TASK 5.4: Обработка ошибок и повторные попытки

```python
# retry_handler.py — механизм повтора с экспоненциальной задержкой

import asyncio
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0
):
    '''Декоратор для повтора функции с экспоненциальной задержкой'''
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Попытка {attempt + 1} из {max_retries} не удалась: {str(e)}. "
                            f"Повтор через {delay} сек..."
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"Все {max_retries} попытки исчерпаны для {func.__name__}"
                        )
            
            raise last_exception
        
        return async_wrapper
    
    return decorator

# Использование
@retry_with_backoff(max_retries=3, initial_delay=2.0)
async def ask_ai(query: str) -> str:
    '''Запрос к AI с повторными попытками'''
    ai_tutor = AITutor()
    return await ai_tutor.ask(query)

# Вызов
try:
    response = await ask_ai("Как решить задачу?")
except Exception as e:
    logger.error(f"Не удалось получить ответ от AI: {e}")
    response = "Сейчас AI недоступен. Попробуйте позже."
```

### Резервный провайдер AI

```python
# В AITutor добавить fallback логику

class AITutor:
    def __init__(self, provider=None, fallback_provider=None, **kwargs):
        self.provider = provider or Config.AI_PROVIDER
        self.fallback_provider = fallback_provider or Config.FALLBACK_AI_PROVIDER
        # ... инициализация
    
    async def ask(self, query: str) -> str:
        '''Запрос с fallback на резервный провайдер'''
        try:
            # Пытаемся основной провайдер
            return await self._ask_provider(self.provider, query)
        
        except Exception as e:
            logger.warning(f"Основной провайдер {self.provider} недоступен: {e}")
            
            if self.fallback_provider:
                logger.info(f"Использую резервный провайдер: {self.fallback_provider}")
                try:
                    return await self._ask_provider(self.fallback_provider, query)
                except Exception as e2:
                    logger.error(f"Оба провайдера недоступны: {e2}")
                    raise
            else:
                raise
    
    async def _ask_provider(self, provider: str, query: str) -> str:
        '''Запрос к конкретному провайдеру'''
        if provider == 'groq':
            return await self._ask_groq(query)
        elif provider == 'ollama':
            return await self._ask_ollama(query)
        elif provider == 'gemini':
            return await self._ask_gemini(query)
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

---

## Безопасность

### TASK 5.4: Защита и валидация

```python
# validators.py — валидация входных данных

import re
from typing import Tuple

class InputValidator:
    '''Валидация входных данных от пользователей'''
    
    @staticmethod
    def validate_user_query(query: str, max_length: int = 4000) -> Tuple[bool, str]:
        '''Проверить запрос пользователя'''
        
        # Проверка на пустоту
        if not query or not query.strip():
            return False, "Запрос не может быть пустым"
        
        # Проверка длины
        if len(query) > max_length:
            return False, f"Запрос слишком длинный (макс. {max_length} символов)"
        
        # Проверка на вредоносный код (простой пример)
        dangerous_patterns = [
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'UNION\s+SELECT',
            r'<script>',
            r'javascript:'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Запрос содержит потенциально опасный код"
        
        return True, "OK"
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        '''Проверить email'''
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if re.match(pattern, email):
            return True, "OK"
        else:
            return False, "Неверный формат email"
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        '''Проверить номер телефона'''
        # Простая проверка на цифры
        digits_only = re.sub(r'\D', '', phone)
        
        if len(digits_only) >= 10:
            return True, "OK"
        else:
            return False, "Неверный номер телефона"

# Использование в handlers
from validators import InputValidator

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обработка сообщения с валидацией'''
    query = update.message.text
    
    # Валидируем запрос
    is_valid, message = InputValidator.validate_user_query(query)
    
    if not is_valid:
        await update.message.reply_text(f"❌ {message}")
        return
    
    # Обрабатываем валидный запрос
    ai_tutor = context.bot_data.get('ai_tutor')
    response = await ai_tutor.ask(query)
    await update.message.reply_text(response)
```

### Логирование безопасности

```python
# security_logger.py — логирование событий безопасности

import logging
from datetime import datetime

security_logger = logging.getLogger('security')
handler = logging.FileHandler('data/logs/security.log')
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
security_logger.addHandler(handler)
security_logger.setLevel(logging.WARNING)

def log_security_event(event_type: str, user_id: int, details: str):
    '''Логировать события безопасности'''
    message = f"[{event_type}] User {user_id}: {details}"
    
    if event_type == 'invalid_query':
        security_logger.warning(message)
    elif event_type == 'unauthorized_access':
        security_logger.error(message)
    elif event_type == 'suspicious_activity':
        security_logger.critical(message)
```

---

**Последнее обновление**: April 16, 2026
