"""
Модуль AI-репетитора для ответов на школьные вопросы и решения задач
Поддерживает бесплатные провайдеры: Groq, Google Gemini и Ollama (локальная модель)
"""
import logging
import re
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Специализация бота: группы/предметы учебного центра
TUTOR_SPECIALIZATION = [
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

# Провайдеры импортируются условно
try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq не установлен. Установите: pip install groq")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI не установлен. Установите: pip install google-generativeai")

try:
    from openai import AsyncOpenAI, RateLimitError, APIError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI не установлен. Установите: pip install openai")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama не установлен. Установите: pip install ollama")


class AITutor:
    """Класс для работы AI-репетитора с поддержкой бесплатных провайдеров"""
    
    def __init__(self, provider: str = 'groq', api_key: str = None, model: str = None, base_url: str = None):
        """
        Инициализация AI-репетитора
        
        Args:
            provider: Провайдер ('groq', 'gemini', 'openai', 'ollama')
            api_key: API ключ (для Groq/OpenAI/Gemini, не требуется для Ollama)
            model: Модель (если не указана, выбирается автоматически)
            base_url: Базовый URL для Ollama (по умолчанию http://localhost:11434)
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or 'http://localhost:11434'
        self.client = None
        self.initialized = False
        
        # Модели по умолчанию для каждого провайдера
        default_models = {
            'groq': 'llama-3.3-70b-versatile',  # Лучшая бесплатная модель Groq
            'gemini': 'gemini-1.5-flash',  # Быстрая и бесплатная модель Gemini
            'openai': 'gpt-4o-mini',
            'ollama': 'llama3.1'  # Локальная модель Ollama
        }
        
        if not self.model:
            self.model = default_models.get(self.provider, default_models['groq'])
        
        # Инициализация в зависимости от провайдера
        if self.provider == 'groq':
            self._init_groq()
        elif self.provider == 'gemini':
            self._init_gemini()
        elif self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'ollama':
            self._init_ollama()
        else:
            logger.warning(f"Неизвестный провайдер: {self.provider}. Попробую Groq...")
            self.provider = 'groq'
            self._init_groq()
    
    def _init_groq(self):
        """Инициализация Groq (бесплатный, быстрый)"""
        if not GROQ_AVAILABLE:
            logger.error("Groq не установлен. Установите: pip install groq")
            return
        
        if not self.api_key:
            logger.warning("Groq API ключ не указан. Получите бесплатный ключ на https://console.groq.com/")
            return
        
        try:
            self.client = AsyncGroq(api_key=self.api_key)
            self.initialized = True
            logger.info(f"Groq инициализирован с моделью {self.model}")
        except Exception as e:
            logger.error(f"Ошибка инициализации Groq: {e}")
    
    def _init_gemini(self):
        """Инициализация Google Gemini (бесплатный)"""
        if not GEMINI_AVAILABLE:
            logger.error("Google Generative AI не установлен. Установите: pip install google-generativeai")
            return
        
        if not self.api_key:
            logger.warning("Gemini API ключ не указан. Получите бесплатный ключ на https://aistudio.google.com/app/apikey")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
            self.initialized = True
            logger.info(f"Google Gemini инициализирован с моделью {self.model}")
        except Exception as e:
            logger.error(f"Ошибка инициализации Gemini: {e}")
    
    def _init_openai(self):
        """Инициализация OpenAI (платный)"""
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI не установлен. Установите: pip install openai")
            return
        
        if not self.api_key:
            logger.warning("OpenAI API ключ не указан")
            return
        
        try:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.initialized = True
            logger.info(f"OpenAI инициализирован с моделью {self.model}")
        except Exception as e:
            logger.error(f"Ошибка инициализации OpenAI: {e}")
    
    def _init_ollama(self):
        """Инициализация Ollama (локальная или удаленная модель)"""
        if not OLLAMA_AVAILABLE:
            logger.error("Ollama не установлен. Установите: pip install ollama")
            return
        
        try:
            # Инициализируем клиент Ollama без синхронной проверки
            # Проверка доступности будет выполнена при первом запросе
            self.client = ollama
            self.initialized = True
            
            # Определяем, это локальное или удаленное подключение
            is_local = 'localhost' in self.base_url or '127.0.0.1' in self.base_url
            connection_type = "локальный" if is_local else "удаленный"
            
            logger.info(f"Ollama инициализирован ({connection_type}) с моделью {self.model} на {self.base_url}")
            
            if is_local:
                logger.info("⚠️  Убедитесь, что Ollama запущен: ollama serve")
                logger.info(f"⚠️  И что модель установлена: ollama pull {self.model}")
            else:
                logger.info(f"⚠️  Подключение к удаленному Ollama серверу: {self.base_url}")
                logger.info(f"⚠️  Убедитесь, что сервер доступен и модель {self.model} установлена")
                logger.info("📖 Инструкция по настройке: см. REMOTE_OLLAMA_SETUP.md")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации Ollama: {e}")
            is_local = 'localhost' in self.base_url or '127.0.0.1' in self.base_url
            if is_local:
                logger.error("Убедитесь, что Ollama установлен и запущен: ollama serve")
            else:
                logger.error(f"Не удалось подключиться к удаленному Ollama серверу: {self.base_url}")
                logger.error("Проверьте:")
                logger.error("1. Что сервер запущен и доступен по сети")
                logger.error("2. Что порт 11434 открыт в файрволе")
                logger.error("3. Что IP-адрес указан правильно")
                logger.error("📖 Подробная инструкция: REMOTE_OLLAMA_SETUP.md")
    
    def _is_math_question(self, question: str) -> bool:
        """Проверка, является ли вопрос математическим"""
        math_keywords = [
            'реши', 'решить', 'вычисли', 'вычислить', 'посчитай', 'посчитать',
            'пример', 'задача', 'уравнение', 'формула', 'математика',
            'алгебра', 'геометрия', 'дробь', 'процент', 'площадь', 'объем',
            '+', '-', '*', '/', '=', 'x', 'y', '^', '√', '∫', '∑'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in math_keywords)
    
    def _extract_math_expression(self, question: str) -> Optional[str]:
        """Извлечение математического выражения из вопроса"""
        patterns = [
            r'(?:реши|решить|вычисли|вычислить|посчитай|посчитать)\s+([0-9+\-*/().\s]+)',
            r'([0-9]+\s*[+\-*/]\s*[0-9]+(?:\s*[+\-*/]\s*[0-9]+)*)',
            r'([0-9]+\s*=\s*[0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _get_specialization(self) -> list:
        """Получить список специализаций из конфига или TUTOR_SPECIALIZATION по умолчанию."""
        try:
            from config import Config
            spec = Config.load_organization_config().get('features', {}).get('tutor', {}).get('specialization', [])
            if spec:
                return spec
        except Exception:
            pass
        return TUTOR_SPECIALIZATION

    def _create_system_prompt(self, user_group: Optional[str] = None) -> str:
        """Создание системного промпта для AI"""
        specialization = self._get_specialization()
        base_prompt = f"""Ты - опытный репетитор и помощник образовательного центра. Твоя специализация — следующие направления:
{chr(10).join('- ' + s for s in specialization)}

Ты помогаешь учащимся именно по этим предметам и темам. Отвечай развёрнуто, но по существу. Если вопрос вне твоей специализации, вежливо предложи сформулировать его в рамках одного из направлений выше.

Основные принципы:
1. Объясняй материал понятно и доступно
2. Для задач и примеров — показывай пошаговое решение
3. Задавай наводящие вопросы, чтобы ученик сам пришёл к ответу
4. Используй примеры из практики
5. Будь дружелюбным и поддерживающим

Формат ответов:
- Для задач: покажи пошаговое решение
- Для вопросов: дай развёрнутый, но понятный ответ
- Используй эмодзи для визуального разделения (📝, ✅, 💡, 📚)
- Без ссылок на видео и внешние ресурсы в конце ответа"""
        
        if user_group:
            base_prompt += f"\n\nУчащийся занимается в группе «{user_group}». Учитывай контекст этой группы при ответе."
        
        return base_prompt
    
    @staticmethod
    def _build_messages(system_prompt: str, user_message: str, history=None) -> list:
        """Собрать список сообщений для API с учётом истории диалога."""
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for turn in history:
                messages.append({"role": "user", "content": turn['message']})
                messages.append({"role": "assistant", "content": turn['response']})
        messages.append({"role": "user", "content": user_message})
        return messages

    async def _call_groq(self, system_prompt: str, user_message: str, history=None) -> str:
        """Вызов Groq API"""
        try:
            messages = self._build_messages(system_prompt, user_message, history)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ошибка Groq API: {e}")
            raise
    
    async def _call_gemini(self, system_prompt: str, user_message: str, history=None) -> str:
        """Вызов Google Gemini API (не поддерживает roles напрямую — история добавляется в промпт)."""
        try:
            full_prompt = system_prompt
            if history:
                full_prompt += "\n\nИстория диалога:\n"
                for turn in history:
                    full_prompt += f"Пользователь: {turn['message']}\nАссистент: {turn['response']}\n"
            full_prompt += f"\nВопрос ученика: {user_message}"
            response = await self.client.generate_content_async(full_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Ошибка Gemini API: {e}")
            raise
    
    async def _call_openai(self, system_prompt: str, user_message: str, history=None) -> str:
        """Вызов OpenAI API"""
        try:
            messages = self._build_messages(system_prompt, user_message, history)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ошибка OpenAI API: {e}")
            raise
    
    async def _call_ollama(self, system_prompt: str, user_message: str, history=None) -> str:
        """Вызов Ollama API (локальная модель)"""
        # Собираем список сообщений один раз — используется в обоих путях (HTTP и sync Client)
        ollama_messages = self._build_messages(system_prompt, user_message, history)

        try:
            import asyncio
            import aiohttp
            import json

            # Пробуем использовать прямой HTTP запрос через aiohttp (полностью асинхронный)
            try:
                logger.info(f"Подключение к Ollama через HTTP: {self.base_url}, модель: {self.model}")

                async with aiohttp.ClientSession() as session:
                    # Формируем запрос к Ollama API
                    url = f"{self.base_url}/api/chat"
                    payload = {
                        "model": self.model,
                        "messages": ollama_messages,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 2000
                        },
                        "stream": False
                    }
                    
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                        if response.status == 200:
                            data = await response.json()
                            answer = data.get('message', {}).get('content', '').strip()
                            logger.info(f"Ollama успешно ответил через HTTP (длина: {len(answer)} символов)")
                            return answer
                        elif response.status == 503:
                            error_text = await response.text()
                            logger.error(f"Ollama вернул 503: {error_text}")
                            raise ConnectionError(
                                f"❌ Модель '{self.model}' не установлена или не загружена.\n\n"
                                f"📋 Что нужно сделать:\n"
                                f"1. Откройте терминал/командную строку\n"
                                f"2. Выполните команду: `ollama pull {self.model}`\n"
                                f"3. Дождитесь завершения загрузки модели\n"
                                f"4. Попробуйте снова отправить сообщение боту\n\n"
                                f"💡 Проверить установленные модели: `ollama list`"
                            )
                        else:
                            error_text = await response.text()
                            logger.error(f"Ollama вернул ошибку {response.status}: {error_text}")
                            raise Exception(f"HTTP {response.status}: {error_text}")
            except ConnectionError:
                # Пробрасываем ConnectionError дальше
                raise
            except Exception as http_error:
                logger.warning(f"HTTP запрос не удался: {http_error}, пробуем через Client")
                # Если HTTP запрос не сработал, пробуем через Client
                pass
            
            # Альтернативный вариант через синхронный Client в executor
            def call_ollama_sync():
                # Используем Client - он принимает полный URL с протоколом
                from ollama import Client
                
                # Client принимает host в формате полного URL: "http://localhost:11434"
                # Используем base_url напрямую
                logger.info(f"Подключение к Ollama: {self.base_url}, модель: {self.model}")
                client = Client(host=self.base_url)
                
                # Проверяем доступные модели (для отладки)
                model_to_use = self.model
                try:
                    models = client.list()
                    available_models = [m['name'] for m in models.get('models', [])]
                    logger.info(f"Доступные модели Ollama: {', '.join(available_models) if available_models else 'нет моделей'}")
                    
                    # Если указанная модель не найдена, пытаемся найти похожую
                    if model_to_use not in available_models:
                        # Пробуем найти модель с похожим именем
                        for available_model in available_models:
                            if 'llama3.1' in available_model.lower() or 'llama3' in available_model.lower():
                                model_to_use = available_model
                                logger.warning(f"Модель {self.model} не найдена, используем {model_to_use}")
                                break
                        else:
                            if available_models:
                                model_to_use = available_models[0]
                                logger.warning(f"Модель {self.model} не найдена, используем первую доступную: {model_to_use}")
                            else:
                                # Нет доступных моделей - это критическая ошибка
                                raise ConnectionError(
                                    f"❌ Нет установленных моделей Ollama.\n\n"
                                    f"📋 Установите модель:\n"
                                    f"`ollama pull {self.model}`"
                                )
                    else:
                        model_to_use = self.model
                except ConnectionError:
                    # Пробрасываем ConnectionError дальше
                    raise
                except Exception as e:
                    error_str = str(e)
                    # Если это 503 при получении списка моделей, значит модель не установлена
                    if '503' in error_str or 'status code: 503' in error_str:
                        logger.warning(f"Ошибка 503 при получении списка моделей - модель {self.model} вероятно не установлена")
                        # Продолжаем попытку использовать модель, но ошибка возникнет при запросе
                    else:
                        logger.warning(f"Не удалось получить список моделей: {e}, используем модель {self.model}")
                
                logger.info(f"Отправка запроса к модели {model_to_use}")
                response = client.chat(
                    model=model_to_use,
                    messages=ollama_messages,
                    options={
                        "temperature": 0.7,
                        "num_predict": 2000
                    }
                )
                logger.info(f"Получен ответ от Ollama, длина: {len(response.get('message', {}).get('content', ''))} символов")
                return response['message']['content'].strip()
            
            # Выполняем синхронный вызов в executor для асинхронности
            # В асинхронном контексте всегда должен быть running loop
            loop = asyncio.get_running_loop()
            answer = await loop.run_in_executor(None, call_ollama_sync)
            logger.info(f"Ollama успешно ответил (длина: {len(answer)} символов)")
            return answer
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Ошибка Ollama API ({error_type}): {error_msg}")
            
            # Обрабатываем ResponseError от ollama
            status_code = None
            # Пытаемся получить статус код из атрибута ошибки
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            # Или извлекаем из строки ошибки
            if not status_code:
                # Ищем паттерны типа "status code: 503" или "(status code: 503)"
                import re
                match = re.search(r'status code:\s*(\d+)', error_msg, re.IGNORECASE)
                if match:
                    try:
                        status_code = int(match.group(1))
                    except:
                        pass
                # Если не нашли, проверяем наличие 503 в сообщении
                if not status_code and ('503' in error_msg or 'service unavailable' in error_msg.lower()):
                    status_code = 503
            
            # Если это ResponseError или есть статус код, обрабатываем специально
            if status_code or (error_type == 'ResponseError' or 'ResponseError' in error_msg):
                is_local = 'localhost' in self.base_url or '127.0.0.1' in self.base_url
                if status_code == 503:
                    # Ошибка 503 обычно означает, что модель не установлена или не загружена
                    if is_local:
                        raise ConnectionError(
                            f"❌ Модель '{self.model}' не установлена или не загружена.\n\n"
                            f"📋 Что нужно сделать:\n"
                            f"1. Откройте терминал/командную строку\n"
                            f"2. Выполните команду: `ollama pull {self.model}`\n"
                            f"3. Дождитесь завершения загрузки модели\n"
                            f"4. Попробуйте снова отправить сообщение боту\n\n"
                            f"💡 Проверить установленные модели: `ollama list`\n"
                            f"💡 Если модель уже установлена, попробуйте перезапустить Ollama"
                        )
                    else:
                        raise ConnectionError(
                            f"❌ Модель '{self.model}' не установлена на удаленном сервере {self.base_url}.\n\n"
                            f"📋 Что нужно сделать на удаленном компьютере:\n"
                            f"1. Откройте терминал/командную строку на компьютере с Ollama\n"
                            f"2. Выполните команду: `ollama pull {self.model}`\n"
                            f"3. Дождитесь завершения загрузки модели\n"
                            f"4. Попробуйте снова отправить сообщение боту\n\n"
                            f"💡 Проверить установленные модели: `ollama list`\n"
                            f"💡 Если модель уже установлена, попробуйте перезапустить Ollama на сервере"
                        )
                elif status_code == 404:
                    if is_local:
                        raise ConnectionError(
                            f"Модель {self.model} не найдена.\n\n"
                            f"Установите модель: `ollama pull {self.model}`"
                        )
                    else:
                        raise ConnectionError(
                            f"Модель {self.model} не найдена на удаленном сервере {self.base_url}.\n\n"
                            f"Установите модель на удаленном компьютере: `ollama pull {self.model}`"
                        )
                elif status_code:
                    raise ConnectionError(
                        f"Ошибка Ollama сервера (код {status_code}): {error_msg}\n\n"
                        f"Проверьте, что Ollama запущен и модель {self.model} установлена."
                    )
                else:
                    # ResponseError без известного статус кода
                    raise ConnectionError(
                        f"Ошибка Ollama API: {error_msg}\n\n"
                        f"Проверьте:\n"
                        f"1. Что Ollama запущен: `ollama serve`\n"
                        f"2. Что модель установлена: `ollama pull {self.model}`"
                    )
            
            # Проверяем, связана ли ошибка с недоступностью сервера
            is_local = 'localhost' in self.base_url or '127.0.0.1' in self.base_url
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "cannot connect" in error_msg.lower():
                if is_local:
                    raise ConnectionError(
                        f"❌ Ollama сервер недоступен по адресу {self.base_url}.\n\n"
                        "📋 Что нужно сделать:\n"
                        "1. Убедитесь, что Ollama запущен: `ollama serve`\n"
                        "2. Проверьте, что порт 11434 не занят другим приложением"
                    )
                else:
                    raise ConnectionError(
                        f"❌ Не удалось подключиться к удаленному Ollama серверу: {self.base_url}\n\n"
                        "📋 Проверьте:\n"
                        "1. Что Ollama запущен на удаленном компьютере\n"
                        "2. Что Ollama настроен для работы по сети (OLLAMA_HOST=0.0.0.0:11434)\n"
                        "3. Что порт 11434 открыт в файрволе на удаленном компьютере\n"
                        "4. Что IP-адрес указан правильно в .env файле\n"
                        "5. Что ноутбук и компьютер в одной сети\n\n"
                        "📖 Подробная инструкция: REMOTE_OLLAMA_SETUP.md"
                    )
            raise
    
    async def process_question(
        self,
        question: str,
        user_context: Optional[Dict] = None,
        history: Optional[list] = None,
        raise_on_error: bool = False
    ) -> str:
        """
        Обработка вопроса пользователя.

        Args:
            question: Вопрос пользователя
            user_context: Контекст пользователя (группа, имя и т.д.)
            history: Список предыдущих пар {'message': ..., 'response': ...}
            raise_on_error: Если True — пробрасывает исключение при ошибке AI,
                            вместо возврата строки с ошибкой (нужно для fallback).
        Returns:
            Ответ репетитора
        """
        if not self.initialized or not self.client:
            if raise_on_error:
                raise RuntimeError(f"AI провайдер '{self.provider}' не инициализирован")
            if self.provider == 'ollama':
                is_local = 'localhost' in self.base_url or '127.0.0.1' in self.base_url
                if is_local:
                    return (
                        "🤖 AI-репетитор временно недоступен.\n\n"
                        f"Провайдер: {self.provider} (локальный)\n"
                        f"Адрес: {self.base_url}\n\n"
                        "Убедитесь, что Ollama запущен: ollama serve\n"
                        f"И что модель {self.model} установлена: ollama pull {self.model}"
                    )
                else:
                    return (
                        "🤖 AI-репетитор временно недоступен.\n\n"
                        f"Провайдер: {self.provider} (удалённый)\n"
                        f"Адрес сервера: {self.base_url}\n\n"
                        "Проверьте:\n"
                        "1. Что Ollama запущен на удалённом компьютере\n"
                        "2. Что сервер доступен по сети\n"
                        f"3. Что модель {self.model} установлена на сервере\n\n"
                        "📖 Инструкция: REMOTE_OLLAMA_SETUP.md"
                    )
            else:
                return (
                    "🤖 AI-репетитор временно недоступен.\n\n"
                    f"Провайдер: {self.provider}\n"
                    "Для работы AI-репетитора необходимо настроить API ключ.\n"
                    "См. инструкцию: FREE_AI_SETUP.md"
                )
        
        if not question or not question.strip():
            return "Пожалуйста, задай свой вопрос! 📚"

        try:
            import asyncio as _asyncio

            # Контекст пользователя
            user_group = user_context.get('group_name') if user_context else None

            # Системный промпт
            system_prompt = self._create_system_prompt(user_group)

            # Доп. контекст для математических задач
            is_math = self._is_math_question(question)
            user_message = question
            if is_math:
                math_expr = self._extract_math_expression(question)
                if math_expr:
                    user_message = f"{question}\n\nПокажи пошаговое решение."

            # Параметры повторных попыток (только для Ollama, 5.4)
            try:
                from config import Config
                tutor_cfg = Config.load_organization_config().get('features', {}).get('tutor', {})
                max_retries = int(tutor_cfg.get('ollama_retries', 2)) if self.provider == 'ollama' else 0
                retry_delay = float(tutor_cfg.get('ollama_retry_delay', 3))
            except Exception:
                max_retries = 2 if self.provider == 'ollama' else 0
                retry_delay = 3.0

            # Вызов API с поддержкой повторных попыток
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    if self.provider == 'groq':
                        answer = await self._call_groq(system_prompt, user_message, history)
                    elif self.provider == 'gemini':
                        answer = await self._call_gemini(system_prompt, user_message, history)
                    elif self.provider == 'openai':
                        answer = await self._call_openai(system_prompt, user_message, history)
                    elif self.provider == 'ollama':
                        answer = await self._call_ollama(system_prompt, user_message, history)
                    else:
                        return "Неизвестный провайдер AI"
                    last_error = None
                    break  # успех — выходим из цикла
                except ConnectionError as e:
                    last_error = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Ollama недоступен (попытка {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Повтор через {retry_delay:.0f}с..."
                        )
                        await _asyncio.sleep(retry_delay)
                    else:
                        raise
            if last_error:
                raise last_error

            # Добавляем префикс для математических задач
            if is_math:
                answer = f"📐 Решение задачи:\n\n{answer}"

            logger.info(f"AI ({self.provider}) ответил на вопрос (длина: {len(answer)} символов)")
            return answer

        except ConnectionError as e:
            logger.error(f"Ошибка подключения к AI ({self.provider}): {e}", exc_info=True)
            if raise_on_error:
                raise
            is_local = 'localhost' in self.base_url or '127.0.0.1' in self.base_url
            error_msg = str(e)
            if "📋" in error_msg or "❌" in error_msg:
                return error_msg
            if is_local:
                return (
                    "🤖 Ошибка подключения к Ollama.\n\n"
                    f"{error_msg}\n\n"
                    "Убедитесь, что:\n"
                    "1. Ollama запущен: `ollama serve`\n"
                    f"2. Модель установлена: `ollama pull {self.model}`\n"
                    f"3. Сервер доступен по адресу: {self.base_url}"
                )
            else:
                return (
                    "🤖 Ошибка подключения к удалённому Ollama серверу.\n\n"
                    f"{error_msg}\n\n"
                    f"Адрес сервера: {self.base_url}\n\n"
                    "Проверьте:\n"
                    "1. Что Ollama запущен на удалённом компьютере\n"
                    "2. Что сервер настроен для работы по сети\n"
                    "3. Что порт 11434 открыт в файрволе\n"
                    "4. Что ноутбук и компьютер в одной сети\n\n"
                    "📖 Подробная инструкция: REMOTE_OLLAMA_SETUP.md"
                )
        except Exception as e:
            logger.error(f"Ошибка при обработке вопроса AI: {e}", exc_info=True)
            if raise_on_error:
                raise
            return (
                "😔 Извини, произошла ошибка при обработке твоего вопроса.\n\n"
                "Попробуй переформулировать вопрос или обратись позже."
            )
    
    async def solve_math_problem(self, problem: str, user_class: Optional[int] = None) -> str:
        """
        Специализированный метод для решения математических задач
        
        Args:
            problem: Текст задачи или математическое выражение
            user_class: Класс ученика
            
        Returns:
            Пошаговое решение задачи
        """
        if not self.initialized or not self.client:
            return "AI-репетитор недоступен. Настройте API ключ."
        
        try:
            system_prompt = f"""Ты - математический репетитор. Решай задачи пошагово, объясняя каждый шаг.

Правила:
1. Покажи все шаги решения
2. Объясни, почему делаешь именно так
3. Проверь ответ
4. Используй понятные обозначения
5. Для формул используй текстовое описание

Уровень ученика: {user_class if user_class else 'не указан'} класс."""
            
            user_prompt = f"Реши эту задачу пошагово:\n\n{problem}"
            
            # Вызываем соответствующий API
            if self.provider == 'groq':
                solution = await self._call_groq(system_prompt, user_prompt)
            elif self.provider == 'gemini':
                solution = await self._call_gemini(system_prompt, user_prompt)
            elif self.provider == 'openai':
                solution = await self._call_openai(system_prompt, user_prompt)
            elif self.provider == 'ollama':
                solution = await self._call_ollama(system_prompt, user_prompt)
            else:
                return "Неизвестный провайдер AI"
            
            return f"📐 Решение:\n\n{solution}"
            
        except Exception as e:
            logger.error(f"Ошибка при решении задачи: {e}", exc_info=True)
            return f"Ошибка при решении задачи: {str(e)}"
