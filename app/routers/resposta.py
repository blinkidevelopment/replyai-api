from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.schemas.digisac_schema import DigisacRequest
from app.schemas.evolutionapi_schema import EvolutionAPIRequest
from app.services.contato_service import obter_criar_contato, mudar_recebimento_ia
from app.services.direcionamento_service import direcionar
from app.services.empresa_service import obter_empresa
from app.services.thread_service import executar_thread
from app.services.mensagem_service import obter_mensagem_audio, enviar_mensagem
from app.db.database import obter_sessao
from app.utils.evolutionapi import EvolutionAPI
from app.utils.rdstation_crm import RDStationCRM

router = APIRouter()

@router.post("/{slug}/{token}")
async def responder(
        request: DigisacRequest | EvolutionAPIRequest,
        slug: str,
        token: str,
        db: Session = Depends(obter_sessao)
):
    try:
        resultado = False

        if isinstance(request, EvolutionAPIRequest):
            if request.data.key.fromMe:
                empresa = (await obter_empresa(slug, token, db))[0]
                await mudar_recebimento_ia(request.data.key.remoteJid, empresa, False, db)
                return resultado

        dados_empresa = await obter_empresa(slug, token, db)
        if dados_empresa is not None:
            empresa, message_client, agenda_client, crm_client = dados_empresa
            contato, assistente, dados_contato = await obter_criar_contato(request, None, empresa, message_client, crm_client, db)

            if not contato.receber_respostas_ia:
                return resultado

            mensagem, audio = await obter_mensagem_audio(request, message_client, assistente)

            if isinstance(message_client, EvolutionAPI):
                message_client.enviar_presenca(request.data.key.remoteJid, audio)

            resposta = await executar_thread(mensagem, contato, dados_contato, assistente, db)
            await direcionar(resposta, audio, message_client, agenda_client, crm_client, empresa, contato, assistente, db)
            resultado = True
        return resultado
    except Exception as e:
        if "AIResponseError" in str(e):
            dados_empresa = await obter_empresa(slug, token, db)
            if dados_empresa is not None:
                empresa, message_client, agenda_client, crm_client = dados_empresa
                contato, assistente, _ = await obter_criar_contato(request, None, empresa, message_client, crm_client, db)
                await enviar_mensagem(empresa.mensagem_erro_ia, False, contato, message_client, assistente, db)
            pass
        return {"erro": str(e)}


@router.post("/rdstation")
async def rdstation_teste():
    crm = RDStationCRM(token="6787ad97b0cd20001b1e61c0",
        user_id="6787a88632a2b50014fcba29",
        deal_stage_id="6787a8af5e6d630018eaef3d",
        deal_source_id="6787a8af5e6d630018eaef30")

    return crm.criar_lead(
        nome_negociacao="Teste Escritório",
        nome_contato="Escritório",
        telefone_contato="5519991030412"
    )