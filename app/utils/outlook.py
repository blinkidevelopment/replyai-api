from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.calendar.get_schedule.get_schedule_request_builder import RequestConfiguration
from msgraph.generated.users.item.calendar.get_schedule.get_schedule_post_request_body import GetSchedulePostRequestBody
from msgraph.generated.models.event import Event
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone

from app.utils.agenda_client import AgendaClient


class Outlook(AgendaClient):
    def __init__(self, clientId: str, tenantId: str, clientSecret: str, duracaoEvento: int, usuarioPadrao: str, horaInicioAgenda: str, horaFinalAgenda: str, timeZone: str):
        credential = ClientSecretCredential(
            tenant_id=tenantId,
            client_id=clientId,
            client_secret=clientSecret
        )
        scopes = ["https://graph.microsoft.com/.default"]

        self.graph_client = GraphServiceClient(credentials=credential, scopes=scopes)
        self.duracao_evento = duracaoEvento
        self.usuario_padrao = usuarioPadrao
        self.hora_inicio_agenda = horaInicioAgenda
        self.hora_final_agenda = horaFinalAgenda
        self.timezone = timeZone

    async def obter_horarios(self, agenda: str, data: str, usuario: str):
        try:
            request_config = RequestConfiguration()

            request_config.headers.try_add("Prefer", f'outlook.timezone="{self.timezone}"')

            request_body = GetSchedulePostRequestBody()
            request_body.schedules = [agenda]
            request_body.start_time = DateTimeTimeZone(date_time=f"{data}T{self.hora_inicio_agenda}", time_zone=self.timezone)
            request_body.end_time = DateTimeTimeZone(date_time=f"{data}T{self.hora_final_agenda}", time_zone=self.timezone)
            request_body.availability_view_interval = self.duracao_evento

            response = await self.graph_client.users.by_user_id(usuario).calendar.get_schedule.post(request_configuration=request_config, body=request_body)

            return RespostaSchedule.from_object(response.value[0])
        except Exception as e:
            return str(e)
    
    async def cadastrar_evento(self, agenda: str, data: str, titulo: str):
        try:
            data_final = datetime.strptime(data, "%Y-%m-%dT%H:%M:%S") + timedelta(minutes=self.duracao_evento)

            request_body = Event()
            request_body.subject = titulo
            request_body.start = DateTimeTimeZone(date_time=f"{data}", time_zone=self.timezone)
            request_body.end = DateTimeTimeZone(date_time=f"{data_final.strftime("%Y-%m-%dT%H:%M:%S")}", time_zone=self.timezone)
            await self.graph_client.users.by_user_id(agenda).events.post(body=request_body)
            return True
        except:
            return False
    

class RespostaSchedule:
    def __init__(self, availability_view: str, schedule_id: str, schedule_items: list):
        self.availability_view = availability_view
        self.schedule_id = schedule_id
        self.schedule_items = schedule_items

    @classmethod
    def from_object(cls, data: object):
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


class Horarios:
    def __init__(self, mapeamento: str):
        self.OitoHoras = mapeamento[0] != '2'
        self.OitoMeiaHoras = mapeamento[1] != '2'
        self.NoveHoras = mapeamento[2] != '2'
        self.NoveMeiaHoras = mapeamento[3] != '2'
        self.DezHoras = mapeamento[4] != '2'
        self.DezMeiaHoras = mapeamento[5] != '2'
        self.OnzeHoras = mapeamento[6] != '2'
        self.OnzeMeiaHoras = mapeamento[7] != '2'
        self.DozeHoras = mapeamento[8] != '2'
        self.DozeMeiaHoras = mapeamento[9] != '2'
        self.TrezeHoras = mapeamento[10] != '2'
        self.TrezeMeiaHoras = mapeamento[11] != '2'
        self.QuatorzeHoras = mapeamento[12] != '2'
        self.QuatorzeMeiaHoras = mapeamento[13] != '2'
        self.QuinzeHoras = mapeamento[14] != '2'
        self.QuinzeMeiaHoras = mapeamento[15] != '2'
        self.DezesseisHoras = mapeamento[16] != '2'
        self.DezesseisMeiaHoras = mapeamento[17] != '2'
        self.DezesseteHoras = mapeamento[18] != '2'
        self.DezesseteMeiaHoras = mapeamento[19] != '2'

    def __str__(self):
        return (
            f"OitoHoras: {self.OitoHoras}, OitoMeiaHoras: {self.OitoMeiaHoras}, "
            f"NoveHoras: {self.NoveHoras}, NoveMeiaHoras: {self.NoveMeiaHoras}, "
            f"DezHoras: {self.DezHoras}, DezMeiaHoras: {self.DezMeiaHoras}, "
            f"OnzeHoras: {self.OnzeHoras}, OnzeMeiaHoras: {self.OnzeMeiaHoras}, "
            f"DozeHoras: {self.DozeHoras}, DozeMeiaHoras: {self.DozeMeiaHoras}, "
            f"TrezeHoras: {self.TrezeHoras}, TrezeMeiaHoras: {self.TrezeMeiaHoras}, "
            f"CatorzeHoras: {self.QuatorzeHoras}, CatorzeMeiaHoras: {self.QuatorzeMeiaHoras}, "
            f"QuinzeHoras: {self.QuinzeHoras}, QuinzeMeiaHoras: {self.QuinzeMeiaHoras}, "
            f"DezesseisHoras: {self.DezesseisHoras}, DezesseisMeiaHoras: {self.DezesseisMeiaHoras}, "
            f"DezesseteHoras: {self.DezesseteHoras}, DezesseteMeiaHoras: {self.DezesseteMeiaHoras}"
        )
