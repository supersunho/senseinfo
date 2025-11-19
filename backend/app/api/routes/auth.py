# backend/app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    CodeInvalidError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    ApiIdInvalidError,
    FloodWaitError,
    PasswordHashInvalidError
)
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
from app.db.session import get_db
from app.core.config import settings
from app.core.telegram_client import client_manager
from app.models.user import User
from app.utils.logger import logger
from app.api.dependencies import get_current_user 

router = APIRouter(prefix="/auth", tags=["authentication"])


class PhoneVerificationRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+\d{10,15}$", description="Phone number with country code")


class CodeVerificationRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+\d{10,15}$")
    phone_code_hash: str = Field(..., min_length=10)
    code: str = Field(..., min_length=4, max_length=6)


class PasswordVerificationRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+\d{10,15}$")
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    status: str
    message: str
    requires_2fa: bool = False
    user_id: Optional[int] = None


auth_sessions: Dict[str, Dict] = {}


@router.post("/telegram/start", response_model=AuthResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_telegram_auth(
    request: PhoneVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    try:
        client = TelegramClient(
            session=f"{settings.session_directory}/temp_{request.phone_number}",
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash
        )
        
        await client.connect()
        sent_code = await client.send_code_request(request.phone_number)
        
        auth_sessions[request.phone_number] = {
            "client": client,
            "phone_code_hash": sent_code.phone_code_hash,
            "timestamp": time.time()
        }
        
        background_tasks.add_task(cleanup_auth_session, request.phone_number, delay=300)
        
        logger.info(f"Verification code sent to {request.phone_number}")
        
        return AuthResponse(
            status="code_sent",
            message="Verification code sent successfully",
            requires_2fa=False
        )
        
    except PhoneNumberInvalidError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    except ApiIdInvalidError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid Telegram API credentials"
        )
    except FloodWaitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please wait {e.seconds} seconds"
        )
    except Exception as e:
        logger.error(f"Auth start error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start authentication"
        )


@router.post("/telegram/verify", response_model=AuthResponse)
async def verify_telegram_code(
    request: CodeVerificationRequest,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    try:
        session_data = auth_sessions.get(request.phone_number)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session expired or not found. Please start authentication again."
            )
        
        client = session_data["client"]
        
        try:
            user = await client.sign_in(
                phone=request.phone_number,
                code=request.code,
                phone_code_hash=session_data["phone_code_hash"]
            )
            
            db_user = await db.execute(
                select(User).where(User.telegram_id == user.id)
            )
            existing_user = db_user.scalar_one_or_none()
            
            if existing_user:
                existing_user.is_authenticated = True
                existing_user.session_string = StringSession.save(client.session)
                existing_user.last_auth_date = datetime.utcnow()
                existing_user.first_name = getattr(user, 'first_name', None)
                existing_user.last_name = getattr(user, 'last_name', None)
                existing_user.username = getattr(user, 'username', None)
                user_obj = existing_user
            else:
                new_user = User(
                    telegram_id=user.id,
                    phone_number=request.phone_number,
                    first_name=getattr(user, 'first_name', None),
                    last_name=getattr(user, 'last_name', None),
                    username=getattr(user, 'username', None),
                    is_authenticated=True,
                    session_string=StringSession.save(client.session),
                    last_auth_date=datetime.utcnow()
                )
                db.add(new_user)
                user_obj = new_user
            
            await db.flush()
            
            await client.disconnect()
            del auth_sessions[request.phone_number]
            
            logger.info(f"User {user.id} authenticated successfully")
            
            return AuthResponse(
                status="authenticated",
                message="Authentication successful",
                requires_2fa=False,
                user_id=user_obj.id
            )
            
        except SessionPasswordNeededError:
            return AuthResponse(
                status="2fa_required",
                message="Two-factor authentication required",
                requires_2fa=True
            )
        except (CodeInvalidError, PhoneCodeInvalidError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


@router.post("/telegram/2fa", response_model=AuthResponse)
async def verify_telegram_2fa(
    request: PasswordVerificationRequest,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    try:
        session_data = auth_sessions.get(request.phone_number)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session expired. Please start authentication again."
            )
        
        client = session_data["client"]
        user = await client.sign_in(password=request.password)
        
        db_user = await db.execute(
            select(User).where(User.telegram_id == user.id)
        )
        existing_user = db_user.scalar_one_or_none()
        
        if existing_user:
            existing_user.is_authenticated = True
            existing_user.session_string = StringSession.save(client.session)
            existing_user.last_auth_date = datetime.utcnow()
            user_obj = existing_user
        else:
            new_user = User(
                telegram_id=user.id,
                phone_number=request.phone_number,
                first_name=getattr(user, 'first_name', None),
                last_name=getattr(user, 'last_name', None),
                username=getattr(user, 'username', None),
                is_authenticated=True,
                session_string=StringSession.save(client.session),
                last_auth_date=datetime.utcnow()
            )
            db.add(new_user)
            user_obj = new_user
        
        await db.flush()
        
        await client.disconnect()
        del auth_sessions[request.phone_number]
        
        logger.info(f"User {user.id} authenticated with 2FA")
        
        return AuthResponse(
            status="authenticated",
            message="2FA authentication successful",
            requires_2fa=False,
            user_id=user_obj.id
        )
        
    except PasswordHashInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA password"
        )
    except Exception as e:
        logger.error(f"2FA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA verification failed"
        )


@router.post("/logout", response_model=AuthResponse)
async def logout(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    try:
        await client_manager.disconnect_client(user.id)
        
        user.is_authenticated = False
        user.session_string = None
        
        await db.commit()
        
        logger.info(f"User {user.id} logged out successfully")
        
        return AuthResponse(
            status="logged_out",
            message="Successfully logged out",
            user_id=user.id
        )
        
    except Exception as e:
        logger.error(f"Logout error for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


async def cleanup_auth_session(phone_number: str, delay: int = 300):
    await asyncio.sleep(delay)
    
    if phone_number in auth_sessions:
        try:
            client = auth_sessions[phone_number]["client"]
            await client.disconnect()
        except Exception:
            pass
        finally:
            del auth_sessions[phone_number]
            logger.info(f"Cleaned up auth session for {phone_number}")
