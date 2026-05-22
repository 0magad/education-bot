"""
Скрипт для получения user_id пользователя
После того как пользователь написал /start боту, его user_id сохраняется в базе данных
Этот скрипт поможет найти user_id по username
"""
import asyncio
import logging
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_user_id_by_username(db: Database, username: str):
    """
    Получение user_id по username
    
    Args:
        db: Экземпляр Database
        username: Username пользователя (без @)
    
    Returns:
        user_id или None если не найден
    """
    # Получаем всех пользователей и ищем по username
    users = await db.get_all_active_users()
    for user in users:
        if user.get('username') == username:
            return user
    return None


async def list_all_users(db: Database):
    """Показать всех пользователей в базе"""
    users = await db.get_all_active_users()
    if users:
        logger.info("\n=== Пользователи в базе данных ===")
        for user in users:
            username = user.get('username', 'Не указан')
            logger.info(f"User ID: {user['user_id']}, Username: @{username}, Имя: {user.get('first_name', 'Не указано')}")
    else:
        logger.info("В базе данных пока нет пользователей.")
        logger.info("Попросите пользователей написать /start боту, чтобы они добавились в базу.")


async def main():
    """Основная функция"""
    db = Database()
    await db.init_db()
    
    try:
        # Показать всех пользователей
        await list_all_users(db)
        
        # Пример поиска по username
        username = "Rkelmx"  # Без символа @
        user_info = await get_user_id_by_username(db, username)
        
        if user_info:
            logger.info(f"\n=== Найден пользователь ===")
            logger.info(f"User ID: {user_info['user_id']}")
            logger.info(f"Username: @{user_info['username']}")
            logger.info(f"Имя: {user_info['first_name']}")
            logger.info(f"\nИспользуйте этот User ID в load_data.py:")
            logger.info(f"({user_info['user_id']}, 'Математика')")
        else:
            logger.warning(f"\nПользователь @{username} не найден в базе данных.")
            logger.info("Попросите пользователя написать /start боту, чтобы он добавился в базу.")
            
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())

