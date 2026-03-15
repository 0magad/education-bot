"""
Основной файл Telegram-бота для образовательной системы
"""
import logging

from telegram import Update
from telegram.ext import Application

from config import Config
from database import Database
from handlers import register_handlers
from scheduler import Scheduler
from modules.ai_tutor import AITutor

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class EducationBot:
    """Основной класс бота"""
    
    def __init__(self):
        self.config = Config()
        self.db = Database(db_path=self.config.DB_PATH)
        self.scheduler = Scheduler(self.db)
        self.application = None
        
    async def initialize(self):
        """Асинхронная инициализация"""
        await self.db.init_db()

        # Заполняем маппинг групп на темы мероприятий
        # Временно — потом вынести в organization.yaml
        group_keywords = {
            'Пайтон для начинающих': ['python', 'программирование', 'вебинар', 'разработка'],
            'Основы веб-программирования': ['web', 'html', 'css', 'javascript', 'вебинар'],
            '3D моделирование': ['3d', 'blender', 'концепт-арт', 'геймдев'],
            'Инженерная графика': ['графика', 'cad', 'дизайн', 'чертёж'],
            'Интеллект-школа. История': ['олимпиада', 'история', 'обществознание'],
            'Интеллект школа. Русский язык': ['олимпиада', 'русский язык', 'литература'],
        }
        for group_name, keywords in group_keywords.items():
            await self.db.upsert_group_topics(group_name, keywords)
        logger.info('Маппинг групп на темы загружен')

        # Сохраняем ссылку на БД в bot_data для доступа из обработчиков
        self.application.bot_data['db'] = self.db
        
        # Инициализируем AI-репетитора с поддержкой бесплатных провайдеров
        provider = self.config.AI_PROVIDER.lower()
        
        # Определяем API ключ и параметры в зависимости от провайдера
        api_key = None
        base_url = None
        model = self.config.AI_MODEL if self.config.AI_MODEL else None
        
        if provider == 'groq':
            api_key = self.config.GROQ_API_KEY or self.config.AI_API_KEY
        elif provider == 'gemini':
            api_key = self.config.GEMINI_API_KEY
        elif provider == 'openai':
            api_key = self.config.AI_API_KEY
        elif provider == 'ollama':
            base_url = self.config.OLLAMA_BASE_URL
            if not model:
                model = self.config.OLLAMA_MODEL
        
        ai_tutor = AITutor(
            provider=provider,
            api_key=api_key if api_key else None,
            model=model,
            base_url=base_url
        )
        self.application.bot_data['ai_tutor'] = ai_tutor
        
        if ai_tutor.initialized:
            logger.info(f"AI-репетитор успешно инициализирован (провайдер: {provider}, модель: {model})")
        else:
            if provider == 'ollama':
                logger.warning(f"AI-репетитор не инициализирован (провайдер: {provider})")
                logger.warning("Убедитесь, что Ollama запущен: ollama serve")
                logger.warning(f"И что модель {model} установлена: ollama pull {model}")
            else:
                logger.warning(f"AI-репетитор не инициализирован (провайдер: {provider}, отсутствует API ключ)")
                logger.info("Для настройки бесплатных моделей см. FREE_AI_SETUP.md")
        
        # Устанавливаем бота в планировщик
        self.scheduler.set_bot(self.application.bot)
        await self.scheduler.start()
        logger.info("Бот успешно инициализирован")
        
        # Отправляем уведомления о грядущих занятиях при запуске
        await self.scheduler.send_startup_notifications()
        
    async def cleanup(self):
        """Очистка при остановке бота"""
        await self.scheduler.stop()
        await self.db.close()
        logger.info("Бот остановлен")
        
    def run(self):
        """Запуск бота"""
        # Создание приложения
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        
        # Регистрация обработчиков
        register_handlers(self.application)
        
        # Используем post_init и post_shutdown через правильный способ
        # Создаем обертки для совместимости с Python 3.14
        async def post_init_wrapper(app: Application):
            await self.initialize()
            
        async def post_shutdown_wrapper(app: Application):
            await self.cleanup()
        
        # Пересоздаем application с правильными колбэками
        self.application = Application.builder().token(self.config.BOT_TOKEN).post_init(post_init_wrapper).post_shutdown(post_shutdown_wrapper).build()
        
        # Регистрируем обработчики снова
        register_handlers(self.application)
        
        # Запуск бота
        try:
            logger.info("Запуск бота...")
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
        except KeyboardInterrupt:
            logger.info("Остановка бота по запросу пользователя")
        except Exception as e:
            logger.error(f"Ошибка при работе бота: {e}", exc_info=True)


def main():
    """Точка входа"""
    try:
        # Проверка конфигурации
        Config.validate()
        
        bot = EducationBot()
        bot.run()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        logger.error("Пожалуйста, убедитесь, что файл .env создан и содержит BOT_TOKEN")
    except KeyboardInterrupt:
        logger.info("Остановка бота по запросу пользователя")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)


if __name__ == '__main__':
    main()

