"""
Модуль для планирования и отправки периодических сообщений
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from telegram import Bot
from telegram.error import TelegramError

from config import Config

logger = logging.getLogger(__name__)


class Scheduler:
    """Класс для управления периодическими задачами"""
    
    def __init__(self, database):
        self.db = database
        self.config = Config()
        self.bot: Optional[Bot] = None
        self.running = False
        self.task: Optional[asyncio.Task] = None
        # Отслеживание отправленных уведомлений: {(user_id, schedule_id, date): timestamp}
        self.sent_notifications = {}
        
    async def start(self):
        """Запуск планировщика"""
        self.running = True
        self.task = asyncio.create_task(self._reminder_loop())
        logger.info("Планировщик запущен")
        
    async def stop(self):
        """Остановка планировщика"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Планировщик остановлен")
        
    def set_bot(self, bot: Bot):
        """Установка экземпляра бота"""
        self.bot = bot
        
    async def send_startup_notifications(self):
        """Отправка уведомлений о грядущих занятиях при запуске бота"""
        if not self.bot:
            return
            
        try:
            logger.info("Проверка грядущих занятий при запуске...")
            # Получаем расписание на сегодня для всех групп
            today_schedule = await self.db.get_today_schedule_by_groups()
            
            if not today_schedule:
                logger.info("Нет занятий на сегодня")
                return
                
            current_time = datetime.now()
            today_date = current_time.date()
            sent_count = 0
            
            # Группируем занятия по пользователям для более удобных сообщений
            user_lessons = {}
            
            for group_name, lessons in today_schedule.items():
                students = await self.db.get_students_by_group(group_name)
                if not students:
                    continue

                for lesson in lessons:
                    lesson_time_str = lesson.get('lesson_time', '')
                    schedule_id = lesson.get('schedule_id')

                    try:
                        # Парсим время
                        if ':' in lesson_time_str:
                            time_parts = lesson_time_str.split(':')
                            if len(time_parts) >= 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1].split('.')[0]) if '.' in time_parts[1] else int(time_parts[1])
                                time_display = f"{hour:02d}:{minute:02d}"
                                lesson_hour = hour
                            else:
                                time_display = lesson_time_str[:5] if len(lesson_time_str) >= 5 else lesson_time_str
                                lesson_hour = None
                        else:
                            time_display = lesson_time_str[:5] if len(lesson_time_str) >= 5 else lesson_time_str
                            lesson_hour = None

                        # Проверяем, что занятие еще не прошло
                        if lesson_hour is not None:
                            if lesson_hour < current_time.hour:
                                continue
                            if lesson_hour == current_time.hour and current_time.minute > 30:
                                continue

                        for student in students:
                            user_id = student['user_id']
                            notification_key = (user_id, schedule_id, today_date)
                            
                            # При запуске бота отправляем уведомления, но отмечаем их как отправленные
                            if user_id not in user_lessons:
                                user_lessons[user_id] = []
                            user_lessons[user_id].append({
                                'group_name': group_name,
                                'time': time_display,
                                'schedule_id': schedule_id
                            })
                            
                            # Отмечаем как отправленное, чтобы не дублировать в основном цикле
                            self.sent_notifications[notification_key] = current_time

                    except Exception as e:
                        logger.warning(f"Ошибка при обработке занятия {schedule_id}: {e}")
            
            # Отправляем уведомления каждому пользователю
            for user_id, lessons in user_lessons.items():
                try:
                    if len(lessons) == 1:
                        lesson = lessons[0]
                        message = (
                            f"🤖 Бот запущен!\n\n"
                            f"📚 У тебя сегодня занятие в группе «{lesson['group_name']}» в {lesson['time']}.\n"
                            f"Не забудь подготовиться! ✨"
                        )
                    else:
                        lessons_list = "\n".join([f"⏰ {l['time']} — {l['group_name']}" for l in sorted(lessons, key=lambda x: x['time'])])
                        message = (
                            f"🤖 Бот запущен!\n\n"
                            f"📚 Твои занятия на сегодня:\n\n"
                            f"{lessons_list}\n\n"
                            f"Не забудь подготовиться! ✨"
                        )
                    
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message
                    )
                    
                    sent_count += 1
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Не удалось отправить уведомление при запуске пользователю {user_id}: {e}")
            
            if sent_count > 0:
                logger.info(f"Отправлено {sent_count} уведомлений о грядущих занятиях при запуске")
            else:
                logger.info("Нет грядущих занятий для уведомлений при запуске")
                
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений при запуске: {e}", exc_info=True)
        
    async def _reminder_loop(self):
        """Основной цикл отправки напоминаний"""
        last_general_reminder_time = None
        
        while self.running:
            try:
                # Проверяем расписание на сегодня (часто, для быстрой реакции на изменения)
                await self._check_and_send_schedule_notifications()
                
                # Обычные напоминания отправляем реже (каждые REMINDER_INTERVAL)
                current_time = datetime.now()
                should_send_general = False
                
                if last_general_reminder_time is None:
                    should_send_general = True
                    last_general_reminder_time = current_time
                else:
                    time_since_last = current_time - last_general_reminder_time
                    if time_since_last.total_seconds() >= self.config.REMINDER_INTERVAL:
                        should_send_general = True
                        last_general_reminder_time = current_time
                
                if should_send_general:
                    await self._send_reminders()
                
                # Ждем короткий интервал перед следующей проверкой расписания
                await asyncio.sleep(self.config.SCHEDULE_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле напоминаний: {e}", exc_info=True)
                await asyncio.sleep(1)  # Ждем минуту перед повтором при ошибке
                
    async def _check_and_send_schedule_notifications(self):
        """
        Проверка расписания на сегодня и отправка уведомлений.
        Бот получает расписание по группам и дням недели, затем находит учащихся этих групп.
        Предотвращает дублирование уведомлений.
        """
        if not self.bot:
            return
            
        try:
            # Получаем расписание на сегодня для всех групп
            today_schedule = await self.db.get_today_schedule_by_groups()
            
            if not today_schedule:
                logger.debug("Нет занятий на сегодня для уведомлений")
                return
                
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute
            today_date = current_time.date()
            
            # Очищаем старые записи из кэша (старше 1 дня)
            self._cleanup_old_notifications(today_date)
            
            sent_count = 0
            
            # Для каждой группы получаем расписание и учащихся
            for group_name, lessons in today_schedule.items():
                students = await self.db.get_students_by_group(group_name)
                
                if not students:
                    logger.debug(f"Нет учащихся в группе {group_name}")
                    continue
                
                # Группируем занятия по ученикам
                user_lessons = {}
                
                for lesson in lessons:
                    lesson_time_str = lesson['lesson_time']
                    schedule_id = lesson.get('schedule_id')
                    
                    try:
                        # Парсим время
                        if ':' in lesson_time_str:
                            time_parts = lesson_time_str.split(':')
                            if len(time_parts) >= 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1].split('.')[0]) if '.' in time_parts[1] else int(time_parts[1])
                                time_display = f"{hour:02d}:{minute:02d}"
                                lesson_hour = hour
                                lesson_minute = minute
                            else:
                                time_display = lesson_time_str[:5] if len(lesson_time_str) >= 5 else lesson_time_str
                                lesson_hour = None
                                lesson_minute = None
                        else:
                            time_display = lesson_time_str[:5] if len(lesson_time_str) >= 5 else lesson_time_str
                            lesson_hour = None
                            lesson_minute = None
                        
                        # Определяем, нужно ли отправлять уведомление
                        should_notify = False
                        
                        if lesson_hour is not None:
                            # Проверяем, не прошло ли занятие (больше чем на 30 минут)
                            lesson_datetime = current_time.replace(hour=lesson_hour, minute=lesson_minute or 0, second=0, microsecond=0)
                            time_diff = (lesson_datetime - current_time).total_seconds() / 60  # в минутах
                            
                            if time_diff < -30:
                                # Занятие прошло более 30 минут назад - не уведомляем
                                continue
                            
                            if 7 <= current_hour <= 10:
                                # Утреннее уведомление (7-10 утра) для занятий в этот день
                                if lesson_hour >= current_hour:
                                    should_notify = True
                            elif lesson_hour > current_hour:
                                # Занятие еще не прошло - уведомляем за 1-2 часа до начала
                                time_until_lesson = lesson_hour - current_hour
                                if time_until_lesson == 1 or (time_until_lesson == 2 and current_minute >= 0):
                                    should_notify = True
                            elif lesson_hour == current_hour:
                                # Занятие в этот час - уведомляем если до начала меньше 30 минут
                                if lesson_minute is not None:
                                    if current_minute <= lesson_minute and (lesson_minute - current_minute) <= 30:
                                        should_notify = True
                                else:
                                    should_notify = True
                        else:
                            if 7 <= current_hour <= 10:
                                should_notify = True
                        
                        if not should_notify:
                            continue
                        
                        # Добавляем занятие всем учащимся группы
                        for student in students:
                            user_id = student['user_id']
                            notification_key = (user_id, schedule_id, today_date)
                            
                            # Проверяем, не отправляли ли уже уведомление
                            if notification_key in self.sent_notifications:
                                continue  # Уже отправляли
                            
                            if user_id not in user_lessons:
                                user_lessons[user_id] = []
                            user_lessons[user_id].append({
                                'group_name': group_name,
                                'time': time_display,
                                'schedule_id': schedule_id
                            })
                            
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке занятия: {e}")
                
                # Отправляем уведомления каждому учащемуся группы
                for user_id, lessons_list in user_lessons.items():
                    try:
                        if len(lessons_list) == 1:
                            lesson = lessons_list[0]
                            message = (
                                f"📚 Напоминание!\n\n"
                                f"Сегодня у тебя занятие в группе «{lesson['group_name']}» в {lesson['time']}.\n"
                                f"Не забудь подготовиться! ✨"
                            )
                            # Отмечаем как отправленное
                            notification_key = (user_id, lesson['schedule_id'], today_date)
                            self.sent_notifications[notification_key] = current_time
                        else:
                            # Для нескольких занятий - проверяем каждое отдельно
                            new_lessons = []
                            for l in lessons_list:
                                notification_key = (user_id, l['schedule_id'], today_date)
                                if notification_key not in self.sent_notifications:
                                    new_lessons.append(l)
                                    self.sent_notifications[notification_key] = current_time
                            
                            if not new_lessons:
                                continue  # Все уведомления уже отправлены
                            
                            lessons_text = "\n".join([f"⏰ {l['time']} — {l['group_name']}" for l in sorted(new_lessons, key=lambda x: x['time'])])
                            message = (
                                f"📚 Напоминание о занятиях на сегодня!\n\n"
                                f"{lessons_text}\n\n"
                                f"Не забудь подготовиться! ✨"
                            )
                        
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=message
                        )
                        
                        sent_count += 1
                        await asyncio.sleep(0.1)
                        
                    except TelegramError as e:
                        logger.warning(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}", exc_info=True)
                    
            if sent_count > 0:
                logger.info(f"Отправлено уведомлений о занятиях: {sent_count}")
                
        except Exception as e:
            logger.error(f"Ошибка при проверке расписания: {e}", exc_info=True)
    
    def _cleanup_old_notifications(self, current_date):
        """Очистка старых записей о отправленных уведомлениях"""
        keys_to_remove = [key for key in self.sent_notifications.keys() if key[2] < current_date]
        for key in keys_to_remove:
            del self.sent_notifications[key]
        if keys_to_remove:
            logger.debug(f"Очищено {len(keys_to_remove)} старых записей о уведомлениях")
                
    async def _send_reminders(self):
        """Отправка напоминаний всем пользователям"""
        if not self.bot:
            logger.warning("Бот не установлен, пропуск отправки напоминаний")
            return
            
        users = await self.db.get_all_active_users()
        if not users:
            logger.info("Нет активных пользователей для отправки напоминаний")
            return
            
        current_time = datetime.now()
        sent_count = 0
        
        for user in users:
            user_id = user['user_id']
            
            try:
                # Проверяем, нужно ли отправлять напоминание
                last_reminder = await self.db.get_last_reminder_time(user_id)
                
                if last_reminder:
                    time_since_last = current_time - last_reminder
                    if time_since_last < timedelta(seconds=self.config.REMINDER_INTERVAL):
                        continue  # Еще не прошло достаточно времени
                
                # Отправляем сообщение
                message = self._generate_reminder_message(user)
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
                
                # Обновляем время последнего напоминания
                await self.db.update_last_reminder(user_id)
                sent_count += 1
                
                # Небольшая задержка между отправками
                await asyncio.sleep(0.1)
                
            except TelegramError as e:
                logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            except Exception as e:
                logger.error(f"Ошибка при отправке напоминания пользователю {user_id}: {e}", exc_info=True)
                
        logger.info(f"Отправлено напоминаний: {sent_count} из {len(users)}")
        
    def _generate_reminder_message(self, user: dict) -> str:
        """Генерация текста напоминания"""
        # Здесь можно добавить логику генерации разных сообщений
        messages = [
            "👋 Привет! Не забывай про учебу!",
            "📚 Время для занятий!",
            "💡 Помни, что регулярные занятия - залог успеха!",
            "🎯 Сегодня отличный день для изучения чего-то нового!",
            "✨ Твои знания ждут тебя!",
        ]
        
        # Простой выбор сообщения на основе user_id для разнообразия
        message_index = user['user_id'] % len(messages)
        return messages[message_index]



