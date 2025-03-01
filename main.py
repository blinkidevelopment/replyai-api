from fastapi import FastAPI

from app.routers import resposta, trabalho, empresa, usuario, assistente, voz, evolutionapi, digisac, midia, agenda, microsoft, google
from fastapi.middleware.cors import CORSMiddleware
import os


app = FastAPI()

origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(resposta.router, prefix="/resposta", tags=["Respostas"])
app.include_router(trabalho.router, prefix="/trabalho",tags=["Trabalhos"])
app.include_router(empresa.router, prefix="/empresa", tags=["Empresas"])
app.include_router(usuario.router, prefix="/usuario", tags=["Usuarios"])
app.include_router(agenda.router, prefix="/agenda", tags=["Agendas"])
app.include_router(midia.router, prefix="/midia", tags=["Mídias"])
app.include_router(assistente.router, prefix="/assistente", tags=["Assistentes"])
app.include_router(voz.router, prefix="/voz", tags=["Vozes"])
app.include_router(evolutionapi.router, prefix="/evolutionapi", tags=["EvolutionAPI"])
app.include_router(digisac.router, prefix="/digisac", tags=["Digisac"])
app.include_router(microsoft.router, prefix="/microsoft", tags=["Microsoft"])
app.include_router(google.router, prefix="/google", tags=["Google"])
