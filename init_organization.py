"""
TASK 3.5: Инициализация организации при первом запуске
Создаёт необходимые конфиги, БД, папки для новой организации
"""
import os
import shutil
import sys
import yaml
from pathlib import Path
from dotenv import dotenv_values, set_key
from datetime import datetime


class OrganizationInitializer:
    """Инициализация новой организации"""
    
    def __init__(self, org_name=None, bot_token=None):
        self.org_name = org_name
        self.bot_token = bot_token
        self.root_dir = Path(__file__).parent
        self.env_file = self.root_dir / '.env'
        self.example_env_file = self.root_dir / '_env.example'
        
    def run(self):
        """Запустить процесс инициализации"""
        print("\n" + "="*60)
        print("🚀 ИНИЦИАЛИЗАЦИЯ НОВОЙ ОРГАНИЗАЦИИ")
        print("="*60)
        
        # Шаг 1: Получить название организации
        if not self.org_name:
            self.org_name = self._prompt_organization_name()
        
        # Шаг 2: Получить токен бота
        if not self.bot_token:
            self.bot_token = self._prompt_bot_token()
        
        # Шаг 3: Создать папки
        self._create_directories()
        
        # Шаг 4: Создать .env файл
        self._create_env_file()
        
        # Шаг 5: Создать organization.yaml с параметрами
        self._create_organization_config()
        
        # Шаг 6: Инициализировать БД
        self._initialize_database()
        
        # Шаг 7: Показать инструкции
        self._show_next_steps()
        
    def _prompt_organization_name(self):
        """Запросить название организации"""
        print("\n📝 Укажите название вашей организации:")
        print("   (например: 'Школа №1' или 'Образовательный центр')")
        name = input("\n>>> ").strip()
        
        if not name:
            print("❌ Название не может быть пустым!")
            return self._prompt_organization_name()
        
        return name
    
    def _prompt_bot_token(self):
        """Запросить токен Telegram бота"""
        print("\n🤖 Укажите токен вашего Telegram бота:")
        print("   (получите у @BotFather в Telegram)")
        print("   Подробнее: https://core.telegram.org/bots/tutorial")
        token = input("\n>>> ").strip()
        
        if not token or ':' not in token:
            print("❌ Токен должен быть в формате: 123456:ABC-DEF...")
            return self._prompt_bot_token()
        
        return token
    
    def _create_directories(self):
        """Создать необходимые папки"""
        print("\n📁 Создание папок...")
        
        directories = [
            'data',
            'data/backups',
            'data/logs',
            'assets',
            'modules'
        ]
        
        for dir_path in directories:
            full_path = self.root_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✓ {dir_path}")
    
    def _create_env_file(self):
        """Создать .env файл из шаблона"""
        print("\n⚙️  Создание файла конфигурации .env...")
        
        if self.env_file.exists():
            print(f"   ⚠️  Файл .env уже существует")
            response = input("   Перезаписать? (y/n): ").strip().lower()
            if response != 'y':
                return
        
        # Прочитать пример
        if self.example_env_file.exists():
            with open(self.example_env_file, 'r', encoding='utf-8') as f:
                example_content = f.read()
        else:
            example_content = self._get_default_env_template()
        
        # Подставить значения
        env_content = example_content
        env_content = env_content.replace(
            'BOT_TOKEN=ваш_токен_бота',
            f'BOT_TOKEN={self.bot_token}'
        )
        env_content = env_content.replace(
            'ORGANIZATION_NAME=YourOrgName',
            f'ORGANIZATION_NAME={self.org_name}'
        )
        
        # Записать файл
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"   ✓ Файл .env создан")
        print(f"   💡 Отредактируйте его для дополнительных настроек")
    
    def _create_organization_config(self):
        """Создать organization.yaml с параметрами организации"""
        print("\n🏢 Создание конфига организации...")
        
        org_config = {
            'organization': {
                'name': self.org_name,
                'description': f'Образовательное учреждение "{self.org_name}"',
                'support_contact': '@support',
                'logo_path': 'assets/logo.png',
                'abbreviation': self._generate_abbreviation(self.org_name),
                'region': '',
                'website': ''
            },
            'groups': {
                'default': [
                    '1A', '1B', '1В',
                    '2A', '2B', '2В',
                    '3A', '3B', '3В',
                    '4A', '4B', '4В'
                ]
            },
            'branding': {
                'primary_color': '#1F77E4',
                'secondary_color': '#25C6DA',
                'emoji': '🎓',
                'greeting_phrase': 'Добро пожаловать в'
            },
            'version': '1.0'
        }
        
        config_file = self.root_dir / 'organization.yaml'
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(org_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"   ✓ Файл organization.yaml создан")
    
    def _initialize_database(self):
        """Инициализировать БД"""
        print("\n🗄️  Инициализация базы данных...")
        
        try:
            from database import Database
            from config import Config
            
            config = Config()
            db = Database(db_path=config.DB_PATH)
            
            # Синхронно инициализируем БД
            import asyncio
            asyncio.run(db.init_db())
            
            print(f"   ✓ База данных инициализирована: {config.DB_PATH}")
            
        except Exception as e:
            print(f"   ⚠️  Не удалось инициализировать БД: {e}")
            print(f"   💡 Это можно сделать позже командой: python -c 'from database import Database; import asyncio; asyncio.run(Database().init_db())'")
    
    def _show_next_steps(self):
        """Показать следующие шаги"""
        print("\n" + "="*60)
        print("✅ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА")
        print("="*60)
        
        print(f"\n🎉 Организация '{self.org_name}' инициализирована!")
        
        print("\n📋 Следующие шаги:")
        print("\n1. 📝 ОТРЕДАКТИРУЙТЕ КОНФИГИ:")
        print("   - .env: добавьте API ключи, настройте AI провайдер")
        print("   - organization.yaml: настройте название, описание, контакт поддержки")
        print("   - groups.yaml (optional): настройте группы (классы)")
        
        print("\n2. 📥 ЗАГРУЗИТЕ ДАННЫЕ:")
        print("   - Учащихся (Excel файл)")
        print("   - Расписание (Excel файл)")
        print("   - Указания для администратора: python admin_loader.py")
        
        print("\n3. 🤖 НАСТРОЙТЕ AI (выберите один вариант):")
        print("   - Бесплатно: Groq.com (быстро, GROQ_API_KEY в .env)")
        print("   - Бесплатно: Google AI Studio (GEMINI_API_KEY в .env)")
        print("   - Локально: Ollama (ollama.ai, запустите: ollama serve)")
        
        print("\n4. 🚀 ЗАПУСТИТЕ БОТА:")
        print("   python bot.py")
        
        print("\n📚 ДОКУМЕНТАЦИЯ:")
        print("   - Полная инструкция: DEPLOYMENT.md")
        print("   - Быстрый старт: QUICK_START_NEW.md")
        print("   - Администрирование: ADMIN_GUIDE.md")
        
        print("\n💬 ПОДДЕРЖКА:")
        print("   - Документация: README.md")
        print("   - GitHub Issues: https://github.com/yourusername/chatbot/issues")
        print("   - Контакт поддержки в .env: SUPPORT_CONTACT")
        
        print("\n" + "="*60 + "\n")
    
    def _generate_abbreviation(self, org_name):
        """Сгенерировать аббревиатуру организации"""
        words = org_name.split()
        abbr = ''.join([w[0] for w in words if w])
        return abbr.upper()[:4]  # Максимум 4 буквы
    
    def _get_default_env_template(self):
        """Получить дефолтный шаблон .env если файл отсутствует"""
        return """# Токен Telegram бота (обязательно)
BOT_TOKEN=ваш_токен_бота

# === TASK 3.1: Organization Config ===
ORGANIZATION_NAME=YourOrgName
ORGANIZATION_DESCRIPTION=Образовательный центр
SUPPORT_CONTACT=@support
LOGO_PATH=assets/logo.png

# Провайдер AI
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
GROQ_API_KEY=
GEMINI_API_KEY=
OPENAI_API_KEY=

# === TASK 3.4: Multi-DB ===
DB_PATH=data/bot.db
DB_PATH_ANALYTICS=

# Логирование
LOG_LEVEL=INFO
"""


def main():
    """Точка входа"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Инициализация новой организации',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python init_organization.py
  python init_organization.py --name "Школа №1" --token "123456:abc..."
        """
    )
    
    parser.add_argument(
        '--name', '-n',
        dest='org_name',
        help='Название организации'
    )
    parser.add_argument(
        '--token', '-t',
        dest='bot_token',
        help='Токен Telegram бота'
    )
    
    args = parser.parse_args()
    
    initializer = OrganizationInitializer(
        org_name=args.org_name,
        bot_token=args.bot_token
    )
    initializer.run()


if __name__ == '__main__':
    main()
