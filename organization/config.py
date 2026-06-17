"""
config.py — Конфигурация бота.
TASK 3.1: Organization config (ORG_CONFIG, ORGANIZATION_NAME, etc.)
TASK 3.2: Groups from config (DEFAULT_GROUPS, get_available_groups)
TASK 3.3: Messages from config (MESSAGES, get_message)
TASK 3.4: Multi-DB paths (DB_PATH, DB_PATH_ANALYTICS)
"""
import os
import re
from dataclasses import dataclass
from typing import Optional
import yaml
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: str = "config.yaml") -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        return {}


def _resolve_env(value: str) -> str:
    """Заменяет ${VAR} на значение из env."""
    if isinstance(value, str):
        return re.sub(r'\$\{(\w+)\}', lambda m: os.environ.get(m.group(1), ""), value)
    return value


_cfg = _load_yaml()

# ---------------------------------------------------------------------------
# TASK 3.1 — Organization config
# ---------------------------------------------------------------------------

ORGANIZATION_NAME: str = os.getenv(
    "ORGANIZATION_NAME",
    _resolve_env(_cfg.get("organization", {}).get("name", "ОбразовательныйБот"))
)
ORGANIZATION_DESCRIPTION: str = os.getenv(
    "ORGANIZATION_DESCRIPTION",
    _resolve_env(_cfg.get("organization", {}).get("description", ""))
)
SUPPORT_CONTACT: str = os.getenv(
    "SUPPORT_CONTACT",
    _resolve_env(_cfg.get("organization", {}).get("support_contact", ""))
)
LOGO_PATH: str = os.getenv(
    "LOGO_PATH",
    _resolve_env(_cfg.get("organization", {}).get("logo_path", "assets/logo.png"))
)


@dataclass
class OrgConfig:
    name: str
    description: str
    support_contact: str
    logo_path: str


ORG_CONFIG = OrgConfig(
    name=ORGANIZATION_NAME,
    description=ORGANIZATION_DESCRIPTION,
    support_contact=SUPPORT_CONTACT,
    logo_path=LOGO_PATH,
)

# ---------------------------------------------------------------------------
# TASK 3.4 — DB paths
# ---------------------------------------------------------------------------

_DB_PATH: str = os.getenv("DB_PATH", "data/bot.db")
_DB_PATH_ANALYTICS: Optional[str] = os.getenv("DB_PATH_ANALYTICS") or None

# ---------------------------------------------------------------------------
# TASK 3.2 — Groups from config
# ---------------------------------------------------------------------------

DEFAULT_GROUPS: list[str] = _cfg.get("groups", {}).get("default", [])


async def get_available_groups(db=None) -> list[str]:
    """
    Возвращает список групп: config.yaml (приоритет) + БД (users.group_name).
    Результат дедуплицирован. Config-группы идут первыми.
    """
    groups: list[str] = list(DEFAULT_GROUPS)
    if db is not None:
        try:
            db_groups = await db.get_all_groups()
            for g in db_groups:
                if g and g not in groups:
                    groups.append(g)
        except Exception:
            pass
    return groups


def get_groups_from_config() -> list[str]:
    """Возвращает только группы из config.yaml (без обращения к БД)."""
    return list(DEFAULT_GROUPS)

# ---------------------------------------------------------------------------
# TASK 3.3 — Messages from config
# ---------------------------------------------------------------------------

MESSAGES: dict = _cfg.get("messages", {})


def get_message(key: str, **kwargs) -> str:
    """
    Возвращает текст из config.yaml с подстановкой переменных.
    Поддерживает dot-notation: get_message("buttons.menu")
    {organization_name} подставляется автоматически.

    Примеры:
        get_message("welcome", first_name="Иван")
        get_message("buttons.back")
    """
    keys = key.split(".")
    node = MESSAGES
    for k in keys:
        if not isinstance(node, dict):
            return f"[missing: {key}]"
        node = node.get(k, f"[missing: {key}]")

    if not isinstance(node, str):
        return str(node)

    substitutions = {"organization_name": ORGANIZATION_NAME, **kwargs}
    try:
        return node.format_map(substitutions)
    except (KeyError, ValueError):
        return node

# ---------------------------------------------------------------------------
# Config class — обратная совместимость с существующим кодом
# ---------------------------------------------------------------------------


class Config:
    """Класс конфигурации. Полностью совместим с предыдущей версией."""

    BOT_TOKEN = os.getenv("BOT_TOKEN", "")

    REMINDER_INTERVAL = 2 * 60 * 60
    SCHEDULE_CHECK_INTERVAL = 60

    # TASK 3.4
    DB_PATH = _DB_PATH
    DB_PATH_ANALYTICS = _DB_PATH_ANALYTICS

    # AI
    AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
    AI_MODEL = os.getenv("AI_MODEL", "")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # TASK 3.1: Organization (доступны как атрибуты класса)
    ORGANIZATION_NAME = ORGANIZATION_NAME
    ORGANIZATION_DESCRIPTION = ORGANIZATION_DESCRIPTION
    SUPPORT_CONTACT = SUPPORT_CONTACT
    LOGO_PATH = LOGO_PATH
    ORG_CONFIG = ORG_CONFIG

    # TASK 3.2
    DEFAULT_GROUPS = DEFAULT_GROUPS

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в переменных окружения")
        return True
