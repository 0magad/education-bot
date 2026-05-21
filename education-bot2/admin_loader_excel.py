"""
Скрипт для загрузки данных из Excel файлов
Для администраторов - просто заполните таблицы в Excel и запустите этот скрипт
"""
import asyncio
import logging
from pathlib import Path
from database import Database

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas не установлен. Установите: pip install pandas openpyxl")

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def load_from_excel_users(db: Database, excel_file: str):
    """
    Загрузка учащихся из Excel файла
    
    Лист должен называться 'Учащиеся' (или старое 'Ученики') или 'users'
    Колонки (новая логика): user_id, group_name, full_name, username, first_name, last_name
    """
    if not PANDAS_AVAILABLE:
        logger.error("pandas не установлен. Используйте admin_loader.py для CSV файлов")
        return
        
    if not Path(excel_file).exists():
        logger.error(f"Файл {excel_file} не найден!")
        return
    
    try:
        # Пробуем разные имена листов
        sheet_name = None
        for name in ['Учащиеся', 'Ученики', 'users', 'Users', 0]:
            try:
                df = pd.read_excel(excel_file, sheet_name=name)
                sheet_name = name
                break
            except:
                continue
        
        if sheet_name is None:
            logger.error("Не найден лист 'Ученики' или 'users' в Excel файле")
            return
        
        users_data = []
        for _, row in df.iterrows():
            user_id = int(row['user_id'])
            group_name = None
            if 'group_name' in row and pd.notna(row['group_name']):
                group_name = str(row['group_name']).strip()
            elif 'class_level' in row and pd.notna(row['class_level']):
                # поддержка старого формата
                group_name = str(row['class_level']).strip()
            full_name = str(row['full_name'])
            username = str(row.get('username', '')) if pd.notna(row.get('username')) else ''
            first_name = str(row.get('first_name', '')) if pd.notna(row.get('first_name')) else ''
            last_name = str(row.get('last_name', '')) if pd.notna(row.get('last_name')) else ''
            
            users_data.append((user_id, group_name, full_name, username, first_name, last_name))
        
        await db.bulk_add_users(users_data)
        logger.info(f"✅ Загружено {len(users_data)} учащихся из {excel_file}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке учеников: {e}", exc_info=True)


async def load_from_excel_schedule(db: Database, excel_file: str):
    """
    Загрузка расписания из Excel файла
    
    Лист должен называться 'Расписание' или 'schedule'
    Колонки (новая логика): group_name, day_of_week, lesson_time
    """
    if not PANDAS_AVAILABLE:
        logger.error("pandas не установлен. Используйте admin_loader.py для CSV файлов")
        return
        
    if not Path(excel_file).exists():
        logger.error(f"Файл {excel_file} не найден!")
        return
    
    try:
        # Пробуем разные имена листов
        sheet_name = None
        for name in ['Расписание', 'schedule', 'Schedule', 0]:
            try:
                df = pd.read_excel(excel_file, sheet_name=name)
                sheet_name = name
                break
            except:
                continue
        
        if sheet_name is None:
            logger.error("Не найден лист 'Расписание' или 'schedule' в Excel файле")
            return
        
        schedule_data = []
        for _, row in df.iterrows():
            group_name = None
            if 'group_name' in row and pd.notna(row['group_name']):
                group_name = str(row['group_name']).strip()
            elif 'subject' in row and pd.notna(row['subject']):
                # поддержка старого формата: subject -> group_name
                group_name = str(row['subject']).strip()
            day_of_week = str(row['day_of_week']).lower()
            lesson_time = str(row['lesson_time'])
            
            # Если время в формате datetime, конвертируем в строку
            if ':' not in lesson_time and hasattr(row['lesson_time'], 'strftime'):
                lesson_time = row['lesson_time'].strftime('%H:%M')
            
            schedule_data.append((group_name, day_of_week, lesson_time))
        
        await db.bulk_add_schedule(schedule_data)
        logger.info(f"✅ Загружено {len(schedule_data)} занятий из {excel_file}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке расписания: {e}", exc_info=True)


async def main():
    """
    Главная функция - загружает данные из Excel файлов
    """
    if not PANDAS_AVAILABLE:
        logger.error("Для работы с Excel установите: pip install pandas openpyxl")
        logger.info("Или используйте admin_loader.py для CSV файлов")
        return
    
    db = Database()
    await db.init_db()
    
    try:
        logger.info("=" * 50)
        logger.info("Загрузка данных из Excel файлов")
        logger.info("=" * 50)
        
        # Загрузка учеников
        users_file = 'data/users.xlsx'
        if Path(users_file).exists():
            logger.info(f"\n📋 Загрузка учеников из {users_file}...")
            await load_from_excel_users(db, users_file)
        else:
            logger.warning(f"⚠️  Файл {users_file} не найден. Создайте его на основе data/users_template.xlsx")
        
        # Загрузка расписания
        schedule_file = 'data/schedule.xlsx'
        if Path(schedule_file).exists():
            logger.info(f"\n📅 Загрузка расписания из {schedule_file}...")
            await load_from_excel_schedule(db, schedule_file)
        else:
            logger.warning(f"⚠️  Файл {schedule_file} не найден. Создайте его на основе data/schedule_template.xlsx")
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ Загрузка завершена!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())

