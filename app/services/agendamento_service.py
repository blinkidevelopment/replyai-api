from datetime import datetime, timedelta
import pytz
import json
from sqlalchemy.orm import Session

from app.db.models import Contato, Assistente, Empresa, OutlookClient, GoogleCalendarClient
from app.utils.agenda_client import AgendaClient
from app.utils.assistant import Assistant, Instrucao, RespostaDataSugerida, RespostaAgendamento, RespostaConfirmacao, RespostaTituloAgenda, RespostaTituloAgendaDataNova
from app.utils.google_calendar import GoogleCalendar
from app.utils.outlook import Outlook


async def verificar_data_sugerida(
        agenda_client: AgendaClient,
        contato: Contato,
        endereco_agenda: str,
        empresa: Empresa,
        db: Session
):
    timezone = pytz.timezone(empresa.fuso_horario)
    hoje = datetime.now(timezone)
    hoje_formatado = hoje.strftime("%d/%m/%Y, %A")
    amanha = hoje + timedelta(days=1)
    amanha_formatado = amanha.strftime("%d/%m/%Y, %A")
    numero_semana = hoje.strftime("%U")
    semana_par_impar = "PAR" if int(numero_semana) % 2 == 0 else "ÍMPAR"

    instrucao = Instrucao(
        acao="verificar_data_sugerida",
        dados={
            "hoje": hoje_formatado,
            "sugestao_inicial": amanha_formatado,
            "numero_semana": numero_semana,
            "semana_par_impar": semana_par_impar
        }
    )

    assistente_db = db.query(Assistente).filter_by(proposito="agendar", id_empresa=empresa.id).first()

    if assistente_db is not None:
        assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId, api_key=empresa.openai_api_key)
        assistente.adicionar_mensagens(mensagens=[instrucao.__str__()], id_arquivos=[], thread_id=contato.threadId)

        resposta, _ = assistente.criar_rodar_thread(thread_id=contato.threadId)
        resposta = RespostaDataSugerida.from_dict(json.loads(resposta))

        if resposta.tag == "DATA VÁLIDA":
            agendas = await agenda_client.obter_horarios(agendas=[endereco_agenda], data=resposta.data_sugerida)
            if agendas:
                agenda_disponivel = agendas[0]
                if agenda_disponivel is not None:
                    if set(agenda_disponivel.availability_view) == {"2"}:
                        dados_agenda = {
                            "titulo": agenda_disponivel.schedule_items[0]["subject"] or "",
                            "disponibilidade": agenda_disponivel.availability_view or ""
                        }
                        instrucao.acao = "agenda_fechada"
                    else:
                        dados_agenda = {
                            "data_sugerida": resposta.data_sugerida,
                            "disponibilidade": agenda_disponivel.availability_view,
                            "horario_inicial": agenda_client.hora_inicio_agenda,
                            "horario_final": agenda_client.hora_final_agenda,
                            "intervalo_tempo": agenda_client.duracao_evento
                        }
                        instrucao.acao = "agenda_disponivel"
                    instrucao.dados = dados_agenda
                    assistente.adicionar_mensagens(mensagens=[instrucao.__str__()], id_arquivos=[], thread_id=contato.threadId)

                    resposta, _ = assistente.criar_rodar_thread(thread_id=contato.threadId)
                    resposta = RespostaDataSugerida.from_dict(json.loads(resposta))
                    return resposta.mensagem
        else:
            return resposta.mensagem
    return None


async def cadastrar_evento(
        agenda_client: AgendaClient,
        contato: Contato,
        endereco_agenda: str,
        empresa: Empresa,
        db: Session
):
    timezone = pytz.timezone(empresa.fuso_horario)
    hoje = datetime.now(timezone)
    hoje_formatado = hoje.strftime("%d/%m/%Y, %A")

    instrucao = Instrucao(
        acao="extrair_data_hora_escolhida",
        dados={
            "hoje": hoje_formatado
        }
    )

    assistente_db = db.query(Assistente).filter_by(proposito="agendar", id_empresa=empresa.id).first()

    if assistente_db is not None:
        assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId, api_key=empresa.openai_api_key)
        assistente.adicionar_mensagens(mensagens=[instrucao.__str__()], id_arquivos=[], thread_id=contato.threadId)

        resposta, _ = assistente.criar_rodar_thread(thread_id=contato.threadId)
        resposta = RespostaAgendamento.from_dict(json.loads(resposta))

        if resposta.tag == "DATA VÁLIDA":
            await agenda_client.cadastrar_evento(agenda=endereco_agenda, data=resposta.data_hora_agendamento,
                                                 titulo=resposta.titulo_evento, descricao=resposta.descricao,
                                                 localizacao=resposta.localizacao)
            return resposta.mensagem
        else:
            return resposta.mensagem
    return None


async def extrair_dados_evento(
        agenda: str,
        evento: dict,
        data_atual: str,
        empresa: Empresa,
        db: Session
):
    instrucao = Instrucao(
        acao="extrair_dados_evento",
        dados={
            "email_agenda": agenda,
            "titulo": evento.get("subject", ""),
            "local": evento.get("location", ""),
            "data_hora_inicio": evento.get("start").get("date_time"),
            "data_hora_fim": evento.get("end").get("date_time"),
            "data_hora_atual": data_atual
        }
    )

    assistente_db = db.query(Assistente).filter_by(proposito="agendar", id_empresa=empresa.id).first()

    try:
        if assistente_db is not None:
            assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId, api_key=empresa.openai_api_key)
            assistente.adicionar_mensagens(mensagens=[instrucao.__str__()], id_arquivos=[], thread_id=None)
            resposta, thread_id = assistente.criar_rodar_thread()
            resposta_obj = RespostaConfirmacao.from_dict(json.loads(resposta))
            return resposta_obj, thread_id
    except Exception as e:
        print(e)
    return {}, None


async def extrair_titulo_agenda_evento(
        thread_id: str,
        empresa: Empresa,
        db: Session,
        reagendamento: bool = False
):
    instrucao = Instrucao(
        acao="extrair_titulo_agenda_evento" if not reagendamento else "extrair_titulo_agenda_nova_data",
        dados=None
    )

    assistente_db = db.query(Assistente).filter_by(proposito="agendar", id_empresa=empresa.id).first()

    if assistente_db is not None:
        assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId, api_key=empresa.openai_api_key)
        assistente.adicionar_mensagens(mensagens=[instrucao.__str__()], id_arquivos=[], thread_id=thread_id)
        resposta, _ = assistente.criar_rodar_thread(thread_id)

        if reagendamento:
            resposta_obj = RespostaTituloAgendaDataNova.from_dict(json.loads(resposta))
        else:
            resposta_obj = RespostaTituloAgenda.from_dict(json.loads(resposta))
        return resposta_obj
    return None


def criar_agenda_client(empresa: Empresa, db: Session):
    if empresa.agenda_client_type == "outlook":
        outlook_client_db = db.query(OutlookClient).filter_by(id_empresa=empresa.id).first()
        if outlook_client_db:
            return Outlook(
                clientId=outlook_client_db.clientId,
                tenantId=outlook_client_db.tenantId,
                clientSecret=outlook_client_db.clientSecret,
                duracaoEvento=outlook_client_db.duracaoEvento,
                usuarioPadrao=outlook_client_db.usuarioPadrao,
                horaInicioAgenda=outlook_client_db.horaInicioAgenda,
                horaFinalAgenda=outlook_client_db.horaFinalAgenda,
                timeZone=outlook_client_db.timeZone
            )
    elif empresa.agenda_client_type == "google_calendar":
        googlecalendar_client_db = db.query(GoogleCalendarClient).filter_by(id_empresa=empresa.id).first()
        if googlecalendar_client_db:
            return GoogleCalendar(
                project_id=googlecalendar_client_db.project_id,
                private_key_id=googlecalendar_client_db.private_key_id,
                private_key=googlecalendar_client_db.private_key,
                client_email=googlecalendar_client_db.client_email,
                client_id=googlecalendar_client_db.client_id,
                client_x509_cert_url=googlecalendar_client_db.client_x509_cert_url,
                api_key=googlecalendar_client_db.api_key,
                hora_inicio_agenda=googlecalendar_client_db.hora_inicio_agenda,
                hora_final_agenda=googlecalendar_client_db.hora_final_agenda,
                timezone=googlecalendar_client_db.timezone,
                duracao_evento=googlecalendar_client_db.duracao_evento
            )
