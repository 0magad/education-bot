import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QTabWidget, QFileDialog, QMessageBox, QLabel, 
                             QTextEdit, QHeaderView, QGroupBox, QGridLayout,
                             QComboBox, QLineEdit, QProgressBar, QSplitter,
                             QMenuBar, QMenu, QAction, QStatusBar, QToolBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QBrush
import datetime
import os

class ExcelLoaderThread(QThread):
    """Поток для загрузки Excel файлов"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        
    def run(self):
        try:
            # Имитация прогресса загрузки
            self.progress.emit(30)
            
            # Загрузка данных
            if self.file_path.endswith('.csv'):
                df = pd.read_csv(self.file_path)
            else:
                df = pd.read_excel(self.file_path)
                
            self.progress.emit(80)
            
            # Базовая обработка
            df = df.replace([np.inf, -np.inf], np.nan)
            
            self.progress.emit(100)
            self.finished.emit(df)
            
        except Exception as e:
            self.error.emit(str(e))

class ExcelApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_data = None
        self.file_name = ""
        self.loading_thread = None
        self.recent_files = []
        self.initUI()
        self.setup_menu()
        self.setup_statusbar()
        
    def initUI(self):
        self.setWindowTitle("Excel Интеграция v2.0")
        self.setGeometry(100, 100, 1400, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Создаем тулбар
        self.create_toolbar()
        
        # Верхняя панель с информацией
        info_panel = self.create_info_panel()
        main_layout.addWidget(info_panel)
        
        # Основной контент с вкладками
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Вкладка с данными
        self.data_tab = QWidget()
        self.setup_data_tab()
        self.tabs.addTab(self.data_tab, "📊 Данные")
        
        # Вкладка статистики
        self.stats_tab = QWidget()
        self.setup_stats_tab()
        self.tabs.addTab(self.stats_tab, "📈 Статистика")
        
        # Вкладка с отчетами
        self.report_tab = QWidget()
        self.setup_report_tab()
        self.tabs.addTab(self.report_tab, "📋 Отчеты")
        
        main_layout.addWidget(self.tabs)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Статус бар
        self.statusBar().showMessage("Готов к работе")
        
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = QToolBar("Основные операции")
        self.addToolBar(toolbar)
        
        # Кнопка загрузки
        load_action = QAction("📥 Загрузить", self)
        load_action.setStatusTip("Загрузить данные из Excel")
        load_action.triggered.connect(self.load_from_excel)
        toolbar.addAction(load_action)
        
        # Кнопка экспорта
        self.export_action = QAction("📤 Экспорт", self)
        self.export_action.setStatusTip("Экспортировать данные в Excel")
        self.export_action.triggered.connect(self.export_to_excel)
        self.export_action.setEnabled(False)
        toolbar.addAction(self.export_action)
        
        toolbar.addSeparator()
        
        # Кнопка шаблона
        template_action = QAction("📋 Шаблон", self)
        template_action.setStatusTip("Загрузить шаблон данных")
        template_action.triggered.connect(self.load_template)
        toolbar.addAction(template_action)
        
        # Кнопка обновления
        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.setStatusTip("Обновить статистику")
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
    def setup_menu(self):
        """Создание меню приложения"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        open_action = QAction("Открыть...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_from_excel)
        file_menu.addAction(open_action)
        
        save_action = QAction("Сохранить как...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.export_to_excel)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Шаблоны
        template_menu = menubar.addMenu("Шаблоны")
        
        templates = ["Сотрудники", "Продажи", "Склад", "Финансы"]
        for template in templates:
            action = QAction(template, self)
            action.triggered.connect(lambda checked, t=template: self.load_preset_template(t))
            template_menu.addAction(action)
            
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_info_panel(self):
        """Создание информационной панели"""
        panel = QGroupBox("Информация о файле")
        layout = QGridLayout()
        
        self.file_label = QLabel("Файл: не загружен")
        self.file_label.setStyleSheet("color: gray;")
        
        self.dimensions_label = QLabel("Размерность: -")
        self.memory_label = QLabel("Память: -")
        
        layout.addWidget(QLabel("📁"), 0, 0)
        layout.addWidget(self.file_label, 0, 1)
        layout.addWidget(QLabel("📊"), 1, 0)
        layout.addWidget(self.dimensions_label, 1, 1)
        layout.addWidget(QLabel("💾"), 2, 0)
        layout.addWidget(self.memory_label, 2, 1)
        
        panel.setLayout(layout)
        return panel
        
    def setup_statusbar(self):
        """Настройка статус бара"""
        self.status_label = QLabel("Готов")
        self.statusBar().addWidget(self.status_label, 1)
        
        self.time_label = QLabel(datetime.datetime.now().strftime("%H:%M:%S"))
        self.statusBar().addPermanentWidget(self.time_label)
        
        # Таймер для обновления времени
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        
    def setup_data_tab(self):
        """Настройка вкладки с данными"""
        layout = QVBoxLayout(self.data_tab)
        
        # Панель поиска
        search_panel = QHBoxLayout()
        search_panel.addWidget(QLabel("🔍 Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.textChanged.connect(self.search_data)
        search_panel.addWidget(self.search_input)
        
        search_panel.addWidget(QLabel("Колонка:"))
        self.column_combo = QComboBox()
        self.column_combo.addItem("Все колонки")
        search_panel.addWidget(self.column_combo)
        
        layout.addLayout(search_panel)
        
        # Таблица данных
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.table)
        
    def setup_stats_tab(self):
        """Настройка вкладки статистики"""
        layout = QVBoxLayout(self.stats_tab)
        
        # Верхняя панель с общей статистикой
        stats_grid = QGridLayout()
        
        # Карточки с метриками
        self.create_stat_card(stats_grid, "Всего строк", "0", 0, 0)
        self.create_stat_card(stats_grid, "Всего колонок", "0", 0, 1)
        self.create_stat_card(stats_grid, "Пропуски", "0", 1, 0)
        self.create_stat_card(stats_grid, "Уникальных значений", "0", 1, 1)
        
        layout.addLayout(stats_grid)
        
        # Таблица статистики по колонкам
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(6)
        self.stats_table.setHorizontalHeaderLabels([
            "Колонка", "Тип", "Уникальные", "Пропуски", "Минимум", "Максимум"
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(QLabel("Статистика по колонкам:"))
        layout.addWidget(self.stats_table)
        
    def setup_report_tab(self):
        """Настройка вкладки с отчетами"""
        layout = QVBoxLayout(self.report_tab)
        
        # Кнопки управления отчетом
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Очистить отчет")
        clear_btn.clicked.connect(self.clear_report)
        btn_layout.addWidget(clear_btn)
        
        save_report_btn = QPushButton("Сохранить отчет")
        save_report_btn.clicked.connect(self.save_report)
        btn_layout.addWidget(save_report_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Текстовое поле для отчета
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.report_text)
        
    def create_stat_card(self, layout, title, value, row, col):
        """Создание карточки статистики"""
        card = QGroupBox(title)
        card_layout = QVBoxLayout()
        label = QLabel(value)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 16, QFont.Bold))
        card_layout.addWidget(label)
        card.setLayout(card_layout)
        layout.addWidget(card, row, col)
        
        # Сохраняем ссылку на label для обновления
        if not hasattr(self, 'stat_labels'):
            self.stat_labels = {}
        self.stat_labels[title] = label
        
    def load_from_excel(self):
        """Загрузка данных из Excel с прогрессом"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите файл", 
            "", 
            "Excel файлы (*.xlsx *.xls);;CSV файлы (*.csv);;Все файлы (*)"
        )
        
        if not file_path:
            return
            
        self.file_name = os.path.basename(file_path)
        self.file_label.setText(f"Файл: {self.file_name}")
        self.file_label.setStyleSheet("color: green;")
        
        # Показываем прогресс бар
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Запускаем загрузку в отдельном потоке
        self.loading_thread = ExcelLoaderThread(file_path)
        self.loading_thread.progress.connect(self.progress_bar.setValue)
        self.loading_thread.finished.connect(self.on_data_loaded)
        self.loading_thread.error.connect(self.on_load_error)
        self.loading_thread.start()
        
        self.status_label.setText("Загрузка данных...")
        
        # Добавляем в недавние файлы
        if file_path not in self.recent_files:
            self.recent_files.insert(0, file_path)
            if len(self.recent_files) > 5:
                self.recent_files.pop()
                
    def on_data_loaded(self, df):
        """Обработка успешной загрузки данных"""
        self.current_data = df
        self.progress_bar.setVisible(False)
        
        # Заполняем таблицу
        self.populate_table()
        
        # Обновляем статистику
        self.update_statistics()
        
        # Обновляем информацию о файле
        memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
        self.dimensions_label.setText(f"Размерность: {df.shape[0]} строк × {df.shape[1]} колонок")
        self.memory_label.setText(f"Память: {memory_usage:.2f} MB")
        
        # Показываем отчет
        self.show_report(f"✅ Загружен файл: {self.file_name}\n")
        self.show_report(f"📊 Размер данных: {df.shape[0]}×{df.shape[1]}\n")
        self.show_report(f"💾 Занимаемая память: {memory_usage:.2f} MB\n")
        
        # Активируем кнопки
        self.export_action.setEnabled(True)
        
        self.status_label.setText(f"Загружено {df.shape[0]} строк")
        
        # Обновляем список колонок для поиска
        self.update_column_combo()
        
    def on_load_error(self, error_msg):
        """Обработка ошибки загрузки"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{error_msg}")
        self.show_report(f"❌ Ошибка загрузки: {error_msg}\n")
        self.status_label.setText("Ошибка загрузки")
        
    def update_column_combo(self):
        """Обновление списка колонок для поиска"""
        if self.current_data is not None:
            self.column_combo.clear()
            self.column_combo.addItem("Все колонки")
            self.column_combo.addItems(self.current_data.columns)
            
    def populate_table(self):
        """Заполнение таблицы данными"""
        if self.current_data is None:
            return
            
        # Очищаем таблицу
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        
        # Устанавливаем размеры
        rows, cols = self.current_data.shape
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        
        # Устанавливаем заголовки
        self.table.setHorizontalHeaderLabels(self.current_data.columns)
        
        # Заполняем данные
        for i in range(rows):
            for j in range(cols):
                value = self.current_data.iloc[i, j]
                item = QTableWidgetItem(str(value))
                
                # Подсветка пропущенных значений
                if pd.isna(value):
                    item.setBackground(QColor(255, 200, 200))
                    item.setText("<NULL>")
                    
                self.table.setItem(i, j, item)
                
        # Автоматически подгоняем колонки
        self.table.resizeColumnsToContents()
        
    def update_statistics(self):
        """Обновление статистики"""
        if self.current_data is None:
            return
            
        df = self.current_data
        rows, cols = df.shape
        
        # Обновляем карточки
        self.stat_labels["Всего строк"].setText(str(rows))
        self.stat_labels["Всего колонок"].setText(str(cols))
        self.stat_labels["Пропуски"].setText(str(df.isnull().sum().sum()))
        self.stat_labels["Уникальных значений"].setText(str(df.nunique().sum()))
        
        # Обновляем таблицу статистики
        self.stats_table.setRowCount(cols)
        
        for i, col in enumerate(df.columns):
            # Название колонки
            self.stats_table.setItem(i, 0, QTableWidgetItem(str(col)))
            
            # Тип данных
            dtype = str(df[col].dtype)
            self.stats_table.setItem(i, 1, QTableWidgetItem(dtype))
            
            # Уникальные значения
            unique = df[col].nunique()
            self.stats_table.setItem(i, 2, QTableWidgetItem(str(unique)))
            
            # Пропуски
            missing = df[col].isnull().sum()
            missing_pct = (missing/rows*100) if rows > 0 else 0
            missing_item = QTableWidgetItem(f"{missing} ({missing_pct:.1f}%)")
            if missing_pct > 20:
                missing_item.setBackground(QColor(255, 200, 200))
            self.stats_table.setItem(i, 3, missing_item)
            
            # Минимум (для числовых данных)
            if pd.api.types.is_numeric_dtype(df[col]):
                min_val = df[col].min()
                max_val = df[col].max()
                self.stats_table.setItem(i, 4, QTableWidgetItem(str(min_val)))
                self.stats_table.setItem(i, 5, QTableWidgetItem(str(max_val)))
            else:
                self.stats_table.setItem(i, 4, QTableWidgetItem("-"))
                self.stats_table.setItem(i, 5, QTableWidgetItem("-"))
                
    def search_data(self, text):
        """Поиск по данным"""
        if not text or self.current_data is None:
            # Сбрасываем подсветку
            for i in range(self.table.rowCount()):
                for j in range(self.table.columnCount()):
                    item = self.table.item(i, j)
                    if item:
                        item.setBackground(QBrush())
            return
            
        # Подсвечиваем найденные ячейки
        column = self.column_combo.currentIndex() - 1  # -1 для "Все колонки"
        
        for i in range(self.table.rowCount()):
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item:
                    if column == -1 or column == j:
                        if text.lower() in item.text().lower():
                            item.setBackground(QColor(255, 255, 150))
                        else:
                            item.setBackground(QBrush())
                            
    def load_template(self):
        """Загрузка шаблона"""
        template_data = {
            'ID': [1, 2, 3, 4, 5],
            'Имя': ['Иван', 'Мария', 'Петр', 'Анна', 'Сергей'],
            'Возраст': [25, 30, 35, 28, 42],
            'Город': ['Москва', 'СПб', 'Казань', 'Екатеринбург', 'Новосибирск'],
            'Зарплата': [50000, 60000, 70000, 55000, 80000],
            'Дата приема': ['2023-01-15', '2023-02-20', '2023-03-10', '2023-04-05', '2023-05-12']
        }
        
        self.current_data = pd.DataFrame(template_data)
        self.file_name = "шаблон.xlsx"
        self.file_label.setText(f"Файл: {self.file_name}")
        
        self.populate_table()
        self.update_statistics()
        self.update_column_combo()
        
        self.show_report("📋 Загружен шаблон данных\n")
        self.export_action.setEnabled(True)
        self.status_label.setText("Шаблон загружен")
        
    def load_preset_template(self, template_name):
        """Загрузка предустановленного шаблона"""
        templates = {
            "Сотрудники": {
                'Табельный номер': [1001, 1002, 1003],
                'ФИО': ['Иванов И.И.', 'Петров П.П.', 'Сидоров С.С.'],
                'Должность': ['Менеджер', 'Разработчик', 'Аналитик'],
                'Оклад': [50000, 70000, 60000]
            },
            "Продажи": {
                'Дата': ['2024-01-01', '2024-01-02', '2024-01-03'],
                'Товар': ['Ноутбук', 'Мышь', 'Клавиатура'],
                'Количество': [5, 10, 3],
                'Сумма': [250000, 5000, 9000]
            }
        }
        
        if template_name in templates:
            self.current_data = pd.DataFrame(templates[template_name])
            self.file_name = f"{template_name.lower()}_шаблон.xlsx"
            self.file_label.setText(f"Файл: {self.file_name}")
            
            self.populate_table()
            self.update_statistics()
            self.update_column_combo()
            
            self.show_report(f"📋 Загружен шаблон: {template_name}\n")
            self.export_action.setEnabled(True)
            
    def export_to_excel(self):
        """Экспорт данных в Excel"""
        if self.current_data is None:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить как",
            f"export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel файлы (*.xlsx);;CSV файлы (*.csv)"
        )
        
        if not file_path:
            return
            
        try:
            if file_path.endswith('.csv'):
                self.current_data.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                self.current_data.to_excel(file_path, index=False)
                
            QMessageBox.information(self, "Успех", f"Данные сохранены в:\n{file_path}")
            self.show_report(f"💾 Данные экспортированы в {os.path.basename(file_path)}\n")
            self.status_label.setText(f"Сохранено в {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
            
    def refresh_data(self):
        """Обновление данных"""
        if self.current_data is not None:
            self.update_statistics()
            self.show_report("🔄 Статистика обновлена\n")
            self.status_label.setText("Данные обновлены")
            
    def show_report(self, message):
        """Добавление сообщения в отчет"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.report_text.append(formatted_message)
        
    def clear_report(self):
        """Очистка отчета"""
        self.report_text.clear()
        
    def save_report(self):
        """Сохранение отчета в файл"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет",
            f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Текстовые файлы (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.report_text.toPlainText())
                QMessageBox.information(self, "Успех", "Отчет сохранен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчет:\n{str(e)}")
                
    def show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(
            self,
            "О программе",
            "Excel Интеграция v2.0\n\n"
            "Программа для работы с Excel файлами:\n"
            "✓ Загрузка и просмотр данных\n"
            "✓ Статистический анализ\n"
            "✓ Экспорт в различные форматы\n"
            "✓ Поддержка шаблонов\n"
            "✓ Поиск и фильтрация\n\n"
            "© 2024 Все права защищены"
        )
        
    def update_time(self):
        """Обновление времени в статус баре"""
        self.time_label.setText(datetime.datetime.now().strftime("%H:%M:%S"))

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Современный стиль
    
    # Устанавливаем иконку приложения (опционально)
    app.setWindowIcon(QIcon())
    
    window = ExcelApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
