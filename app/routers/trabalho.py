import os

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.db.database import obter_sessao
from app.jobs.jobs import retomar_conversa, confirmar_agendamento, avisar_vencimento, cobrar_inadimplentes
from app.jobs.sub_jobs import processar_cobranca, processar_nf
from app.schemas.asaas_schema import AsaasPaymentRequest, AsaasInvoiceRequest
from app.services.cobranca_service import criar_financial_client
from app.services.empresa_service import obter_empresa


def verificar_chave_secreta(request: Request):
    secret_key = os.getenv("SECRET_KEY")
    token = request.headers.get("Secret-Key")

    if not token or secret_key != token:
        raise HTTPException(status_code=403, detail="Chave secreta inválida")


router = APIRouter(dependencies=[Depends(verificar_chave_secreta)])

@router.post("/retomar_conversas")
async def executar_retomar_conversa():
    await retomar_conversa()
    return {"status": "Trabalho [retomar_conversas] executado com sucesso"}

@router.post("/confirmar_agendamentos")
async def executar_confirmar_agendamento(background_tasks: BackgroundTasks):
    background_tasks.add_task(confirmar_agendamento)
    return {"status": "Trabalho [confirmar_agendamentos] iniciado com sucesso"}

@router.post("/avisar_vencimentos")
async def executar_avisar_vencimento(background_tasks: BackgroundTasks):
    background_tasks.add_task(avisar_vencimento)
    return {"status": "Trabalho [avisar_vencimentos] iniciado com sucesso"}

@router.post("/cobrar_inadimplentes")
async def executar_cobrar_inadimplente(background_tasks: BackgroundTasks):
    background_tasks.add_task(cobrar_inadimplentes)
    return {"status": "Trabalho [cobrar_inadimplentes] iniciado com sucesso"}

@router.post("/agradecer_pagamento/asaas/{slug}/{token}/{client_number}")
async def executar_agradecer_pagamento(
        request: AsaasPaymentRequest,
        slug: str,
        token: str,
        client_number: int,
        db: Session = Depends(obter_sessao)
):
    dados_empresa = await obter_empresa(slug, token, db)
    if dados_empresa is not None:
        empresa, message_client, _, __ = dados_empresa
        financial_client = criar_financial_client(empresa, db, client_number)
        await processar_cobranca("extrair_dados_agradecer_pagamento", request.payment.model_dump(), "", False,
                                 empresa, message_client, financial_client, db)
        return {"status": "Trabalho [agradecer_pagamento] executado com sucesso"}

@router.post("/enviar_nf/asaas/{slug}/{token}/{client_number}")
async def executar_enviar_nf(
        request: AsaasInvoiceRequest,
        slug: str,
        token: str,
        client_number: int,
        db: Session = Depends(obter_sessao)
):
    dados_empresa = await obter_empresa(slug, token, db)
    if dados_empresa is not None:
        empresa, message_client, _, __ = dados_empresa
        financial_client = criar_financial_client(empresa, db, client_number)
        await processar_nf("extrair_dados_nf_emitida", request.invoice.model_dump(), "", empresa,
                                 message_client, financial_client, db)
        return {"status": "Trabalho [enviar_nf] executado com sucesso"}
