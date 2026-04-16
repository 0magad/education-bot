"""
Конфигурация бота (TASK 3.1-3.4: поддержка конфигов организации)
"""
import os
import yaml
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()
logger = logging.getLogger(__name__)


class ConfigLoader:
    """Загрузчик YAML конфигов с поддержкой подстановки переменных (TASK 3.1)"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.env_vars = os.environ.copy()
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Загрузить YAML файл с подстановкой переменных из .env"""
        filepath = self.root_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Файл {filename} не найден, используем пустой конфиг")
            return {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Подставляем переменные вида ${VAR_NAME|default_value}
            content = self._substitute_variables(content)
            
            # Парсим YAML
            config = yaml.safe_load(content) or {}
            return config
        
        except Exception as e:
            logger.error(f"Ошибка при загрузке {filename}: {e}")
            return {}
    
    def _substitute_variables(self, content: str) -> str:
        """Заменить переменные вида ${VAR|default} на значения из .env"""
        import re
        
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_expr = match.group(1)
            
            # Парсим выражение VAR|default
            if '|' in var_expr:
                var_name, default_value = var_expr.split('|', 1)
                var_name = var_name.strip()
                default_value = default_value.strip()
            else:
                var_name = var_expr.strip()
                default_value = ''
            
            # Получаем значение из .env или используем default
            value = self.env_vars.get(var_name, default_value)
            return str(value)
        
        return re.sub(pattern, replace_var, content)


class Config:
    """Главный класс конфигурации (TASK 3.1-3.4)"""
    
    # === Основные параметры ===
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    
    # === Интервалы ===
    REMINDER_INTERVAL = 2 * 60 * 60  # 2 часа
    SCHEDULE_CHECK_INTERVAL = 60  # 1 минута
    
    # === БД ===
    DB_PATH = os.getenv('DB_PATH', 'data/bot.db')
    DB_PATH_ANALYTICS = os.getenv('DB_PATH_ANALYTICS', '')
    
    # === AI ===
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'ollama')
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1')
    AI_MODEL = os.getenv('AI_MODEL', '')
    FALLBACK_AI_PROVIDER = os.getenv('FALLBACK_AI_PROVIDER', '')
    
    # === Логирование ===
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # === TASK 3.1: Конфиги организации ===
    _org_config: Optional[Dict] = None
    _messages_config: Optional[Dict] = None
    _groups_config: Optional[Dict] = None
    _config_loader: Optional[ConfigLoader] = None
    
    @classmethod
    def validate(cls):
        """Проверка наличия обязательных параметров"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в переменных окружения")
        return True
    
    # === TASK 3.1: Методы для работы с конфигом организации ===
    
    @classmethod
    def _get_loader(cls) -> ConfigLoader:
        """Получить загрузчик конфигов (синглтон)"""
        if cls._config_loader is None:
            cls._config_loader = ConfigLoader()
        return cls._config_loader
    
    @classmethod
    def load_organization_config(cls) -> Dict[str, Any]:
        """Загрузить конфиг организации из organization.yaml"""
        if cls._org_config is None:
            loader = cls._get_loader()
            cls._org_config = loader.load_yaml('organization.yaml')
        return cls._org_config
    
    @classmethod
    def load_messages_config(cls) -> Dict[str, Any]:
        """Загрузить сообщения из messages.yaml"""
        if cls._messages_config is None:
            loader = cls._get_loader()
            cls._messages_config = loader.load_yaml('messages.yaml')
        return cls._messages_config
    
    @classmethod
    def load_groups_config(cls) -> Dict[str, Any]:
        """Загрузить группы из groups.yaml (TASK 3.2)"""
        if cls._groups_config is None:
            loader = cls._get_loader()
            cls._groups_config = loader.load_yaml('groups.yaml')
        return cls._groups_config
    
    @classmethod
    def get_organization_name(cls) -> str:
        """Получить название организации"""
        org_config = cls.load_organization_config()
        return org_config.get('organization', {}).get('name', 'Организация')
    
    @classmethod
    def get_organization_description(cls) -> str:
        """Получить описание организации"""
        org_config = cls.load_organization_config()
        return org_config.get('organization', {}).get('description', '')
    
    @classmethod
    def get_support_contact(cls) -> str:
        """Получить контакт поддержки"""
        org_config = cls.load_organization_config()
        return org_config.get('organization', {}).get('support_contact', '@support')
    
    @classmethod
    def get_groups_list(cls) -> list:
        """Получить список групп (TASK 3.2)
        Приоритет: organization.yaml -> groups.yaml
        """
        # Сначала пробуем из organization.yaml
        org_config = cls.load_organization_config()
        groups = org_config.get('groups', {}).get('default', [])

        if groups:
            return groups

        # Затем из groups.yaml — извлекаем все имена из иерархии категорий
        groups_config = cls.load_groups_config()
        if groups_config:
            result = []
            for category in groups_config.get('groups', {}).values():
                if isinstance(category, dict) and 'items' in category:
                    result.extend([item['name'] for item in category.get('items', [])])
            if result:
                return result

        return []
    
    # === TASK 3.3: Методы для работы с сообщениями ===
    
    @classmethod
    def get_message(cls, key: str, **kwargs) -> str:
        """Получить сообщение из messages.yaml с подстановкой переменных
        
        Примеры:
            Config.get_message('main.welcome', first_name='Иван')
            Config.get_message('schedule.today', date='01.01.2024')
        """
        messages = cls.load_messages_config()
        
        # Разделяем ключ на части (например 'main.welcome' -> ['main', 'welcome'])
        keys = key.split('.')
        message = messages
        
        for k in keys:
            if isinstance(message, dict):
                message = message.get(k, '')
            else:
                return ''
        
        if not isinstance(message, str):
            return str(message)
        
        # Добавляем стандартные переменные
        kwargs.setdefault('organization_name', cls.get_organization_name())
        kwargs.setdefault('support_contact', cls.get_support_contact())
        
        # Подставляем переменные
        try:
            return message.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Недостающа переменная {e} в сообщении {key}")
            return message
    
    @classmethod
    def get_button_text(cls, button_name: str) -> str:
        """Получить текст кнопки"""
        return cls.get_message(f'buttons.{button_name}')



