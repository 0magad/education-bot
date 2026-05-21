"""
Скрипт для создания шаблонов CSV с правильной кодировкой для Excel
Запустите этот скрипт, чтобы пересоздать шаблоны с правильной кодировкой UTF-8 с BOM
"""
import csv
from pathlib import Path

# Создаем папку data если её нет
Path('data').mkdir(exist_ok=True)

# Создание шаблона для учащихся
with open('data/users_template.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    # Заголовки
    writer.writerow(['user_id', 'group_name', 'full_name', 'username', 'first_name', 'last_name'])
    # Примеры данных
    writer.writerow([6218121239, 'Основы веб-программирования', 'Иванов Иван Иванович', 'Rkelmx', 'Иван', 'Иванов'])
    writer.writerow([987654321, '3D моделирование', 'Петров Петр Петрович', 'petrov', 'Петр', 'Петров'])
    writer.writerow([111222333, 'VR/AR приложения', 'Сидоров Сидор Сидорович', 'sidorov', 'Сидор', 'Сидоров'])

print("✅ Создан файл: data/users_template.csv")

# Создание шаблона для расписания
with open('data/schedule_template.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    # Заголовки
    writer.writerow(['group_name', 'day_of_week', 'lesson_time'])
    # Примеры данных
    writer.writerow(['Основы веб-программирования', 'вторник', '14:00'])
    writer.writerow(['Основы веб-программирования', 'вторник', '16:30'])
    writer.writerow(['3D моделирование', 'среда', '10:00'])
    writer.writerow(['3D моделирование', 'среда', '12:00'])
    writer.writerow(['VR/AR приложения', 'четверг', '11:00'])

print("✅ Создан файл: data/schedule_template.csv")
print("\n✅ Шаблоны созданы с правильной кодировкой!")
print("Теперь файлы будут правильно открываться в Excel.")
print("\nЧтобы использовать:")
print("1. Скопируйте users_template.csv → users.csv")
print("2. Скопируйте schedule_template.csv → schedule.csv")
print("3. Заполните данные")
print("4. Запустите: python admin_loader.py")

