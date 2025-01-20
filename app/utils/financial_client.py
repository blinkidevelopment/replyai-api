from abc import ABC, abstractmethod


class FinancialClient(ABC):
    @abstractmethod
    def listar_cobrancas(self, **kwargs):
        pass

    @abstractmethod
    def obter_cliente(self, **kwargs):
        pass