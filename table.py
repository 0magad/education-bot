import sys
import asyncio
import logging
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                             QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QMessageBox,
                             QLabel, QHeaderView, QTabWidget, QComboBox)
from PyQt5.QtCore import Qt, QTimer
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROUPS = [
    "VR/AR приложения",
    "3D моделирование",
    "Инженерная графика",
    "Основы графического дизайна",
    "Пайтон для начинающих",
    "Архитектура и дизайн",
    "Интеллект-школа. История.9-11 классы",
    "Интеллект школа. Русский язык. (7-8 классы)",
    "Концепт-арт: Создание 3D-персонажа",
    "Основы веб-программирования",
]

DAYS_OF_WEEK = [
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Административная панель - Загрузка данных")
        self.setGeometry(100, 100, 1200, 800)

        # Инициализация базы данных
        self.db = None
        self.db_initialized = False

        # Путь к файлу сохранения
        self.save_file_users = Path('data/table_users.json')
        self.save_file_schedule = Path('data/table_schedule.json')
        for file in [self.save_file_users, self.save_file_schedule]:
            file.parent.mkdir(parents=True, exist_ok=True)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Информационная метка
        info_label = QLabel(
            "📋 Работа в два этапа:\n"
            "1. Вкладка 'Учащиеся': добавьте всех учащихся (User ID, ФИО, Группа)\n"
            "2. Вкладка 'Расписание': добавьте расписание (Группа, День недели, Время)\n"
            "Система автоматически свяжет учащихся с расписанием по группе"
        )
        info_label.setStyleSheet("padding: 10px; background-color: #e7f3ff; border-radius: 5px;")
        layout.addWidget(info_label)

        # Создаем вкладки
        self.tabs = QTabWidget()
        
        # Вкладка 1: Учащиеся
        self.users_tab = QWidget()
        users_layout = QVBoxLayout(self.users_tab)
        
        users_info = QLabel("Добавьте всех учащихся. Для каждого укажите группу и уникальный User ID.")
        users_info.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        users_layout.addWidget(users_info)
        
        self.users_table = QTableWidget()
        self.users_table.setRowCount(50)
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["User ID", "ФИО", "Группа"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        users_layout.addWidget(self.users_table)
        self._ensure_group_widgets_for_all_rows()
        
        # Кнопки для вкладки учеников
        users_buttons = QHBoxLayout()
        self.users_add_row = QPushButton("Добавить строку")
        self.users_add_row.setStyleSheet("background-color: #17a2b8; color: white; padding: 8px; border-radius: 5px;")
        self.users_add_row.clicked.connect(lambda: self.add_row(self.users_table))
        
        self.users_delete = QPushButton("Удалить строку")
        self.users_delete.setStyleSheet("background-color: #dc3545; color: white; padding: 8px; border-radius: 5px;")
        self.users_delete.clicked.connect(lambda: self.delete_selected_row(self.users_table))
        
        self.users_clear = QPushButton("Очистить")
        self.users_clear.setStyleSheet("background-color: #ffc107; color: black; padding: 8px; border-radius: 5px;")
        self.users_clear.clicked.connect(lambda: self.clear_table(self.users_table))
        
        users_buttons.addWidget(self.users_add_row)
        users_buttons.addWidget(self.users_delete)
        users_buttons.addWidget(self.users_clear)
        users_buttons.addStretch()
        users_layout.addLayout(users_buttons)
        
        self.tabs.addTab(self.users_tab, "👥 Учащиеся")
        
        # Вкладка 2: Расписание
        self.schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(self.schedule_tab)
        
        schedule_info = QLabel("Добавьте расписание. Учащиеся автоматически получат расписание своей группы.")
        schedule_info.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        schedule_layout.addWidget(schedule_info)
        
        self.schedule_table = QTableWidget()
        self.schedule_table.setRowCount(100)
        self.schedule_table.setColumnCount(3)
        self.schedule_table.setHorizontalHeaderLabels(["Группа", "День недели", "Время"])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.setAlternatingRowColors(True)
        self.schedule_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        schedule_layout.addWidget(self.schedule_table)
        self._ensure_schedule_widgets_for_all_rows()

        # Кнопки для вкладки расписания
        schedule_buttons = QHBoxLayout()
        self.schedule_add_row = QPushButton("Добавить строку")
        self.schedule_add_row.setStyleSheet("background-color: #17a2b8; color: white; padding: 8px; border-radius: 5px;")
        self.schedule_add_row.clicked.connect(lambda: self.add_row(self.schedule_table))
        
        self.schedule_delete = QPushButton("Удалить строку")
        self.schedule_delete.setStyleSheet("background-color: #dc3545; color: white; padding: 8px; border-radius: 5px;")
        self.schedule_delete.clicked.connect(lambda: self.delete_selected_row(self.schedule_table))
        
        self.schedule_clear = QPushButton("Очистить")
        self.schedule_clear.setStyleSheet("background-color: #ffc107; color: black; padding: 8px; border-radius: 5px;")
        self.schedule_clear.clicked.connect(lambda: self.clear_table(self.schedule_table))
        
        schedule_buttons.addWidget(self.schedule_add_row)
        schedule_buttons.addWidget(self.schedule_delete)
        schedule_buttons.addWidget(self.schedule_clear)
        schedule_buttons.addStretch()
        schedule_layout.addLayout(schedule_buttons)
        
        self.tabs.addTab(self.schedule_tab, "📅 Расписание")
        
        layout.addWidget(self.tabs)

        # Общие кнопки
        button_layout = QHBoxLayout()

        self.button_save = QPushButton("Сохранить")
        self.button_save.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.button_save.clicked.connect(self.save_all_data)

        self.button_add = QPushButton("Загрузить в базу данных")
        self.button_add.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.button_add.clicked.connect(self.load_data_to_database)

        button_layout.addWidget(self.button_save)
        button_layout.addStretch()
        button_layout.addWidget(self.button_add)

        layout.addLayout(button_layout)

        # Статусная метка
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e7f3ff; border-radius: 3px;")
        layout.addWidget(self.status_label)

        # Загружаем сохраненные данные при запуске
        QTimer.singleShot(100, self.load_all_data)

        # Подключаем сигналы изменения данных для автосохранения
        self.users_table.itemChanged.connect(self.auto_save)
        self.schedule_table.itemChanged.connect(self.auto_save)

    def add_row(self, table):
        """Добавление новой строки"""
        current_row_count = table.rowCount()
        table.insertRow(current_row_count)

        if table == self.users_table:
            self._ensure_group_widget(current_row_count)
        elif table == self.schedule_table:
            self._ensure_schedule_row_widgets(current_row_count)

        self.status_label.setText(f"Добавлена строка {current_row_count + 1}")

    def delete_selected_row(self, table):
        """Удаление выбранной строки"""
        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)
            self.status_label.setText(f"Строка {current_row + 1} удалена")
            self.auto_save()
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для удаления")

    def clear_table(self, table):
        """Очистка таблицы"""
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            "Вы уверены, что хотите очистить таблицу?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            table.setRowCount(50 if table == self.users_table else 100)
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        item.setText("")

            if table == self.users_table:
                self._ensure_group_widgets_for_all_rows()
                for row in range(table.rowCount()):
                    combo = self.users_table.cellWidget(row, 2)
                    if isinstance(combo, QComboBox):
                        combo.setCurrentIndex(0)
            elif table == self.schedule_table:
                self._ensure_schedule_widgets_for_all_rows()
                for row in range(table.rowCount()):
                    for col in (0, 1):
                        combo = self.schedule_table.cellWidget(row, col)
                        if isinstance(combo, QComboBox):
                            combo.setCurrentIndex(0)
                    item = self.schedule_table.item(row, 2)
                    if item:
                        item.setText("")

            self.status_label.setText("Таблица очищена")
            self.auto_save()

    def _ensure_group_widgets_for_all_rows(self):
        for row in range(self.users_table.rowCount()):
            self._ensure_group_widget(row)

    def _ensure_group_widget(self, row: int):
        existing = self.users_table.cellWidget(row, 2)
        if isinstance(existing, QComboBox):
            return

        combo = QComboBox()
        combo.addItem("")  # пустое значение
        combo.addItems(GROUPS)
        combo.setEditable(False)
        combo.currentTextChanged.connect(lambda _text: self.auto_save())
        self.users_table.setCellWidget(row, 2, combo)

    def _ensure_schedule_widgets_for_all_rows(self):
        for row in range(self.schedule_table.rowCount()):
            self._ensure_schedule_row_widgets(row)

    def _ensure_schedule_row_widgets(self, row: int):
        """Создаёт выпадающие списки для колонок Группа (0) и День недели (1)."""
        for col, items in [(0, GROUPS), (1, DAYS_OF_WEEK)]:
            existing = self.schedule_table.cellWidget(row, col)
            if isinstance(existing, QComboBox):
                continue
            combo = QComboBox()
            combo.addItem("")
            combo.addItems(items)
            combo.setEditable(False)
            combo.currentTextChanged.connect(lambda _text: self.auto_save())
            self.schedule_table.setCellWidget(row, col, combo)
        # Колонка 2 (Время) остаётся обычной ячейкой — проверяем, что item есть при необходимости
        if self.schedule_table.item(row, 2) is None:
            self.schedule_table.setItem(row, 2, QTableWidgetItem(""))

    def _get_table_cell_text(self, table: QTableWidget, row: int, col: int) -> str:
        widget = table.cellWidget(row, col)
        if isinstance(widget, QComboBox):
            return (widget.currentText() or "").strip()

        item = table.item(row, col)
        return (item.text() if item else "").strip()

    def get_users_data(self):
        """Извлечение данных учащихся из таблицы"""
        users_data = []
        user_map = {}  # Для отслеживания уникальных пользователей

        for row in range(self.users_table.rowCount()):
            user_id_str = self._get_table_cell_text(self.users_table, row, 0)
            full_name = self._get_table_cell_text(self.users_table, row, 1)
            group_name = self._get_table_cell_text(self.users_table, row, 2)

            try:
                if not all([user_id_str, full_name, group_name]):
                    continue

                user_id = int(user_id_str)

                if group_name not in GROUPS:
                    logger.warning(f"Строка {row + 1}: неизвестная группа '{group_name}'")
                    continue

                # Проверяем уникальность user_id
                if user_id in user_map:
                    logger.warning(f"Строка {row + 1}: дублирующийся User ID {user_id}")
                    continue

                user_map[user_id] = True

                # Извлекаем имя и фамилию из ФИО
                name_parts = full_name.split()
                first_name = name_parts[1] if len(name_parts) > 1 else name_parts[0] if name_parts else ''
                last_name = name_parts[0] if name_parts else ''
                username = ''

                users_data.append((user_id, group_name, full_name, username, first_name, last_name))

            except ValueError as e:
                logger.warning(f"Строка {row + 1}: ошибка преобразования данных - {e}")
                continue
            except Exception as e:
                logger.error(f"Строка {row + 1}: ошибка обработки - {e}")
                continue

        return users_data

    def get_schedule_data(self):
        """Извлечение данных расписания из таблицы"""
        schedule_data = []

        for row in range(self.schedule_table.rowCount()):
            group_name = self._get_table_cell_text(self.schedule_table, row, 0)
            day_of_week = self._get_table_cell_text(self.schedule_table, row, 1).lower()
            lesson_time = self._get_table_cell_text(self.schedule_table, row, 2)

            try:
                if not all([group_name, day_of_week, lesson_time]):
                    continue

                if group_name not in GROUPS:
                    logger.warning(f"Строка {row + 1}: неизвестная группа '{group_name}'")
                    continue

                # Валидация дня недели
                if day_of_week not in DAYS_OF_WEEK:
                    logger.warning(f"Строка {row + 1}: неверный день недели '{day_of_week}'")
                    continue

                # Валидация времени (формат HH:MM)
                if ':' not in lesson_time:
                    logger.warning(f"Строка {row + 1}: неверный формат времени '{lesson_time}'")
                    continue

                time_parts = lesson_time.split(':')
                if len(time_parts) != 2:
                    logger.warning(f"Строка {row + 1}: неверный формат времени '{lesson_time}'")
                    continue

                try:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                        logger.warning(f"Строка {row + 1}: неверное время '{lesson_time}'")
                        continue
                except ValueError:
                    logger.warning(f"Строка {row + 1}: неверный формат времени '{lesson_time}'")
                    continue

                schedule_data.append((group_name, day_of_week, lesson_time))

            except ValueError as e:
                logger.warning(f"Строка {row + 1}: ошибка преобразования данных - {e}")
                continue
            except Exception as e:
                logger.error(f"Строка {row + 1}: ошибка обработки - {e}")
                continue

        return schedule_data

    async def load_data_async(self):
        """Асинхронная загрузка данных в базу"""
        try:
            # Инициализация БД
            if not self.db_initialized:
                self.db = Database()
                await self.db.init_db()
                self.db_initialized = True

            # Получаем данные из таблиц
            users_data = self.get_users_data()
            schedule_data = self.get_schedule_data()

            if not users_data and not schedule_data:
                return False, "Таблицы пусты или данные не заполнены"

            if not users_data:
                return False, "Необходимо добавить хотя бы одного ученика"

            if not schedule_data:
                return False, "Необходимо добавить хотя бы одно занятие в расписание"

            # Загружаем данные
            await self.db.bulk_add_users(users_data)
            logger.info(f"Загружено {len(users_data)} учащихся")

            await self.db.bulk_add_schedule(schedule_data)
            logger.info(f"Загружено {len(schedule_data)} занятий")

            # Подсчитываем связи
            group_counts = {}
            for _, group_name, _, _, _, _ in users_data:
                group_counts[group_name] = group_counts.get(group_name, 0) + 1

            schedule_by_group = {}
            for group_name, _, _ in schedule_data:
                schedule_by_group[group_name] = schedule_by_group.get(group_name, 0) + 1

            info_msg = f"Успешно загружено:\n"
            info_msg += f"• {len(users_data)} учащихся\n"
            info_msg += f"• {len(schedule_data)} занятий\n\n"
            info_msg += "Расписание автоматически связано с учащимися по группе:\n"
            for group_name in sorted(group_counts.keys()):
                students = group_counts[group_name]
                lessons = schedule_by_group.get(group_name, 0)
                info_msg += f"• {group_name}: {students} учащихся, {lessons} занятий\n"

            return True, info_msg

        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}", exc_info=True)
            return False, f"Ошибка: {str(e)}"

    def load_data_to_database(self):
        """Загрузка данных в базу данных (синхронная обертка)"""
        self.status_label.setText("Загрузка данных...")
        self.button_add.setEnabled(False)

        try:
            # Запускаем асинхронную функцию
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, message = loop.run_until_complete(self.load_data_async())
            loop.close()

            if success:
                QMessageBox.information(self, "Успех", message)
                self.status_label.setText("✓ Данные успешно загружены")
                self.status_label.setStyleSheet("padding: 5px; background-color: #d4edda; border-radius: 3px; color: #155724;")
            else:
                QMessageBox.warning(self, "Ошибка", message)
                self.status_label.setText(f"✗ {message}")
                self.status_label.setStyleSheet("padding: 5px; background-color: #f8d7da; border-radius: 3px; color: #721c24;")

        except Exception as e:
            error_msg = f"Критическая ошибка: {str(e)}"
            QMessageBox.critical(self, "Ошибка", error_msg)
            self.status_label.setText(f"✗ {error_msg}")
            self.status_label.setStyleSheet("padding: 5px; background-color: #f8d7da; border-radius: 3px; color: #721c24;")
        finally:
            self.button_add.setEnabled(True)

    def save_all_data(self):
        """Сохранение всех данных"""
        try:
            # Сохраняем учеников
            users_data = []
            for row in range(self.users_table.rowCount()):
                row_data = []
                for col in range(self.users_table.columnCount()):
                    row_data.append(self._get_table_cell_text(self.users_table, row, col))
                if any(row_data):
                    users_data.append(row_data)

            with open(self.save_file_users, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, ensure_ascii=False, indent=2)

            # Сохраняем расписание
            schedule_data = []
            for row in range(self.schedule_table.rowCount()):
                row_data = []
                for col in range(self.schedule_table.columnCount()):
                    row_data.append(self._get_table_cell_text(self.schedule_table, row, col))
                if any(row_data):
                    schedule_data.append(row_data)

            with open(self.save_file_schedule, 'w', encoding='utf-8') as f:
                json.dump(schedule_data, f, ensure_ascii=False, indent=2)

            self.status_label.setText("✓ Данные сохранены")
            logger.info("Данные таблиц сохранены")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных: {e}", exc_info=True)
            self.status_label.setText("✗ Ошибка сохранения")
            return False

    def load_all_data(self):
        """Загрузка всех данных из файлов"""
        try:
            # Загружаем учеников
            if self.save_file_users.exists():
                with open(self.save_file_users, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                
                if users_data:
                    self.users_table.setRowCount(max(len(users_data), 50))
                    self._ensure_group_widgets_for_all_rows()
                    for row, row_data in enumerate(users_data):
                        for col, value in enumerate(row_data):
                            if col < self.users_table.columnCount() and value:
                                if col == 2:
                                    combo = self.users_table.cellWidget(row, 2)
                                    if isinstance(combo, QComboBox):
                                        if value not in [""] + GROUPS:
                                            combo.addItem(str(value))
                                        combo.setCurrentText(str(value))
                                else:
                                    item = QTableWidgetItem(str(value))
                                    self.users_table.setItem(row, col, item)
                    logger.info(f"Загружено {len(users_data)} учащихся из сохранения")

            # Загружаем расписание
            if self.save_file_schedule.exists():
                with open(self.save_file_schedule, 'r', encoding='utf-8') as f:
                    schedule_data = json.load(f)
                
                if schedule_data:
                    self.schedule_table.setRowCount(max(len(schedule_data), 100))
                    self._ensure_schedule_widgets_for_all_rows()
                    for row, row_data in enumerate(schedule_data):
                        # Поддержка старого формата: [Класс, Предмет, День недели, Время] -> [Группа, День недели, Время]
                        if isinstance(row_data, list) and len(row_data) >= 4:
                            row_data = [row_data[1], row_data[2], row_data[3]]
                        for col, value in enumerate(row_data):
                            if col < self.schedule_table.columnCount() and value:
                                if col in (0, 1):
                                    combo = self.schedule_table.cellWidget(row, col)
                                    if isinstance(combo, QComboBox):
                                        if str(value) not in ([""] + (GROUPS if col == 0 else DAYS_OF_WEEK)):
                                            combo.addItem(str(value))
                                        combo.setCurrentText(str(value))
                                else:
                                    item = self.schedule_table.item(row, col)
                                    if item is None:
                                        self.schedule_table.setItem(row, col, QTableWidgetItem(str(value)))
                                    else:
                                        item.setText(str(value))
                    logger.info(f"Загружено {len(schedule_data)} занятий из сохранения")

        except json.JSONDecodeError as e:
            logger.warning(f"Ошибка чтения JSON файла: {e}")
            self.status_label.setText("Ошибка загрузки сохраненных данных")
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}", exc_info=True)
            self.status_label.setText("Ошибка загрузки сохраненных данных")

    def auto_save(self):
        """Автоматическое сохранение при изменении данных"""
        try:
            self.save_all_data()
        except:
            pass  # Игнорируем ошибки автосохранения

    def closeEvent(self, event):
        """Закрытие приложения"""
        # Сохраняем данные перед закрытием
        self.save_all_data()
        
        if self.db_initialized and self.db:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.db.close())
            loop.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
