"""
Обработчики команд и сообщений бота
"""
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from database import Database
from modules.ai_tutor import AITutor

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    db: Database = context.bot_data.get('db')
    
    if db:
        await db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
    
    welcome_message = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Я твой образовательный помощник с элементами ИИ.\n\n"
        "Я могу помочь тебе:\n"
        "• 📚 Учиться с помощью контекстного AI-репетитора\n"
        "• 📅 Планировать свои занятия\n"
        "• 📖 Использовать справочник знаний\n\n"
        "Используй /help для списка команд."
    )
    
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📋 Доступные команды:\n\n"
        "👤 Основные:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/status - Показать твою информацию (включая User ID)\n\n"
        "📅 Расписание:\n"
        "/schedule - Показать твое расписание на неделю\n"
        "/today - Занятия на сегодня\n\n"
        "🤖 AI-репетитор:\n"
        "Просто напиши мне вопрос или задачу, и я помогу тебе!\n"
        "Я могу решать примеры, объяснять темы и отвечать на вопросы."
    )
    
    await update.message.reply_text(help_text)


async def class_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /class больше не используется (теперь группы назначает администратор)."""
    await update.message.reply_text(
        "В учебном центре нет «классов» — используется «группа», которую назначает администратор.\n"
        "Если у тебя не отображается расписание, обратись к администратору."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    db: Database = context.bot_data.get('db')
    user_id = update.effective_user.id
    
    if db:
        user = await db.get_user(user_id)
        if user and user.get('group_name'):
            status_text = (
                f"👤 Твоя информация:\n\n"
                f"Имя: {user.get('first_name', 'Не указано')}\n"
                f"Группа: {user.get('group_name')}\n"
                f"User ID: {user_id}\n"
                f"Статус: Активен ✅"
            )
        else:
            status_text = (
                "👤 Твоя информация:\n\n"
                f"Имя: {update.effective_user.first_name}\n"
                f"User ID: {user_id}\n"
                "Группа: Не указана\n\n"
                "Группу назначает администратор."
            )
    else:
        status_text = f"Информация недоступна.\n\nВаш User ID: {user_id}"
    
    await update.message.reply_text(status_text)


# Команды для работы с расписанием
async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /schedule"""
    db: Database = context.bot_data.get('db')
    user_id = update.effective_user.id
    
    if db:
        user = await db.get_user(user_id)
        if not user or not user.get('group_name'):
            await update.message.reply_text(
                "Твоя группа ещё не назначена администратором. Обратись к администратору."
            )
            return
            
        schedule = await db.get_user_schedule(user_id)
        if schedule:
            schedule_text = f"📅 Твое расписание (группа: {user.get('group_name')}):\n\n"
            current_day = None
            
            # Группируем по дням недели
            days_order = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
            schedule_by_day = {}
            for lesson in schedule:
                day = lesson['day_of_week']
                if day not in schedule_by_day:
                    schedule_by_day[day] = []
                schedule_by_day[day].append(lesson)
            
            # Выводим по порядку дней недели
            for day in days_order:
                if day in schedule_by_day:
                    schedule_text += f"📆 {day.capitalize()}:\n"
                    lessons = sorted(schedule_by_day[day], key=lambda x: x['lesson_time'])
                    for lesson in lessons:
                        time_str = lesson['lesson_time'][:5] if len(lesson['lesson_time']) >= 5 else lesson['lesson_time']
                        schedule_text += f"  ⏰ {time_str}\n"
                    schedule_text += "\n"
            
            await update.message.reply_text(schedule_text)
        else:
            await update.message.reply_text(
                "У тебя пока нет занятий в расписании."
            )
    else:
        await update.message.reply_text("Ошибка: база данных недоступна.")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /today"""
    db: Database = context.bot_data.get('db')
    user_id = update.effective_user.id
    
    if db:
        user = await db.get_user(user_id)
        if not user or not user.get('group_name'):
            await update.message.reply_text(
                "Твоя группа ещё не назначена администратором. Обратись к администратору."
            )
            return
        
        # Определяем сегодняшний день недели
        from datetime import datetime
        days_ru = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
        today_weekday = datetime.now().weekday()
        today_day = days_ru[today_weekday]
        
        # Получаем расписание на сегодня для группы пользователя
        today_lessons = await db.get_schedule_by_group_and_day(user['group_name'], today_day)
        
        if today_lessons:
            today_text = f"📚 Занятия на сегодня ({today_day}) (группа: {user.get('group_name')}):\n\n"
            # Сортируем по времени
            today_lessons_sorted = sorted(today_lessons, key=lambda x: x['lesson_time'])
            for lesson in today_lessons_sorted:
                time_str = lesson['lesson_time'][:5] if len(lesson['lesson_time']) >= 5 else lesson['lesson_time']
                today_text += f"⏰ {time_str}\n"
            await update.message.reply_text(today_text)
        else:
            await update.message.reply_text(
                f"🎉 У тебя сегодня ({today_day}) нет занятий!\n"
                "Можешь отдохнуть или заняться чем-то полезным."
            )
    else:
        await update.message.reply_text("Ошибка: база данных недоступна.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений с AI-репетитором"""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Показываем индикатор печати
    await update.message.chat.send_action(action="typing")
    
    # Получаем контекст пользователя из БД
    db: Database = context.bot_data.get('db')
    user_context = None
    
    if db:
        user = await db.get_user(user_id)
        if user:
            user_context = {
                'group_name': user.get('group_name'),
                'full_name': user.get('full_name'),
                'user_id': user_id
            }
    
    # Получаем AI-репетитора из bot_data (инициализируется в bot.py)
    ai_tutor: AITutor = context.bot_data.get('ai_tutor')
    
    if not ai_tutor:
        # Если AI-репетитор не инициализирован, используем заглушку
        response = (
            "🤖 AI-репетитор временно недоступен.\n\n"
            "Для работы AI-репетитора необходимо настроить API ключ OpenAI.\n"
            "Обратитесь к администратору или используйте команды бота."
        )
    else:
        # Обрабатываем вопрос через AI-репетитора
        try:
            response = await ai_tutor.process_question(user_message, user_context)
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения AI: {e}", exc_info=True)
            response = (
                "😔 Извини, произошла ошибка при обработке твоего вопроса.\n\n"
                "Попробуй переформулировать вопрос или обратись позже."
            )
    
    await update.message.reply_text(response)


def register_handlers(application: Application):
    """Регистрация всех обработчиков"""
    # Основные команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("class", class_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Команды для работы с расписанием
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("today", today_command))
    
    # Текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Обработчики зарегистрированы")

