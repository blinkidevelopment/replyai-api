from fastapi import FastAPI, Depends

from app.routers import resposta, trabalho
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers.trabalho import verificar_chave_secreta


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
app.include_router(trabalho.router, prefix="/trabalho",tags=["Trabalhos"],
                   dependencies=[Depends(verificar_chave_secreta)])
