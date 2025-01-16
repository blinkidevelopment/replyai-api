from sqlalchemy.orm import Session

from app.db.models import Contato, Empresa, Agenda
from app.services.agendamento_service import extrair_dados_evento, criar_agenda_client
from app.services.contato_service import redefinir_contato, obter_criar_contato, atualizar_thread_contato, \
    atualizar_assistente_atual_contato
from app.services.direcionamento_service import direcionar
from app.services.empresa_service import obter_assistente
from app.services.mensagem_service import criar_message_client
from app.services.thread_service import executar_thread
from app.utils.digisac import Digisac


async def enviar_retomada_conversa(contato: Contato, empresa: Empresa, db: Session):
    assistente, _ = await obter_assistente(empresa, "retomar", None, db)

    if not assistente:
        return

    if contato.recallCount < empresa.recall_quant - 1:
        acao = "retomar_atendimento"
    else:
        acao = "encerrar_conversa"

    message_client = criar_message_client(empresa, db)
    if isinstance(message_client, Digisac):
        ticket_id, last_message_id = message_client.obter_ticket_ultima_mensagem(contato.contactId)
        if ticket_id is None:
            await redefinir_contato(contato, db)
            return
        else:
            if last_message_id is None:
                return
            origem_mensagem = message_client.obter_origem_mensagem(last_message_id)
            if origem_mensagem is None or origem_mensagem == "user":
                await redefinir_contato(contato, db)
                return
    resposta = await executar_thread(acao, contato, None, assistente, db)
    await direcionar(resposta, False, message_client, None, None, empresa, contato, assistente, db)
    contato.recallCount += 1
    db.commit()
    return


async def enviar_confirmacao_consulta(data: str, data_atual: str, empresa: Empresa, db: Session):
    agenda_client = criar_agenda_client(empresa, db)
    agendas = db.query(Agenda).filter_by(id_empresa=empresa.id).all()

    message_client = criar_message_client(empresa, db)
    respostas = await agenda_client.obter_horarios(agendas=[agenda.endereco for agenda in agendas], data=data)

    for resposta in respostas:
        for evento in resposta.schedule_items:
            resposta_extracao, thread_id = await extrair_dados_evento(resposta.schedule_id, evento, data_atual, empresa, db)
            if resposta_extracao:
                if resposta_extracao.telefone:
                    id_contato = message_client.obter_id_contato(resposta_extracao.telefone, resposta_extracao.cliente)
                    contato = (await obter_criar_contato(None, id_contato, empresa, message_client, None, db))[0]
                    assistente, assistente_db_id = await obter_assistente(empresa, "confirmar", None, db)
                    if assistente:
                        if not contato.appointmentConfirmation:
                            contato.appointmentConfirmation = True
                            await atualizar_assistente_atual_contato(contato, assistente_db_id, db)
                        await direcionar(resposta_extracao.resposta_confirmacao, False, message_client, None, None, empresa, contato, assistente, db)
                        await atualizar_thread_contato(contato, thread_id, db)
