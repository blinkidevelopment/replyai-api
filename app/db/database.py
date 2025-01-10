from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os


DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def obter_sessao():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def retornar_sessao():
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        print(f"Erro ao criar a sessão: {e}")
        db.close()