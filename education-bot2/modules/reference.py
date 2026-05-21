"""
Модуль справочника знаний
(Будет реализован позже)
"""
import logging

logger = logging.getLogger(__name__)


class Reference:
    """Класс для работы со справочником"""
    
    def __init__(self, database):
        self.db = database
        
    async def search(self, query: str, subject: str = None):
        """Поиск в справочнике"""
        # TODO: Реализовать поиск по справочнику
        pass
        
    async def get_topic(self, topic_id: int):
        """Получение информации по теме"""
        # TODO: Реализовать получение темы
        pass








