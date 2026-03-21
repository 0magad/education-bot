"""
database/connection.py

PR #2 — реализация поддержки нескольких БД.
ПРИМЕЧАНИЕ: DB_PATH существовал в ветке main, но поддержка нескольких БД
(get_main_db / get_analytics_db) — новая фича PR #2, не унаследована от main.
"""
from typing import Optional
from pathlib import Path
import aiosqlite
from config import Config

_main_conn: Optional[aiosqlite.Connection] = None
_analytics_conn: Optional[aiosqlite.Connection] = None


async def get_main_db() -> aiosqlite.Connection:
    """Возвращает соединение с основной БД (DB_PATH)."""
    global _main_conn
    if _main_conn is None:
        Path(Config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _main_conn = await aiosqlite.connect(Config.DB_PATH)
        _main_conn.row_factory = aiosqlite.Row
    return _main_conn


async def get_analytics_db() -> Optional[aiosqlite.Connection]:
    """
    Возвращает соединение с аналитической БД (DB_PATH_ANALYTICS).
    Возвращает None если DB_PATH_ANALYTICS не задан в .env.
    """
    if not Config.DB_PATH_ANALYTICS:
        return None

    global _analytics_conn
    if _analytics_conn is None:
        Path(Config.DB_PATH_ANALYTICS).parent.mkdir(parents=True, exist_ok=True)
        _analytics_conn = await aiosqlite.connect(Config.DB_PATH_ANALYTICS)
        _analytics_conn.row_factory = aiosqlite.Row
    return _analytics_conn


async def close_all():
    """Закрыть все соединения (вызывать при shutdown бота)."""
    global _main_conn, _analytics_conn
    if _main_conn:
        await _main_conn.close()
        _main_conn = None
    if _analytics_conn:
        await _analytics_conn.close()
        _analytics_conn = None
