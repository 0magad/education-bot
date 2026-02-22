"""
Скрипт для загрузки данных из Excel/CSV файлов
Для администраторов - просто заполните таблицы и запустите этот скрипт

Поддерживает:
- CSV файлы (data/users.csv, data/schedule.csv)
- Excel файлы (data/users.xlsx, data/schedule.xlsx) - если установлен pandas
"""
import asyncio
import logging
import csv
from pathlib import Path
from io import StringIO
from database import Database

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def load_from_csv_users(db: Database, csv_file: str):
    """
    Загрузка учащихся из CSV файла
    
    Формат CSV:
    user_id,group_name,full_name,username,first_name,last_name
    6218121239,Основы веб-программирования,Иванов Иван Иванович,Rkelmx,Иван,Иванов
    """
    if not Path(csv_file).exists():
        logger.error(f"Файл {csv_file} не найден!")
        return
    
    users_data = []
    try:
        # Пробуем разные кодировки
        encodings = ['utf-8-sig', 'utf-8', 'cp1251']
        file_content = None
        used_encoding = None
        
        for enc in encodings:
            try:
                with open(csv_file, 'r', encoding=enc) as f:
                    file_content = f.read()
                    used_encoding = enc
                    break
            except:
                continue
        
        if file_content is None:
            logger.error(f"Не удалось прочитать файл {csv_file}")
            return
        
        # Читаем CSV из строки
        reader = csv.DictReader(StringIO(file_content))
        for row in reader:
            user_id = int(row['user_id'])
            group_name = (row.get('group_name') or row.get('subject') or row.get('class_level') or '').strip() or None
            full_name = row['full_name']
            username = row.get('username', '')
            first_name = row.get('first_name', '')
            last_name = row.get('last_name', '')
            
            users_data.append((user_id, group_name, full_name, username, first_name, last_name))
        
        await db.bulk_add_users(users_data)
        logger.info(f"✅ Загружено {len(users_data)} учащихся из {csv_file}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке учеников: {e}", exc_info=True)


async def load_from_csv_schedule(db: Database, csv_file: str):
    """
    Загрузка расписания из CSV файла
    
    Формат CSV:
    group_name,day_of_week,lesson_time
    Основы веб-программирования,вторник,14:00
    Основы веб-программирования,вторник,16:30
    """
    if not Path(csv_file).exists():
        logger.error(f"Файл {csv_file} не найден!")
        return
    
    schedule_data = []
    try:
        # Пробуем разные кодировки
        encodings = ['utf-8-sig', 'utf-8', 'cp1251']
        file_content = None
        used_encoding = None
        
        for enc in encodings:
            try:
                with open(csv_file, 'r', encoding=enc) as f:
                    file_content = f.read()
                    used_encoding = enc
                    break
            except:
                continue
        
        if file_content is None:
            logger.error(f"Не удалось прочитать файл {csv_file}")
            return
        
        # Читаем CSV из строки
        reader = csv.DictReader(StringIO(file_content))
        for row in reader:
            group_name = (row.get('group_name') or row.get('subject') or '').strip() or None
            day_of_week = row['day_of_week'].lower()
            lesson_time = row['lesson_time']
            
            schedule_data.append((group_name, day_of_week, lesson_time))
        
        await db.bulk_add_schedule(schedule_data)
        logger.info(f"✅ Загружено {len(schedule_data)} занятий из {csv_file}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке расписания: {e}", exc_info=True)


async def load_from_excel_users(db: Database, excel_file: str):
    """Загрузка учащихся из Excel файла"""
    if not PANDAS_AVAILABLE:
        logger.error("pandas не установлен. Используйте CSV файлы или установите: pip install pandas openpyxl")
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
            if pd.isna(row.get('user_id')):
                continue
            user_id = int(row['user_id'])
            group_name = None
            if pd.notna(row.get('group_name')):
                group_name = str(row.get('group_name')).strip()
            elif pd.notna(row.get('subject')):
                group_name = str(row.get('subject')).strip()
            elif pd.notna(row.get('class_level')):
                group_name = str(row.get('class_level')).strip()
            full_name = str(row['full_name'])
            username = str(row.get('username', '')) if pd.notna(row.get('username')) else ''
            first_name = str(row.get('first_name', '')) if pd.notna(row.get('first_name')) else ''
            last_name = str(row.get('last_name', '')) if pd.notna(row.get('last_name')) else ''
            
            users_data.append((user_id, group_name, full_name, username, first_name, last_name))
        
        await db.bulk_add_users(users_data)
        logger.info(f"✅ Загружено {len(users_data)} учащихся из {excel_file}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке учеников из Excel: {e}", exc_info=True)


async def load_from_excel_schedule(db: Database, excel_file: str):
    """Загрузка расписания из Excel файла"""
    if not PANDAS_AVAILABLE:
        logger.error("pandas не установлен. Используйте CSV файлы или установите: pip install pandas openpyxl")
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
            if pd.isna(row.get('day_of_week')) or pd.isna(row.get('lesson_time')):
                continue
            group_name = None
            if pd.notna(row.get('group_name')):
                group_name = str(row.get('group_name')).strip()
            elif pd.notna(row.get('subject')):
                group_name = str(row.get('subject')).strip()
            day_of_week = str(row['day_of_week']).lower()
            lesson_time = str(row['lesson_time'])
            
            # Если время в формате datetime, конвертируем в строку
            if ':' not in lesson_time and hasattr(row['lesson_time'], 'strftime'):
                lesson_time = row['lesson_time'].strftime('%H:%M')
            
            schedule_data.append((group_name, day_of_week, lesson_time))
        
        await db.bulk_add_schedule(schedule_data)
        logger.info(f"✅ Загружено {len(schedule_data)} занятий из {excel_file}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке расписания из Excel: {e}", exc_info=True)


async def main():
    """
    Главная функция - загружает данные из CSV или Excel файлов
    """
    db = Database()
    await db.init_db()
    
    try:
        logger.info("=" * 50)
        logger.info("Загрузка данных из файлов")
        logger.info("=" * 50)
        
        # Загрузка учеников (пробуем Excel, затем CSV)
        users_excel = 'data/users.xlsx'
        users_csv = 'data/users.csv'
        
        if Path(users_excel).exists():
            logger.info(f"\n📋 Загрузка учеников из {users_excel}...")
            await load_from_excel_users(db, users_excel)
        elif Path(users_csv).exists():
            logger.info(f"\n📋 Загрузка учеников из {users_csv}...")
            await load_from_csv_users(db, users_csv)
        else:
            logger.warning(f"⚠️  Файлы {users_excel} или {users_csv} не найдены.")
            logger.info("Создайте их на основе шаблонов: data/users_template.csv")
        
        # Загрузка расписания (пробуем Excel, затем CSV)
        schedule_excel = 'data/schedule.xlsx'
        schedule_csv = 'data/schedule.csv'
        
        if Path(schedule_excel).exists():
            logger.info(f"\n📅 Загрузка расписания из {schedule_excel}...")
            await load_from_excel_schedule(db, schedule_excel)
        elif Path(schedule_csv).exists():
            logger.info(f"\n📅 Загрузка расписания из {schedule_csv}...")
            await load_from_csv_schedule(db, schedule_csv)
        else:
            logger.warning(f"⚠️  Файлы {schedule_excel} или {schedule_csv} не найдены.")
            logger.info("Создайте их на основе шаблонов: data/schedule_template.csv")
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ Загрузка завершена!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())

