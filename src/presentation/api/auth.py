import jwt
import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from telegram import Bot

import logging
from src.core.config import JWT_SECRET, TELEGRAM_BOT_TOKEN
from src.core.security import es_usuario_permitido

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer()

# In-memory store for OTPs (For production, use Redis or SQLite)
otp_store = {}

class OTPRequest(BaseModel):
    chat_id: str

class OTPVerify(BaseModel):
    chat_id: str
    code: str

@router.post("/request-otp")
async def request_otp(data: OTPRequest):
    # Sanitize chat_id
    chat_id_clean = data.chat_id.strip()
    
    # Verify if user is explicitly allowed in Bastion Core
    if not es_usuario_permitido(int(chat_id_clean)):
        raise HTTPException(status_code=403, detail="Chat ID not authorized in Bastion Core")

    # Generate 4-digit numeric code
    code = f"{random.randint(1000, 9999)}"
    
    otp_store[chat_id_clean] = {
        "code": code,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    
    # Dispatch code via Telegram Bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        logger.info(f"🧪 [DEBUG TEST] OTP Generado para [{chat_id_clean}]: {code}")
        await bot.send_message(
            chat_id=chat_id_clean, 
            text=f"🔐 Tu código de acceso a Bastion Core Dashboard es: *{code}*\n\nExpirará en 5 minutos.",
            parse_mode="Markdown"
        )
        return {"msg": "OTP sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to send Telegram message: {str(e)}")

@router.post("/verify-otp")
async def verify_otp(data: OTPVerify):
    chat_id_clean = data.chat_id.strip()
    if chat_id_clean not in otp_store:
        raise HTTPException(status_code=400, detail="OTP not requested or expired")
        
    store_data = otp_store[chat_id_clean]
    if datetime.now(timezone.utc) > store_data["expires_at"]:
        del otp_store[chat_id_clean]
        raise HTTPException(status_code=400, detail="OTP expired")
        
    if store_data["code"] != data.code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
        
    # Evaluate proper RBAC using the strict security rules
    from src.core.security import es_admin
    is_admin = es_admin(int(chat_id_clean))

    payload = {
        "sub": chat_id_clean,
        "role": "admin" if is_admin else "tenant",
        "exp": datetime.now(timezone.utc) + timedelta(days=7) # Maintain session for 7 days
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    del otp_store[data.chat_id]
    return {"token": token}

# Dependency for checking auth and extracting tenant from valid JWT
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
