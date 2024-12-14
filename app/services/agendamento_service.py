from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session

from app.db.models import Contato, Assistente, Empresa
from app.utils.agenda_client import AgendaClient
from app.utils.assistant import Assistant, Instrucao, DadosData, DadosAgenda, DadosEventoFechado, RespostaDataSugerida, RespostaAgendamento


async def verificar_data_sugerida(
        agenda_client: AgendaClient,
        contact: Contato,
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
        dados=DadosData(
            hoje=hoje_formatado,
            sugestao_inicial=amanha_formatado,
            numero_semana=numero_semana,
            semana_par_impar=semana_par_impar
        )
    )

    assistente_db = db.query(Assistente).filter_by(proposito="agendar", id_empresa=empresa.id).first()

    if assistente_db is not None:
        assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId)
        assistente.adicionar_mensagens(mensagens=[instrucao.__str__()], id_arquivos=[], thread_id=contact.threadId)
        resposta = RespostaDataSugerida.from_dict(assistente.rodar_instrucao_agendar(thread_id=contact.threadId))

        if resposta.tag == "DATA VÁLIDA":
            agenda_disponivel = await agenda_client.obter_horarios(agenda=endereco_agenda, data=resposta.data_sugerida, usuario=agenda_client.usuario_padrao)

            if agenda_disponivel is not None:
                if set(agenda_disponivel.availability_view) == {"2"}:
                    dados_agenda = DadosEventoFechado(
                        titulo=agenda_disponivel.schedule_items[0]["subject"],
                        disponibilidade=agenda_disponivel.availability_view
                    )
                    instrucao.acao = "agenda_fechada"
                else:
                    dados_agenda = DadosAgenda(
                        data_sugerida=resposta.data_sugerida,
                        disponibilidade=agenda_disponivel.availability_view,
                        horario_inicial=agenda_client.hora_inicio_agenda,
                        horario_final=agenda_client.hora_final_agenda,
                        intervalo_tempo=agenda_client.duracao_evento
                    )
                    instrucao.acao = "agenda_disponivel"
                instrucao.dados = dados_agenda
                assistente.adicionar_mensagens(mensagens=[instrucao.__str__()], id_arquivos=[], thread_id=contact.threadId)
                resposta = RespostaDataSugerida.from_dict(assistente.rodar_instrucao_agendar(thread_id=contact.threadId))
                return resposta.mensagem
            return None
        else:
            return resposta.mensagem
    return None


async def cadastrar_evento(
        agenda_client: AgendaClient,
        contact: Contato,
        endereco_agenda: str,
        empresa: Empresa,
        db: Session
):
    timezone = pytz.timezone(empresa.fuso_horario)
    hoje = datetime.now(timezone)
    hoje_formatado = hoje.strftime("%d/%m/%Y, %A")

    instrucao = Instrucao(
        acao="extrair_data_hora_escolhida",
        dados=DadosData(
            hoje=hoje_formatado,
            sugestao_inicial="",
            numero_semana="",
            semana_par_impar=""
        )
    )

    assistente_db = db.query(Assistente).filter_by(proposito="agendar", id_empresa=empresa.id).first()

    if assistente_db is not None:
        assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId)
        assistente.adicionar_mensagens(mensagens=[instrucao.__str__()], id_arquivos=[], thread_id=contact.threadId)
        resposta = RespostaAgendamento.from_dict(assistente.rodar_instrucao_agendar(thread_id=contact.threadId))

        if resposta.tag == "DATA VÁLIDA":
            await agenda_client.cadastrar_evento(agenda=endereco_agenda, data=resposta.data_hora_agendamento, titulo=resposta.titulo_evento)
            return resposta.mensagem
        else:
            return resposta.mensagem
    return None