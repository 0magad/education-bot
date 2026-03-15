import asyncio
from database import Database


async def test():
    db = Database(db_path='data/bot.db')
    await db.init_db()

    # 1. Добавляем тестовые группы
    await db.upsert_group_topics(
        'Пайтон для начинающих',
        ['python', 'вебинар', 'программирование']
    )
    await db.upsert_group_topics(
        '3D моделирование',
        ['3d', 'blender', 'геймдев']
    )
    print('OK: Группы добавлены')

    # 2. Добавляем событие
    ok = await db.add_event({
        'source': 'timepad',
        'title': 'Python: вебинар для начинающих',
        'url': 'https://timepad.ru/event/99999/',
        'date_start': '2026-05-10T18:00:00',
        'topics': ['python', 'вебинар'],
    })
    print(f'OK: Событие добавлено: {ok}')  # True

    # 3. Проверяем дедупликацию
    ok2 = await db.add_event({
        'source': 'timepad',
        'title': 'Python вебинар (дубль)',
        'url': 'https://timepad.ru/event/99999/',
        'topics': ['python'],
    })
    print(f'OK: Дубль отклонён: {not ok2}')  # True (ok2 == False)

    # 4. Находим группы по темам
    groups = await db.find_matching_groups(['python', 'вебинар'])
    print(f'OK: Найдены группы: {groups}')  # ['Пайтон для начинающих']

    # 5. Проверяем что событие в очереди на рассылку
    events = await db.get_unnotified_events()
    print(f'OK: Событий для рассылки: {len(events)}')  # 1

    # 6. Помечаем как разосланное
    await db.mark_event_notified(events[0]['id'])
    events_after = await db.get_unnotified_events()
    print(f'OK: После пометки: {len(events_after)}')  # 0

    await db.close()
    print()
    print('Все проверки пройдены!')


asyncio.run(test())


