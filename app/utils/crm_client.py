from abc import ABC, abstractmethod


class CRMClient(ABC):
    @abstractmethod
    def criar_lead(self, **kwargs):
        pass

    @abstractmethod
    def mudar_etapa(self, **kwargs):
        pass