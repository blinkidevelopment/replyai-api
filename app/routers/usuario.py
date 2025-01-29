import jwt

from fastapi import APIRouter, Form, HTTPException, Response
from fastapi.params import Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import obter_sessao
from app.db.models import Usuario
from app.utils.password_utils import verificar_senha, criar_token
from app.utils.password_utils import SECRET_KEY, ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuario/login")

async def obter_usuario_logado(token: str = Cookie(None, alias="access_token"), db: Session = Depends(obter_sessao)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=401,
                detail="Não autenticado"
            )
    except:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado"
        )

    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário não encontrado"
        )

    return user


router = APIRouter()

@router.get("/")
async def obter_usuario(usuario_logado: Usuario = Depends(obter_usuario_logado)):
    return usuario_logado

@router.post("/login")
async def login(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(obter_sessao)
):
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not verificar_senha(form_data.password, usuario.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token = criar_token(data={"sub": usuario.email})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none"
    )

    return {"status": True}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return True
