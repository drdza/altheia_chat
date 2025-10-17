from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, Request, Response
from fastapi.security import OAuth2PasswordBearer
from core.config import settings
import logging

log = logging.getLogger(__name__)

SECRET_JWT_KEY = settings.SECRET_JWT_KEY or "super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    log.info(f"Token expire: {expire}")
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_JWT_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_JWT_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def verify_access_token_from_cookie(request: Request) -> str:
    """Verifica si existe cookie con token válido y devuelve el usuario"""
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    payload = decode_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    return {
        "user": payload.get("sub"),
        "username": payload.get("username"),
        "mail": payload.get("mail")
    }

def clear_auth_cookie(response: Response):
    """Elimina la cookie JWT"""
    response.delete_cookie("access_token")

def get_current_user(request: Request):    
    """Dependencia de FastAPI que devuelve solo el ID (sub)."""
    data = verify_access_token_from_cookie(request)
    return data
    # return data["user"]


