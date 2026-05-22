"""
Обработчики команд и сообщений бота
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

from config import Config
from database import Database
from modules.ai_tutor import AITutor

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────────────────────────────────────

def _get_features() -> dict:
    """Загрузить секцию features из organization.yaml (с кешем)."""
    try:
        return Config.load_organization_config().get('features', {})
    except Exception:
        return {}


def _build_response_keyboard(quick_q_enabled: bool, rating_enabled: bool) -> InlineKeyboardMarkup | None:
    """Собрать InlineKeyboardMarkup для ответа AI."""
    rows = []
    if quick_q_enabled:
        rows.append([
            InlineKeyboardButton("📝 Объясни тему",    callback_data="qq:explain"),
            InlineKeyboardButton("💡 Дай пример",      callback_data="qq:example"),
            InlineKeyboardButton("✅ Проверь решение", callback_data="qq:check"),
        ])
    if rating_enabled:
        rows.append([
            InlineKeyboardButton("✅ Понял",    callback_data="rating:understood"),
            InlineKeyboardButton("❌ Не понял", callback_data="rating:not_understood"),
        ])
    return InlineKeyboardMarkup(rows) if rows else None


# ──────────────────────────────────────────────────────────────────────────────
# Основные команды
# ──────────────────────────────────────────────────────────────────────────────

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

    welcome_message = Config.get_message('main.welcome', first_name=user.first_name)

    # Показываем кнопки быстрых вопросов вместе с приветствием (если включены)
    features = _get_features()
    qq_cfg = features.get('quick_questions', {})
    if qq_cfg.get('enabled', False):
        markup = _build_response_keyboard(quick_q_enabled=True, rating_enabled=False)
        await update.message.reply_text(welcome_message, reply_markup=markup)
    else:
        await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = Config.get_message('main.help')
    features = _get_features()
    if features.get('quick_questions', {}).get('enabled', False):
        markup = _build_response_keyboard(quick_q_enabled=True, rating_enabled=False)
        await update.message.reply_text(help_text, reply_markup=markup)
    else:
        await update.message.reply_text(help_text)


async def class_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /class — устарела."""
    await update.message.reply_text(Config.get_message('main.error_class_removed'))


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    db: Database = context.bot_data.get('db')
    user_id = update.effective_user.id

    if db:
        user = await db.get_user(user_id)
        if user and user.get('group_name'):
            status_text = Config.get_message(
                'main.status',
                user_id=user_id,
                group=user.get('group_name')
            )
        else:
            status_text = (
                f"👤 Твоя информация:\n\n"
                f"Имя: {update.effective_user.first_name}\n"
                f"User ID: {user_id}\n\n"
            ) + Config.get_message('main.error_no_group')
    else:
        status_text = f"Информация недоступна.\n\nВаш User ID: {user_id}"

    await update.message.reply_text(status_text)


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /schedule"""
    db: Database = context.bot_data.get('db')
    user_id = update.effective_user.id

    if not db:
        await update.message.reply_text(Config.get_message('errors.db_connection'))
        return

    user = await db.get_user(user_id)
    if not user or not user.get('group_name'):
        await update.message.reply_text(Config.get_message('main.error_no_group'))
        return

    schedule = await db.get_user_schedule(user_id)
    if not schedule:
        await update.message.reply_text(Config.get_message('schedule.week_empty'))
        return

    schedule_text = f"📅 Твоё расписание (группа: {user.get('group_name')}):\n\n"
    days_order = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    schedule_by_day: dict = {}
    for lesson in schedule:
        schedule_by_day.setdefault(lesson['day_of_week'], []).append(lesson)

    for day in days_order:
        if day in schedule_by_day:
            schedule_text += f"📆 {day.capitalize()}:\n"
            for lesson in sorted(schedule_by_day[day], key=lambda x: x['lesson_time']):
                schedule_text += f"  ⏰ {lesson['lesson_time'][:5]}\n"
            schedule_text += "\n"

    await update.message.reply_text(schedule_text)


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /today"""
    db: Database = context.bot_data.get('db')
    user_id = update.effective_user.id

    if not db:
        await update.message.reply_text(Config.get_message('errors.db_connection'))
        return

    user = await db.get_user(user_id)
    if not user or not user.get('group_name'):
        await update.message.reply_text(Config.get_message('main.error_no_group'))
        return

    days_ru = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    today_day = days_ru[datetime.now().weekday()]
    today_lessons = await db.get_schedule_by_group_and_day(user['group_name'], today_day)

    if today_lessons:
        today_text = Config.get_message('schedule.today', date=today_day) + "\n"
        today_text += f"Группа: {user.get('group_name')}\n\n"
        for lesson in sorted(today_lessons, key=lambda x: x['lesson_time']):
            today_text += f"⏰ {lesson['lesson_time'][:5]}\n"
        await update.message.reply_text(today_text)
    else:
        await update.message.reply_text(Config.get_message('schedule.today_empty'))


# ──────────────────────────────────────────────────────────────────────────────
# AI-репетитор — основной обработчик
# ──────────────────────────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений: вызывает AI-репетитора."""
    user_id = update.effective_user.id
    user_message = update.message.text

    # Подставляем шаблон быстрого вопроса (если пользователь нажал inline-кнопку)
    prefix = context.user_data.pop('qq_prefix', '')
    if prefix:
        user_message = prefix + user_message

    await update.message.chat.send_action(action="typing")

    db: Database = context.bot_data.get('db')
    user_context = None
    history = []

    if db:
        user = await db.get_user(user_id)
        if user:
            user_context = {
                'group_name': user.get('group_name'),
                'full_name':  user.get('full_name'),
                'user_id':    user_id,
            }
        # История диалога
        features = _get_features()
        context_limit = features.get('tutor', {}).get('context_messages', 10)
        history = await db.get_conversation_history(user_id, limit=context_limit)

    ai_tutor: AITutor     = context.bot_data.get('ai_tutor')
    fallback_tutor: AITutor = context.bot_data.get('fallback_ai_tutor')

    ai_success = False

    if not ai_tutor:
        response = Config.get_message('tutor.error_no_ai')
    else:
        try:
            response = await ai_tutor.process_question(
                user_message, user_context, history,
                raise_on_error=bool(fallback_tutor)
            )
            ai_success = True
        except Exception as primary_err:
            logger.warning(f"Основной AI недоступен — пробуем резервный: {primary_err}")
            if fallback_tutor:
                try:
                    response = await fallback_tutor.process_question(
                        user_message, user_context, history
                    )
                    ai_success = True
                except Exception as fallback_err:
                    logger.error(f"Резервный AI тоже недоступен: {fallback_err}")
                    response = Config.get_message('tutor.error_no_ai')
            else:
                response = Config.get_message('tutor.error_no_ai')

    # Кнопки быстрых вопросов и оценки — только при успешном ответе AI
    features = _get_features()
    reply_markup = None
    if ai_success:
        qq_on     = features.get('quick_questions', {}).get('enabled', False)
        rating_on = features.get('answer_rating',   {}).get('enabled', False)
        reply_markup = _build_response_keyboard(qq_on, rating_on)

    await update.message.reply_text(response, reply_markup=reply_markup)

    # Сохраняем историю только при успешном ответе AI
    if db and ai_success:
        try:
            await db.save_ai_message(user_id, user_message, response)
        except Exception as e:
            logger.warning(f"Не удалось сохранить историю диалога: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Callback-обработчики (InlineKeyboard)
# ──────────────────────────────────────────────────────────────────────────────

async def handle_quick_question_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия кнопок быстрых вопросов (5.2)."""
    query = update.callback_query
    await query.answer()

    prefixes = {
        'qq:explain': "📝 Объясни тему: ",
        'qq:example': "💡 Дай пример по теме: ",
        'qq:check':   "✅ Проверь моё решение: ",
    }
    prompts = {
        'qq:explain': Config.get_message('tutor.quick_explain_prompt'),
        'qq:example': Config.get_message('tutor.quick_example_prompt'),
        'qq:check':   Config.get_message('tutor.quick_check_prompt'),
    }

    prefix = prefixes.get(query.data, '')
    prompt = prompts.get(query.data, 'Введи свой вопрос:')

    if prefix:
        context.user_data['qq_prefix'] = prefix

    await query.message.reply_text(prompt)


async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия кнопок оценки ответа AI (5.2)."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    feedback_type = query.data.split(':')[1]  # 'understood' | 'not_understood'

    # Логируем оценку в БД
    db: Database = context.bot_data.get('db')
    if db:
        try:
            conv_id = await db.get_last_conversation_id(user_id)
            await db.log_ai_feedback(user_id, conv_id, feedback_type)
        except Exception as e:
            logger.warning(f"Не удалось сохранить оценку: {e}")

    # Убираем кнопки с предыдущего сообщения
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Отвечаем пользователю
    key = 'tutor.rating_understood' if feedback_type == 'understood' else 'tutor.rating_not_understood'
    await query.message.reply_text(Config.get_message(key))


# ──────────────────────────────────────────────────────────────────────────────
# Регистрация обработчиков
# ──────────────────────────────────────────────────────────────────────────────

def register_handlers(application: Application):
    """Регистрация всех обработчиков команд и callback-ов."""
    # Команды
    application.add_handler(CommandHandler("start",    start_command))
    application.add_handler(CommandHandler("help",     help_command))
    application.add_handler(CommandHandler("class",    class_command))
    application.add_handler(CommandHandler("status",   status_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("today",    today_command))

    # Inline-кнопки
    application.add_handler(CallbackQueryHandler(handle_quick_question_callback, pattern=r'^qq:'))
    application.add_handler(CallbackQueryHandler(handle_rating_callback,         pattern=r'^rating:'))

    # Текстовые сообщения — AI-репетитор
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Обработчики зарегистрированы")
