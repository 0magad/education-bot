"""
Конфигурация бота: .env (секреты) + organization.yaml (настройки)
Интерфейс не меняется — существующий код работает без правок.
"""
import os
from pathlib import Path
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = Path(__file__).resolve().parent / 'organization.yaml'


@lru_cache(maxsize=1)
def _get_yaml() -> dict:
    """Загружает organization.yaml (кэш)."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        import yaml
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return {}
    except Exception:
        return {}


def _cfg(*keys: str, default: Any = None) -> Any:
    d = _get_yaml()
    for k in keys:
        d = (d or {}).get(k) if isinstance(d, dict) else None
        if d is None:
            return default
    return d


class Config:
    """Интерфейс как раньше — BOT_TOKEN, REMINDER_INTERVAL и т.д."""

    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

    REMINDER_INTERVAL = _cfg('bot', 'reminder_interval') or 2 * 60 * 60
    SCHEDULE_CHECK_INTERVAL = _cfg('bot', 'schedule_check_interval') or 60
    LOG_LEVEL = os.getenv('LOG_LEVEL') or _cfg('bot', 'log_level') or 'INFO'

    DB_PATH = os.getenv('DB_PATH') or _cfg('database', 'path') or 'data/bot.db'

    AI_PROVIDER = os.getenv('AI_PROVIDER') or _cfg('ai', 'provider') or 'ollama'
    AI_MODEL = os.getenv('AI_MODEL') or _cfg('ai', 'model') or ''
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL') or _cfg('ai', 'ollama', 'base_url') or 'http://localhost:11434'
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL') or _cfg('ai', 'ollama', 'model') or 'llama3.1'

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в переменных окружения")
        return True
