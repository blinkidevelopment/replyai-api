from sqlalchemy.orm import Session

from app.db.models import Contato, Departamentos, Empresa, Agenda, DigisacClient, Assistente
from app.services.agendamento_service import verificar_data_sugerida, cadastrar_evento
from app.services.mensagem_service import enviar_mensagem
from app.services.thread_service import rodar_criar_thread
from app.utils.agenda_client import AgendaClient
from app.utils.assistant import Resposta, Assistant
from app.utils.digisac import Digisac
from app.utils.message_client import MessageClient


async def direcionar(
        resposta: Resposta,
        audio: bool,
        message_client: MessageClient,
        agenda_client: AgendaClient,
        empresa: Empresa,
        contato: Contato,
        assistente: Assistant,
        db: Session
):
    match resposta.atividade:
        case "R":
            await enviar_mensagem(resposta.mensagem, audio, contato, message_client, assistente, db)
        case "T":
            if isinstance(message_client, Digisac):
                digisac_client_db = db.query(DigisacClient).filter_by(digisacSlug=message_client.slug).first()
                if digisac_client_db is not None:
                    departamento = db.query(Departamentos).filter_by(atalho=resposta.departamento, id_digisac_client=digisac_client_db.id).first()
                    if departamento is not None:
                        await enviar_mensagem(resposta.mensagem, audio, contato, message_client, assistente, db)
                        message_client.transferir(contactId=contato.contactId, departmentId=departamento.departmentId,
                                                  userId=departamento.userId, byUserId=None, comments=departamento.comentario)
        case "E":
            if isinstance(message_client, Digisac):
                await enviar_mensagem(resposta.mensagem, audio, contato, message_client, assistente, db)
                message_client.encerrar_chamado(contactId=contato.contactId, ticketTopicIds=[], comments="", byUserId=None)
                contato.threadId = None
                contato.assistenteAtual = None
                db.commit()
        case "M":
            await enviar_mensagem(resposta.mensagem, audio, contato, message_client, assistente, db)
            assistente_db = db.query(Assistente).filter_by(id_empresa=empresa.id, atalho=resposta.assistente).first()
            if assistente_db is not None:
                assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId)
                resposta_assistente = await rodar_criar_thread("", contato, None, assistente, db)
                contato.assistenteAtual = assistente_db.id
                db.commit()
                await enviar_mensagem(resposta_assistente.mensagem, audio, contato, message_client, assistente, db)
        case "AG":
            agenda = db.query(Agenda).filter_by(atalho=resposta.agenda, id_empresa=empresa.id).first()
            mensagem = await verificar_data_sugerida(agenda_client, contato, agenda.endereco, empresa, db)
            if mensagem is not None:
                await enviar_mensagem(mensagem, audio, contato, message_client, assistente, db)
        case "AG-OK":
            agenda = db.query(Agenda).filter_by(atalho=resposta.agenda, id_empresa=empresa.id).first()
            mensagem = await cadastrar_evento(agenda_client, contato, agenda.endereco, empresa, db)
            if mensagem is not None:
                await enviar_mensagem(mensagem, audio, contato, message_client, assistente, db)
