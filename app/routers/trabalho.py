import os
from fastapi import APIRouter, Request, HTTPException

from app.jobs.jobs import retomar_conversa, confirmar_agendamento


def verificar_chave_secreta(request: Request):
    secret_key = os.getenv("SECRET_KEY")
    token = request.headers.get("Secret-Key")

    if not token or secret_key != token:
        raise HTTPException(status_code=403, detail="Chave secreta inválida")


router = APIRouter()

@router.post("/retomar_conversas")
async def executar_retomar_conversa():
    await retomar_conversa()
    return {"status": "Trabalho [retomar_conversas] executado com sucesso"}

@router.post("/confirmar_agendamentos")
async def executar_confirmar_agendamento():
    await confirmar_agendamento()
    return {"status": "Trabalho [confirmar_agendamentos] executado com sucesso"}