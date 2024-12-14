from fastapi import FastAPI
from app.routers import resposta
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
