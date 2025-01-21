from datetime import datetime, timedelta

import pytz
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

from app.utils.agenda_client import AgendaClient, Schedule
from app.utils.assistant import RespostaTituloAgenda, RespostaTituloAgendaDataNova


class GoogleCalendar(AgendaClient):
    def __init__(self, project_id: str, private_key_id: str, private_key: str, client_email: str, client_id: str,
                 client_x509_cert_url: str, api_key: str, hora_inicio_agenda: str, hora_final_agenda: str, timezone: str,
                 duracao_evento: int):
        creds = Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": private_key_id,
                "private_key": private_key.replace("\\n", "\n"),
                "client_email": client_email,
                "client_id": client_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": client_x509_cert_url,
                "universe_domain": "googleapis.com"
            },
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        self.api_key = api_key
        self.service = build("calendar", "v3", credentials=creds)
        self.hora_inicio_agenda = hora_inicio_agenda
        self.hora_final_agenda = hora_final_agenda
        self.timezone = pytz.timezone(timezone)
        self.duracao_evento = duracao_evento

    async def obter_horarios(self, agendas: [str], data: str):
        responses = []

        for agenda in agendas:
            response = self.service.events().list(
                calendarId=agenda,
                timeMin=f"{data}T{self.hora_inicio_agenda}Z",
                timeMax=f"{data}T{self.hora_final_agenda}Z"
            ).execute()
            responses.append(response)

        config = {
            "duracao_evento": self.duracao_evento,
            "hora_inicio_agenda": self.hora_inicio_agenda,
            "hora_final_agenda": self.hora_final_agenda,
            "timezone": self.timezone,
            "data_consulta": data
        }

        return [Schedule.from_dict(data=item, config=config) for item in responses]

    async def cadastrar_evento(self, agenda: str, data: str, titulo: str, descricao: str, localizacao: str):
        data = datetime.strptime(data, '%Y-%m-%dT%H:%M:%S').astimezone(self.timezone)
        data_final = data + timedelta(minutes=self.duracao_evento)

        evento = {
            "summary": titulo,
            "start": {
                "dateTime": data.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "timeZone": str(self.timezone)
            },
            "end": {
                "dateTime": data_final.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "timeZone": str(self.timezone)
            }
        }

        if descricao:
            evento["description"] = descricao

        if localizacao:
            evento["location"] = localizacao

        evento_cadastrado = self.service.events().insert(calendarId=agenda, body=evento).execute()
        return evento_cadastrado

    async def confirmar_evento(self, dados: RespostaTituloAgenda):
        try:
            eventos = self.service.events().list(
                calendarId=dados.endereco_agenda,
                q=dados.titulo
            ).execute()

            evento_obj = eventos.get("items")[0] if eventos.get("items") else None

            if evento_obj:
                evento_obj["summary"] = f"CONFIRMADO - {evento_obj["summary"]}"
                self.service.events().update(
                    calendarId=dados.endereco_agenda,
                    eventId=evento_obj["id"],
                    body=evento_obj
                ).execute()
                return True
        except Exception as e:
            print(e)
        return False

    async def reagendar_evento(self, dados: RespostaTituloAgendaDataNova):
        try:
            eventos = self.service.events().list(
                calendarId=dados.endereco_agenda,
                q=dados.titulo
            ).execute()

            evento_obj = eventos.get("items")[0] if eventos.get("items") else None

            if evento_obj:
                data = datetime.strptime(dados.data_nova, '%Y-%m-%dT%H:%M:%S').astimezone(self.timezone)
                data_final = data + timedelta(minutes=self.duracao_evento)

                evento_obj["summary"] = f"REAGENDADO - {evento_obj["summary"]}"
                evento_obj["start"] = {
                    "dateTime": data.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "timeZone": str(self.timezone)
                }
                evento_obj["end"] = {
                    "dateTime": data_final.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "timeZone": str(self.timezone)
                }

                self.service.events().update(
                    calendarId=dados.endereco_agenda,
                    eventId=evento_obj["id"],
                    body=evento_obj
                ).execute()
                return True
        except Exception as e:
            print(e)
        return False

    async def cancelar_evento(self, dados: RespostaTituloAgenda, tipo_cancelamento: str):
        try:
            eventos = self.service.events().list(
                calendarId=dados.endereco_agenda,
                q=dados.titulo
            ).execute()

            evento_obj = eventos.get("items")[0] if eventos.get("items") else None

            if evento_obj:
                if tipo_cancelamento == "excluir":
                    self.service.events().delete(
                        calendarId=dados.endereco_agenda,
                        eventId=evento_obj["id"]
                    ).execute()
                elif tipo_cancelamento == "manter":
                    evento_obj["summary"] = f"CANCELADO - {evento_obj["summary"]}"
                    self.service.events().update(
                        calendarId=dados.endereco_agenda,
                        eventId=evento_obj["id"],
                        body=evento_obj
                    ).execute()
                return True
        except Exception as e:
            print(e)
        return False
