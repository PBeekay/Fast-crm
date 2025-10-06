"""
FastCRM Dependencies
Ortak bağımlılıklar ve yardımcı fonksiyonlar
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import models
from database import SessionLocal
from auth import decode_access_token
import logging

logger = logging.getLogger("fastcrm")

# OAuth2 şemasını tanımla
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Veritabanı bağımlılığı
def get_db():
    """Veritabanı oturumu bağımlılığı"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Kullanıcı yardımcı fonksiyonları
def get_user_by_email(db: Session, email: str):
    """E-posta adresine göre kullanıcı bulur"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: int):
    """ID'ye göre kullanıcı bulur"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def authenticate_user(db: Session, email: str, password: str):
    """Kullanıcı kimlik doğrulaması yapar"""
    from auth import verify_password
    
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Mevcut kullanıcı bağımlılığı
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """Mevcut kullanıcıyı token'dan alır"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token payload"
        )
    
    user = get_user(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found"
        )
    
    return user

# Refresh Token yardımcı fonksiyonları
def create_refresh_token_db(db: Session, user_id: int, refresh_token: str, device_info: str = None):
    """Veritabanında refresh token oluşturur"""
    from auth import get_refresh_token_expire_time
    
    db_refresh_token = models.RefreshToken(
        token=refresh_token,
        user_id=user_id,
        expires_at=get_refresh_token_expire_time(),
        device_info=device_info
    )
    db.add(db_refresh_token)
    db.commit()
    db.refresh(db_refresh_token)
    return db_refresh_token

def get_refresh_token_db(db: Session, refresh_token: str):
    """Veritabanından refresh token'ı alır"""
    return db.query(models.RefreshToken).filter(
        models.RefreshToken.token == refresh_token,
        models.RefreshToken.is_active == "true"
    ).first()

def invalidate_refresh_token(db: Session, refresh_token: str):
    """Refresh token'ı geçersiz kılar"""
    db_token = get_refresh_token_db(db, refresh_token)
    if db_token:
        db_token.is_active = "false"
        db.commit()
    return db_token

def cleanup_expired_tokens(db: Session):
    """Süresi dolmuş token'ları temizler"""
    from datetime import datetime
    
    expired_tokens = db.query(models.RefreshToken).filter(
        models.RefreshToken.expires_at < datetime.utcnow()
    ).all()
    
    for token in expired_tokens:
        db.delete(token)
    
    db.commit()
    return len(expired_tokens)

# Role tabanlı erişim kontrolleri
async def get_admin_user(current_user: models.User = Depends(get_current_user)):
    """Admin yetkisi kontrolü"""
    if current_user.role != models.UserRole.ADMIN:
        logger.warning(f"❌ Admin access denied for user: {current_user.email} (Role: {current_user.role.value})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin privileges required"
        )
    return current_user

async def get_premium_user(current_user: models.User = Depends(get_current_user)):
    """Premium kullanıcı yetkisi kontrolü (premium_user veya admin)"""
    if current_user.role not in [models.UserRole.PREMIUM_USER, models.UserRole.ADMIN]:
        logger.warning(f"❌ Premium access denied for user: {current_user.email} (Role: {current_user.role.value})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Premium user privileges required"
        )
    return current_user

async def get_active_user(current_user: models.User = Depends(get_current_user)):
    """Aktif kullanıcı kontrolü"""
    if current_user.is_active != "true":
        logger.warning(f"❌ Inactive user access denied: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Account is inactive"
        )
    return current_user

def check_user_permissions(current_user: models.User, required_role: models.UserRole):
    """Kullanıcı izinlerini kontrol eder"""
    role_hierarchy = {
        models.UserRole.BASIC_USER: 1,
        models.UserRole.PREMIUM_USER: 2,
        models.UserRole.ADMIN: 3
    }
    
    user_level = role_hierarchy.get(current_user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

# OAuth2 Client Authentication
def get_oauth2_client(db: Session, client_id: str, client_secret: str) -> Optional[models.OAuth2Client]:
    """OAuth2 client credentials doğrula"""
    return db.query(models.OAuth2Client).filter(
        models.OAuth2Client.client_id == client_id,
        models.OAuth2Client.client_secret == client_secret,
        models.OAuth2Client.is_active == "true"
    ).first()

def get_current_user_oauth2(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
) -> models.User:
    """OAuth2 Bearer token ile kullanıcı doğrula"""
    token = credentials.credentials
    
    # Token'ı çöz
    payload = decode_access_token(token)
    if payload is None:
        logger.warning("❌ Invalid OAuth2 token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Kullanıcıyı al
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("❌ Token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user(db, int(user_id))
    if user is None:
        logger.warning(f"❌ User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_active != "true":
        logger.warning(f"❌ Inactive user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"✅ OAuth2 authenticated user: {user.email}")
    return user
