from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.jobs.jobs import scheduler
from app.routers import resposta
from fastapi.middleware.cors import CORSMiddleware
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    ativar_scheduler = os.getenv("ACTIVE_SCHEDULER", "False").lower() == "true"

    if ativar_scheduler:
        scheduler.start()
        print("Scheduler ativo")

        try:
            yield
        finally:
            scheduler.shutdown()
            print("Scheduler encerrado")
    else:
        print("Scheduler inativo")
        yield

app = FastAPI(lifespan=lifespan)

origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(resposta.router, prefix="/resposta", tags=["Respostas"])
