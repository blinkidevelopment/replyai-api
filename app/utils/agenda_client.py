from abc import ABC, abstractmethod


class AgendaClient(ABC):
    @abstractmethod
    def obter_horarios(self, **kwargs):
        pass

    @abstractmethod
    def cadastrar_evento(self, **kwargs):
        pass