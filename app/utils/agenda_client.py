from abc import ABC, abstractmethod

from app.utils.assistant import RespostaTituloAgenda, RespostaTituloAgendaDataNova


class AgendaClient(ABC):
    @abstractmethod
    def obter_horarios(self, **kwargs):
        pass

    @abstractmethod
    def cadastrar_evento(self, **kwargs):
        pass

    @abstractmethod
    def confirmar_evento(self, dados: RespostaTituloAgenda):
        pass

    @abstractmethod
    def reagendar_evento(self, dados: RespostaTituloAgendaDataNova):
        pass

    @abstractmethod
    def cancelar_evento(self, dados: RespostaTituloAgenda, tipo_cancelamento: str):
        pass