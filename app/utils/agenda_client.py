from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

import pytz
from msgraph.generated.models.schedule_information import ScheduleInformation

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


class Schedule:
    def __init__(self, availability_view: str, schedule_id: str, schedule_items: list):
        self.availability_view = availability_view
        self.schedule_id = schedule_id
        self.schedule_items = schedule_items

    @classmethod
    def from_object(cls, data: ScheduleInformation):
        schedule_items = [
            {
                "start": {
                    "date_time": item.start.date_time,
                    "time_zone": item.start.time_zone
                },
                "end": {
                    "date_time": item.end.date_time,
                    "time_zone": item.end.time_zone
                },
                "location": item.location,
                "is_private": item.is_private,
                "status": item.status,
                "subject": item.subject
            }
            for item in data.schedule_items
        ]

        return cls(
            availability_view=data.availability_view,
            schedule_id=data.schedule_id,
            schedule_items=schedule_items
        )

    @classmethod
    def from_dict(cls, data: dict, config: dict):
        eventos = [
            {
                "start": {
                    "date_time": item.get("start", {}).get("dateTime", ""),
                    "time_zone": item.get("start", {}).get("timeZone", "")
                },
                "end": {
                    "date_time": item.get("end", {}).get("dateTime", ""),
                    "time_zone": item.get("end", {}).get("timeZone", "")
                },
                "location": item.get("location", ""),
                "is_private": False,
                "status": item.get("status", ""),
                "subject": item.get("summary", "")
            }
            for item in data.get("items", [])
        ]

        availability_view = cls.gerar_availability_view(
            eventos=eventos, intervalo=config.get("duracao_evento"),
            hora_inicio=config.get("hora_inicio_agenda"), hora_final=config.get("hora_final_agenda"),
            timezone=config.get("timezone"), data=config.get("data_consulta")
        )

        return cls(
            availability_view=availability_view,
            schedule_id=data.get("summary", ""),
            schedule_items=eventos
        )

    @staticmethod
    def gerar_availability_view(eventos: List[dict], intervalo: int, hora_inicio: str, hora_final: str, data: str, timezone: pytz.timezone):
        hora_inicio_dt = timezone.localize(datetime.strptime(f"{data} {hora_inicio}", "%Y-%m-%d %H:%M:%S"))
        hora_final_dt = timezone.localize(datetime.strptime(f"{data} {hora_final}", "%Y-%m-%d %H:%M:%S"))

        total_minutos = int((hora_final_dt - hora_inicio_dt).total_seconds() // 60)
        total_blocos = total_minutos // intervalo
        blocks = ["0"] * total_blocos

        for evento in eventos:
            inicio_evento = datetime.fromisoformat(evento["start"]["date_time"])
            fim_evento = datetime.fromisoformat(evento["end"]["date_time"])

            offset = int((inicio_evento - hora_inicio_dt).total_seconds() // 60)
            index_inicial_bloco = offset // intervalo

            duracao_evento = int((fim_evento - inicio_evento).total_seconds() // 60)

            for i in range(index_inicial_bloco, index_inicial_bloco + (duracao_evento // intervalo) + 1):
                if i < total_blocos:
                    blocks[i] = "2"

        return "".join(blocks)