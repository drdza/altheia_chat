from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
from services.auth_ad import authenticate_user
from services.auth_jwt import create_access_token, verify_access_token_from_cookie, clear_auth_cookie
from core.config import settings
from models.schemas import LoginRequest, TokenResponse

router = APIRouter()

# --- LOGIN ---
@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, response: Response):    
    user_info = authenticate_user(req.username, req.password)
        
    if not user_info:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    token_payload = {
        "sub": user_info["user"],
        "username": user_info["username"],
        "mail": user_info["mail"]
    }

    token = create_access_token(token_payload)
    # print(f"Token: {token}")
    
    ACCESS_TOKEN_EXPIRE_SECONDS = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    response.set_cookie(
        key="access_token", 
        value=token,
        httponly=True, 
        samesite="none",
        secure=False, 
        max_age=ACCESS_TOKEN_EXPIRE_SECONDS
    )

    return { "access_token": token , "token_type": "bearer" }

# --- CURRENT USER ---
@router.get("/me")
async def get_current_user_info(request: Request):
    """Devuelve el usuario actual para frontend/Streamlit."""
    user_data = verify_access_token_from_cookie(request)
    return {"user": user_data}


    # --- LOGOUT ---
@router.post("/logout")
async def logout(response: Response):
    """Elimina la cookie JWT y cierra sesión."""
    clear_auth_cookie(response)
    return {"message": "Sesión cerrada correctamente"}