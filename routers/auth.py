"""
Authentication Router
Kullanıcı kimlik doğrulama endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import logging

import models
import schemas
from dependencies import (
    get_db, 
    get_current_user, 
    authenticate_user,
    get_user_by_email,
    create_refresh_token_db,
    get_refresh_token_db,
    invalidate_refresh_token,
    cleanup_expired_tokens
)
from auth import get_password_hash, create_token_pair

# Router oluştur
router = APIRouter(
    prefix="/api/auth",
    tags=["🔐 Authentication"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger("fastcrm")

@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Kullanıcı kaydı - yeni kullanıcı oluşturur"""
    logger.info(f"📝 User registration attempt: {user_in.email}")
    
    existing = get_user_by_email(db, user_in.email)
    if existing:
        logger.warning(f"❌ Registration failed - Email already exists: {user_in.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = get_password_hash(user_in.password)
    user = models.User(
        email=user_in.email, 
        hashed_password=hashed, 
        full_name=user_in.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"✅ User registered successfully: {user.email} (ID: {user.id})")
    return user

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    request: Request, 
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Kullanıcı girişi - access ve refresh token'ı oluşturur"""
    logger.info(f"🔐 Login attempt: {form_data.username}")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"❌ Login failed - Invalid credentials: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password"
        )
    
    # Token çifti oluştur
    token_data = create_token_pair(user.id)
    
    # Cihaz bilgisini al
    user_agent = request.headers.get('user-agent', 'Unknown Device')[:100]
    
    # Refresh token'ı veritabanına kaydet
    create_refresh_token_db(db, user.id, token_data["refresh_token"], user_agent)
    
    # Eski token'ları temizle
    cleanup_expired_tokens(db)
    
    logger.info(f"✅ Login successful: {user.email} (ID: {user.id})")
    return token_data

@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(
    request: Request, 
    token_data: schemas.TokenRefresh, 
    db: Session = Depends(get_db)
):
    """Refresh token ile yeni access token alır"""
    logger.info(f"🔄 Token refresh attempt")
    
    # Refresh token'ı veritabanından kontrol et
    db_refresh_token = get_refresh_token_db(db, token_data.refresh_token)
    if not db_refresh_token:
        logger.warning(f"❌ Invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid refresh token"
        )
    
    # Token süresi kontrolü
    from datetime import datetime
    if db_refresh_token.expires_at < datetime.utcnow():
        logger.warning(f"❌ Expired refresh token")
        db.delete(db_refresh_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token expired"
        )
    
    # Kullanıcıyı al
    from dependencies import get_user
    user = get_user(db, db_refresh_token.user_id)
    if not user:
        logger.warning(f"❌ User not found for refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found"
        )
    
    # Yeni token çifti oluştur
    new_token_data = create_token_pair(user.id)
    
    # Eski refresh token'ı geçersiz kıl
    invalidate_refresh_token(db, token_data.refresh_token)
    
    # Yeni refresh token'ı kaydet
    user_agent = request.headers.get('user-agent', 'Unknown Device')[:100]
    create_refresh_token_db(db, user.id, new_token_data["refresh_token"], user_agent)
    
    # Son kullanım tarihini güncelle
    db_refresh_token.last_used_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"✅ Token refreshed successfully for user: {user.email}")
    return new_token_data

@router.get("/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    """Mevcut kullanıcı bilgilerini getirir"""
    return current_user

@router.get("/me/tokens", response_model=List[schemas.RefreshTokenOut])
def get_my_tokens(
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Kullanıcının aktif token'larını listeler"""
    logger.info(f"📱 Getting tokens for user: {current_user.email}")
    
    active_tokens = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id,
        models.RefreshToken.is_active == "true"
    ).order_by(models.RefreshToken.created_at.desc()).all()
    
    logger.info(f"✅ Found {len(active_tokens)} active tokens")
    return active_tokens

@router.delete("/me/tokens/{token_id}")
def revoke_token(
    token_id: int, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Belirli bir token'ı geçersizleştir"""
    logger.info(f"🗑️ Revoking token {token_id} for user: {current_user.email}")
    
    token = db.query(models.RefreshToken).filter(
        models.RefreshToken.id == token_id,
        models.RefreshToken.user_id == current_user.id
    ).first()
    
    if not token:
        logger.warning(f"❌ Token not found: {token_id}")
        raise HTTPException(status_code=404, detail="Token not found")
    
    db.delete(token)
    db.commit()
    
    logger.info(f"✅ Token {token_id} revoked successfully")
    return {"message": "Token revoked successfully", "status": "success"}

@router.post("/logout")
def logout(
    request: Request, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Kullanıcı çıkışı - tüm refresh token'ları geçersizleştir"""
    logger.info(f"🚪 User logout: {current_user.email} (ID: {current_user.id})")
    
    # Kullanıcının tüm aktif refresh token'larını geçersiz kıl
    active_tokens = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id,
        models.RefreshToken.is_active == "true"
    ).all()
    
    for token in active_tokens:
        token.is_active = "false"
    
    db.commit()
    
    logger.info(f"✅ Logged out successfully, invalidated {len(active_tokens)} tokens")
    return {
        "message": "Logged out successfully", 
        "status": "success", 
        "tokens_invalidated": len(active_tokens)
    }

@router.post("/logout-all")
def logout_all_devices(
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Tüm cihazlardan çıkış - kullanıcının tüm token'larını geçersizleştir"""
    logger.info(f"🚪 Logout all devices: {current_user.email} (ID: {current_user.id})")
    
    # Kullanıcının tüm refresh token'larını sil
    deleted_count = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id
    ).delete()
    
    db.commit()
    
    logger.info(f"✅ Logged out from all devices, deleted {deleted_count} tokens")
    return {
        "message": "Logged out from all devices", 
        "status": "success", 
        "tokens_deleted": deleted_count
    }
