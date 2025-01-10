from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.free_busy_status import FreeBusyStatus
from msgraph.generated.users.item.calendar.get_schedule.get_schedule_request_builder import RequestConfiguration
from msgraph.generated.users.item.calendar.get_schedule.get_schedule_post_request_body import GetSchedulePostRequestBody
from msgraph.generated.users.item.calendar.events.item.calendar.calendar_request_builder import RequestConfiguration as EventsRequestConfiguration
from msgraph.generated.models.event import Event
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone

from app.utils.agenda_client import AgendaClient
from app.utils.assistant import RespostaTituloAgenda, RespostaTituloAgendaDataNova


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

    async def obter_horarios(self, agendas: [str], data: str, usuario: str):
        try:
            request_config = RequestConfiguration()

            request_config.headers.try_add("Prefer", f'outlook.timezone="{self.timezone}"')

            request_body = GetSchedulePostRequestBody()
            request_body.schedules = agendas
            request_body.start_time = DateTimeTimeZone(date_time=f"{data}T{self.hora_inicio_agenda}", time_zone=self.timezone)
            request_body.end_time = DateTimeTimeZone(date_time=f"{data}T{self.hora_final_agenda}", time_zone=self.timezone)
            request_body.availability_view_interval = self.duracao_evento

            response = await self.graph_client.users.by_user_id(usuario).calendar.get_schedule.post(request_configuration=request_config, body=request_body)

            return [RespostaSchedule.from_object(item) for item in response.value]
        except Exception as e:
            print(str(e))
    
    async def cadastrar_evento(self, agenda: str, data: str, titulo: str):
        try:
            data_final = datetime.strptime(data, "%Y-%m-%dT%H:%M:%S") + timedelta(minutes=self.duracao_evento)

            request_body = Event()
            request_body.subject = titulo
            request_body.start = DateTimeTimeZone(date_time=f"{data}", time_zone=self.timezone)
            request_body.end = DateTimeTimeZone(date_time=f"{data_final.strftime("%Y-%m-%dT%H:%M:%S")}", time_zone=self.timezone)
            await self.graph_client.users.by_user_id(agenda).events.post(body=request_body)
            return True
        except Exception as e:
            print(str(e))
            return False

    async def confirmar_evento(self, dados: RespostaTituloAgenda):
        try:
            request_config = EventsRequestConfiguration()
            request_config.query_parameters = {
                "$select": "start,end,subject,id,location",
                "$filter": f"startsWith(subject,'{dados.titulo}')"
            }

            response = await self.graph_client.users.by_user_id(dados.endereco_agenda).events.get(request_configuration=request_config)

            if len(response.value) > 0:
                id = response.value[0].id
                request_body = Event()
                request_body.subject = f"CONFIRMADO - {dados.titulo}"

                await self.graph_client.users.by_user_id(dados.endereco_agenda).events.by_event_id(id).patch(body=request_body)
                return True
        except Exception as e:
            print(str(e))
        return False

    async def reagendar_evento(self, dados: RespostaTituloAgendaDataNova):
        try:
            request_config = EventsRequestConfiguration()
            request_config.query_parameters = {
                "$select": "start,end,subject,id,location",
                "$filter": f"startsWith(subject,'{dados.titulo}')"
            }

            response = await self.graph_client.users.by_user_id(dados.endereco_agenda).events.get(request_configuration=request_config)

            if len(response.value) > 0:
                data_final = datetime.strptime(dados.data_nova, "%Y-%m-%dT%H:%M:%S") + timedelta(minutes=self.duracao_evento)

                id = response.value[0].id
                request_body = Event()
                request_body.subject = f"REAGENDADO - {dados.titulo}"
                request_body.start = DateTimeTimeZone(date_time=f"{dados.data_nova}", time_zone=self.timezone)
                request_body.end = DateTimeTimeZone(date_time=f"{data_final.strftime("%Y-%m-%dT%H:%M:%S")}", time_zone=self.timezone)

                await self.graph_client.users.by_user_id(dados.endereco_agenda).events.by_event_id(id).patch(body=request_body)
                return True
        except Exception as e:
            print(str(e))
        return False

    async def cancelar_evento(self, dados: RespostaTituloAgenda, tipo_cancelamento: str):
        try:
            request_config = EventsRequestConfiguration()
            request_config.query_parameters = {
                "$select": "start,end,subject,id,location",
                "$filter": f"startsWith(subject,'{dados.titulo}')"
            }

            response = await self.graph_client.users.by_user_id(dados.endereco_agenda).events.get(request_configuration=request_config)

            if len(response.value) > 0:
                id = response.value[0].id

                if tipo_cancelamento == "excluir":
                    await self.graph_client.users.by_user_id(dados.endereco_agenda).events.by_event_id(id).delete()
                elif tipo_cancelamento == "manter":
                    request_body = Event()
                    request_body.subject = f"CANCELADO - {dados.titulo}"
                    request_body.show_as = FreeBusyStatus("free")
                    await self.graph_client.users.by_user_id(dados.endereco_agenda).events.by_event_id(id).patch(body=request_body)

                return True
        except Exception as e:
            print(str(e))
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
