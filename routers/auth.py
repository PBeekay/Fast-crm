"""
Authentication Router
Kullanıcı kimlik doğrulama endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
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
import secrets
import uuid

# SECURITY: Rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)

# Router oluştur
router = APIRouter(
    prefix="/api/auth",
    tags=["🔐 Authentication"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger("fastcrm")

@router.post("/register", response_model=schemas.UserRegistrationResponse)
@limiter.limit("5/minute")  # SECURITY: Rate limit registration attempts
def register(request: Request, user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Kullanıcı kaydı - yeni kullanıcı oluşturur ve OAuth2 client credentials oluşturur.
    
    OAuth2 credentials otomatik oluşturulur ancak güvenlik nedeniyle yanıtta döndürülmez.
    API erişimi için OAuth2 credentials'ı Swagger UI'dan veya admin panelinden alabilirsiniz.
    """
    logger.info(f"📝 User registration attempt: {user_in.email}")
    
    existing = get_user_by_email(db, user_in.email)
    if existing:
        logger.warning(f"❌ Registration failed - Email already exists: {user_in.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        hashed = get_password_hash(user_in.password)
    except ValueError as e:
        logger.warning(f"❌ Registration failed - Password validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    user = models.User(
        email=user_in.email, 
        hashed_password=hashed, 
        full_name=user_in.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # OAuth2 Client Credentials oluştur
    client_id = f"fcrm_{uuid.uuid4().hex[:16]}"  # FastCRM prefix + 16 karakter
    client_secret = secrets.token_urlsafe(32)  # 32 karakter güvenli secret
    
    oauth2_client = models.OAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        user_id=user.id,
        is_active="true"
    )
    db.add(oauth2_client)
    db.commit()
    db.refresh(oauth2_client)
    
    logger.info(f"✅ User registered successfully: {user.email} (ID: {user.id})")
    logger.info(f"🔑 OAuth2 Client created: {client_id}")
    
    return {
        "user": user,
        "message": "Registration successful! You can now login with your credentials. Your API access credentials have been created and can be viewed in the Swagger UI documentation."
    }

@router.post("/oauth2/token", response_model=schemas.Token)
@limiter.limit("20/minute")  # SECURITY: Rate limit OAuth2 token requests
def get_oauth2_token(
    request: Request,
    client_credentials: schemas.OAuth2ClientCredentials,
    db: Session = Depends(get_db)
):
    """OAuth2 Client Credentials flow - API erişimi için token alır"""
    logger.info(f"🔑 OAuth2 token request for client: {client_credentials.client_id}")
    
    # OAuth2 client'ı doğrula
    oauth2_client = db.query(models.OAuth2Client).filter(
        models.OAuth2Client.client_id == client_credentials.client_id,
        models.OAuth2Client.client_secret == client_credentials.client_secret,
        models.OAuth2Client.is_active == "true"
    ).first()
    
    if not oauth2_client:
        logger.warning(f"❌ Invalid OAuth2 client credentials: {client_credentials.client_id}")
        raise HTTPException(
            status_code=401,
            detail="Invalid client credentials"
        )
    
    # Kullanıcıyı al
    user = db.query(models.User).filter(
        models.User.id == oauth2_client.user_id,
        models.User.is_active == "true"
    ).first()
    
    if not user:
        logger.warning(f"❌ User not found or inactive for OAuth2 client: {client_credentials.client_id}")
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive"
        )
    
    # Token çifti oluştur
    token_pair = create_token_pair(user.id)
    
    # Refresh token'ı veritabanına kaydet
    create_refresh_token_db(db, user.id, token_pair["refresh_token"])
    
    # OAuth2 client'ın son kullanım tarihini güncelle
    from datetime import datetime
    oauth2_client.last_used_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"✅ OAuth2 token issued for user: {user.email} (Client: {client_credentials.client_id})")
    
    return token_pair

@router.post("/token", response_model=schemas.Token)
@limiter.limit("10/minute")  # SECURITY: Rate limit login attempts
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

@router.get("/me/oauth2-credentials", response_model=List[schemas.OAuth2ClientOut])
def get_my_oauth2_credentials(
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Kullanıcının OAuth2 client credentials'larını listeler.
    
    Bu endpoint, API erişimi için gerekli client_id ve client_secret bilgilerini döndürür.
    Sadece Swagger UI veya authenticated API çağrıları üzerinden erişilebilir.
    """
    logger.info(f"🔑 Getting OAuth2 credentials for user: {current_user.email}")
    
    oauth2_clients = db.query(models.OAuth2Client).filter(
        models.OAuth2Client.user_id == current_user.id,
        models.OAuth2Client.is_active == "true"
    ).order_by(models.OAuth2Client.created_at.desc()).all()
    
    logger.info(f"✅ Found {len(oauth2_clients)} OAuth2 clients")
    return oauth2_clients

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
