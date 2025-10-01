from fastapi import FastAPI, Depends, HTTPException, status, Request  # FastAPI ve bağımlılık yönetimi
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer  # OAuth2 kimlik doğrulama
from fastapi.staticfiles import StaticFiles  # Statik dosya servisi için
from fastapi.responses import FileResponse, JSONResponse  # Dosya yanıtı için
from fastapi.middleware.cors import CORSMiddleware  # CORS middleware
from sqlalchemy.orm import Session  # Veritabanı oturumu
from typing import List  # Tip belirteçleri
import models, schemas  # Veritabanı modelleri ve şemalar
from database import SessionLocal, engine  # Veritabanı bağlantısı
from auth import get_password_hash, verify_password, create_access_token, decode_access_token, create_token_pair, get_refresh_token_expire_time  # Kimlik doğrulama fonksiyonları
import logging  # Logging için
import time  # Zaman ölçümü için
import traceback  # Error tracing

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Konsola log yazdır
    ]
)
logger = logging.getLogger("fastcrm")

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

# FastAPI uygulamasını oluştur
app = FastAPI(title="Simple CRM MVP")

# CORS middleware - Allow requests from other devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """HTTP isteklerini ve yanıtlarını logla"""
    start_time = time.time()
    
    # Client bilgilerini al
    client_ip = request.client.host if request.client else 'unknown'
    user_agent = request.headers.get('user-agent', 'unknown')[:50]  # İlk 50 karakter
    
    # İstek bilgilerini logla
    method_emoji = {
        'GET': '📖',
        'POST': '📝', 
        'PUT': '✏️',
        'DELETE': '🗑️',
        'PATCH': '🔧',
        'HEAD': '👁️',
        'OPTIONS': '⚙️'
    }.get(request.method, '🔵')
    
    logger.info(f"{method_emoji} {request.method} {request.url.path} - Client: {client_ip}")
    logger.info(f"📱 User-Agent: {user_agent}")
    
    # Query parameters varsa logla
    if request.query_params:
        logger.info(f"🔍 Query: {dict(request.query_params)}")
    
    # Request body size (if available)
    content_length = request.headers.get('content-length')
    if content_length:
        logger.info(f"📦 Request Body Size: {content_length} bytes")
    
    # İsteği işle
    response = await call_next(request)
    
    # Yanıt bilgilerini logla
    process_time = time.time() - start_time
    
    # Status code'a göre emoji ve açıklama
    if response.status_code < 200:
        status_emoji = "🟡"
        status_desc = "Informational"
    elif response.status_code < 300:
        status_emoji = "🟢"
        status_desc = "Success"
    elif response.status_code < 400:
        status_emoji = "🟡"
        status_desc = "Redirect"
    elif response.status_code < 500:
        status_emoji = "🟠"
        status_desc = "Client Error"
    else:
        status_emoji = "🔴"
        status_desc = "Server Error"
    
    # Response headers'da önemli bilgiler varsa logla
    content_type = response.headers.get('content-type', 'unknown')
    content_length = response.headers.get('content-length', 'unknown')
    
    # Performance categorization
    if process_time < 0.1:
        perf_emoji = "⚡"
        perf_desc = "Fast"
    elif process_time < 0.5:
        perf_emoji = "🚀"
        perf_desc = "Good"
    elif process_time < 1.0:
        perf_emoji = "🐌"
        perf_desc = "Slow"
    else:
        perf_emoji = "🐢"
        perf_desc = "Very Slow"
    
    logger.info(f"{status_emoji} {request.method} {request.url.path} - Status: {response.status_code} ({status_desc}) - Time: {process_time:.3f}s")
    logger.info(f"📄 Content-Type: {content_type} | Content-Length: {content_length}")
    logger.info(f"{perf_emoji} Performance: {perf_desc} ({process_time:.3f}s)")
    
    # Error durumlarında daha detaylı log
    if response.status_code >= 400:
        logger.warning(f"⚠️ Error Response: {response.status_code} for {request.method} {request.url.path}")
    
    # Specific status code logging
    if response.status_code == 200:
        logger.info(f"✅ OK: {request.method} {request.url.path} completed successfully")
    elif response.status_code == 201:
        logger.info(f"✅ Created: {request.method} {request.url.path} resource created")
    elif response.status_code == 400:
        logger.warning(f"❌ Bad Request: {request.method} {request.url.path} - Invalid request data")
    elif response.status_code == 401:
        logger.warning(f"🔒 Unauthorized: {request.method} {request.url.path} - Authentication required")
    elif response.status_code == 403:
        logger.warning(f"🚫 Forbidden: {request.method} {request.url.path} - Access denied")
    elif response.status_code == 404:
        logger.warning(f"🔍 Not Found: {request.method} {request.url.path} - Resource not found")
    elif response.status_code == 422:
        logger.warning(f"📝 Unprocessable Entity: {request.method} {request.url.path} - Validation error")
    elif response.status_code == 500:
        logger.error(f"💥 Internal Server Error: {request.method} {request.url.path} - Server error")
    
    # Request summary
    logger.info(f"📊 Request Summary: {method_emoji} {request.method} {request.url.path} → {status_emoji} {response.status_code} ({perf_emoji} {process_time:.3f}s)")
    
    return response

# Global exception handler to ensure JSON responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure all errors return JSON"""
    logger.error(f"❌ Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "path": str(request.url)
        }
    )

# Statik dosyaları servis et
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache-busting middleware for development
@app.middleware("http")
async def add_cache_control_header(request, call_next):
    """Add cache control headers to prevent caching during development"""
    response = await call_next(request)
    
    # Add cache-busting headers for static files
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["ETag"] = str(int(time.time()))  # Dynamic ETag
    
    return response

# OAuth2 şemasını tanımla - token URL'i belirt
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# Ana sayfa ve kayıt sayfası
@app.get("/")
async def read_root():
    """Ana sayfa - giriş ekranını servis et"""
    return FileResponse("static/index.html")

@app.get("/register")
async def read_register():
    """Kayıt sayfası"""
    return FileResponse("static/register.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint for debugging"""
    return {
        "status": "healthy",
        "message": "FastCRM API is running",
        "timestamp": time.time()
    }


# Veritabanı bağımlılığı - her istek için yeni oturum oluştur
def get_db():
    db = SessionLocal()  # Yeni veritabanı oturumu oluştur
    try:
        yield db  # Oturumu kullanıma sun
    finally:
        db.close()  # İşlem bitince oturumu kapat

# --- Kimlik Doğrulama Yardımcı Fonksiyonları ---
def get_user_by_email(db: Session, email: str):
    """E-posta adresine göre kullanıcı bulur"""
    return db.query(models.User).filter(models.User.email == email).first()  # E-posta ile kullanıcı ara

def get_user(db: Session, user_id: int):
    """ID'ye göre kullanıcı bulur"""
    return db.query(models.User).filter(models.User.id == user_id).first()  # ID ile kullanıcı ara

def authenticate_user(db: Session, email: str, password: str):
    """Kullanıcı kimlik doğrulaması yapar"""
    user = get_user_by_email(db, email)  # Kullanıcıyı e-posta ile bul
    if not user:  # Kullanıcı bulunamadıysa
        return False  # False döndür
    if not verify_password(password, user.hashed_password):  # Şifre yanlışsa
        return False  # False döndür
    return user  # Kullanıcıyı döndür

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Mevcut kullanıcıyı token'dan alır"""
    payload = decode_access_token(token)  # Token'ı çöz
    if not payload:  # Token geçersizse
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")  # 401 hatası
    user_id = payload.get("sub")  # Token'dan kullanıcı ID'sini al
    if not user_id:  # ID yoksa
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")  # 401 hatası
    user = get_user(db, int(user_id))  # Kullanıcıyı veritabanından al
    if not user:  # Kullanıcı bulunamadıysa
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")  # 401 hatası
    return user  # Kullanıcıyı döndür

# --- Refresh Token Yardımcı Fonksiyonları ---
def create_refresh_token_db(db: Session, user_id: int, refresh_token: str, device_info: str = None):
    """Veritabanında refresh token oluşturur"""
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

# --- API Endpoint'leri ---
@app.post("/api/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Kullanıcı kaydı - yeni kullanıcı oluşturur"""
    logger.info(f"📝 User registration attempt: {user_in.email}")
    
    existing = get_user_by_email(db, user_in.email)  # E-posta zaten kayıtlı mı kontrol et
    if existing:  # Eğer kayıtlıysa
        logger.warning(f"❌ Registration failed - Email already exists: {user_in.email}")
        raise HTTPException(status_code=400, detail="Email already registered")  # 400 hatası döndür
    
    hashed = get_password_hash(user_in.password)  # Şifreyi hash'le
    user = models.User(email=user_in.email, hashed_password=hashed, full_name=user_in.full_name)  # Yeni kullanıcı oluştur
    db.add(user)  # Kullanıcıyı veritabanına ekle
    db.commit()  # Değişiklikleri kaydet
    db.refresh(user)  # Kullanıcıyı yenile (ID almak için)
    
    logger.info(f"✅ User registered successfully: {user.email} (ID: {user.id})")
    return user  # Kullanıcıyı döndür

@app.post("/api/token", response_model=schemas.Token)
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Kullanıcı girişi - access ve refresh token'ı oluşturur"""
    logger.info(f"🔐 Login attempt: {form_data.username}")
    
    user = authenticate_user(db, form_data.username, form_data.password)  # Kullanıcıyı doğrula
    if not user:  # Doğrulama başarısızsa
        logger.warning(f"❌ Login failed - Invalid credentials: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")  # 401 hatası
    
    # Token çifti oluştur
    token_data = create_token_pair(user.id)
    
    # Cihaz bilgisini al
    user_agent = request.headers.get('user-agent', 'Unknown Device')[:100]
    
    # Refresh token'ı veritabanına kaydet
    create_refresh_token_db(db, user.id, token_data["refresh_token"], user_agent)
    
    # Eski token'ları temizle (opsiyonel)
    cleanup_expired_tokens(db)
    
    logger.info(f"✅ Login successful: {user.email} (ID: {user.id})")
    return token_data  # Token çiftini döndür

@app.get("/api/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    """Mevcut kullanıcı bilgilerini getirir"""
    return current_user  # Giriş yapmış kullanıcıyı döndür

@app.get("/api/me/tokens", response_model=List[schemas.RefreshTokenOut])
def get_my_tokens(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Kullanıcının aktif token'larını listeler"""
    logger.info(f"📱 Getting tokens for user: {current_user.email}")
    
    # Kullanıcının aktif token'larını al
    active_tokens = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id,
        models.RefreshToken.is_active == "true"
    ).order_by(models.RefreshToken.created_at.desc()).all()
    
    logger.info(f"✅ Found {len(active_tokens)} active tokens")
    return active_tokens

@app.delete("/api/me/tokens/{token_id}")
def revoke_token(token_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Belirli bir token'ı geçersizleştir"""
    logger.info(f"🗑️ Revoking token {token_id} for user: {current_user.email}")
    
    # Token'ı bul ve kullanıcının token'ı olduğunu kontrol et
    token = db.query(models.RefreshToken).filter(
        models.RefreshToken.id == token_id,
        models.RefreshToken.user_id == current_user.id
    ).first()
    
    if not token:
        logger.warning(f"❌ Token not found: {token_id}")
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Token'ı sil
    db.delete(token)
    db.commit()
    
    logger.info(f"✅ Token {token_id} revoked successfully")
    return {"message": "Token revoked successfully", "status": "success"}

@app.post("/api/refresh", response_model=schemas.Token)
def refresh_access_token(request: Request, token_data: schemas.TokenRefresh, db: Session = Depends(get_db)):
    """Refresh token ile yeni access token alır"""
    logger.info(f"🔄 Token refresh attempt")
    
    # Refresh token'ı veritabanından kontrol et
    db_refresh_token = get_refresh_token_db(db, token_data.refresh_token)
    if not db_refresh_token:
        logger.warning(f"❌ Invalid refresh token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    # Token süresi kontrolü
    from datetime import datetime
    if db_refresh_token.expires_at < datetime.utcnow():
        logger.warning(f"❌ Expired refresh token")
        # Süresi dolmuş token'ı sil
        db.delete(db_refresh_token)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    
    # Kullanıcıyı al
    user = get_user(db, db_refresh_token.user_id)
    if not user:
        logger.warning(f"❌ User not found for refresh token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
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

@app.post("/api/logout")
def logout(request: Request, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
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
    return {"message": "Logged out successfully", "status": "success", "tokens_invalidated": len(active_tokens)}

@app.post("/api/logout-all")
def logout_all_devices(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Tüm cihazlardan çıkış - kullanıcının tüm token'larını geçersizleştir"""
    logger.info(f"🚪 Logout all devices: {current_user.email} (ID: {current_user.id})")
    
    # Kullanıcının tüm refresh token'larını sil
    deleted_count = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id
    ).delete()
    
    db.commit()
    
    logger.info(f"✅ Logged out from all devices, deleted {deleted_count} tokens")
    return {"message": "Logged out from all devices", "status": "success", "tokens_deleted": deleted_count}

# --- Müşteri Endpoint'leri ---
@app.post("/api/customers", response_model=schemas.CustomerOut)
def create_customer(customer_in: schemas.CustomerCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Yeni müşteri oluşturur"""
    logger.info(f"👤 Creating customer: {customer_in.name} (Owner: {current_user.email})")
    
    customer = models.Customer(  # Yeni müşteri nesnesi oluştur
        name=customer_in.name,  # Müşteri adı
        email=customer_in.email,  # E-posta
        phone=customer_in.phone,  # Telefon
        company=customer_in.company,  # Şirket
        owner_id=current_user.id  # Sahip kullanıcı ID'si
    )
    db.add(customer)  # Müşteriyi veritabanına ekle
    db.commit()  # Değişiklikleri kaydet
    db.refresh(customer)  # Müşteriyi yenile (ID almak için)
    
    logger.info(f"✅ Customer created: {customer.name} (ID: {customer.id})")
    return customer  # Müşteriyi döndür

@app.get("/api/customers", response_model=List[schemas.CustomerOut])
def list_customers(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Kullanıcının müşterilerini listeler (sayfalama ve arama ile)"""
    query = db.query(models.Customer).filter(models.Customer.owner_id == current_user.id)
    
    # Arama filtresi ekle
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            models.Customer.name.ilike(search_term) |
            models.Customer.email.ilike(search_term) |
            models.Customer.company.ilike(search_term) |
            models.Customer.phone.ilike(search_term)
        )
        logger.info(f"🔍 Searching customers with term: '{search}' (User: {current_user.email})")
    
    customers = query.offset(skip).limit(limit).all()
    logger.info(f"📋 Listed {len(customers)} customers for user: {current_user.email}")
    return customers

@app.get("/api/customers/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Belirli bir müşteriyi getirir"""
    logger.info(f"🔍 Getting customer ID: {customer_id} (User: {current_user.email})")
    
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        logger.warning(f"❌ Customer not found: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    
    logger.info(f"✅ Customer retrieved: {customer.name} (ID: {customer.id})")
    return customer  # Müşteriyi döndür

@app.put("/api/customers/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(customer_id: int, customer_update: schemas.CustomerUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Müşteri bilgilerini günceller"""
    logger.info(f"✏️ Updating customer ID: {customer_id} (User: {current_user.email})")
    
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        logger.warning(f"❌ Customer not found: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    
    # Sadece sağlanan alanları güncelle
    update_data = customer_update.dict(exclude_unset=True)  # Sadece sağlanan alanları al
    for field, value in update_data.items():  # Her alan için
        setattr(customer, field, value)  # Müşteri nesnesini güncelle
    
    db.commit()  # Değişiklikleri kaydet
    db.refresh(customer)  # Müşteriyi yenile
    
    logger.info(f"✅ Customer updated: {customer.name} (ID: {customer.id})")
    return customer  # Güncellenmiş müşteriyi döndür

@app.delete("/api/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Müşteriyi siler"""
    logger.info(f"🗑️ Deleting customer ID: {customer_id} (User: {current_user.email})")
    
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        logger.warning(f"❌ Customer not found for deletion: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    
    customer_name = customer.name
    db.delete(customer)  # Müşteriyi sil
    db.commit()  # Değişiklikleri kaydet
    
    logger.info(f"✅ Customer deleted: {customer_name} (ID: {customer_id})")
    return  # Boş döndür (204 No Content)

# --- Not Endpoint'leri ---
@app.post("/api/customers/{customer_id}/notes", response_model=schemas.NoteOut)
def add_note(customer_id: int, note_in: schemas.NoteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Müşteriye not ekler"""
    logger.info(f"📝 Adding note to customer ID: {customer_id} (User: {current_user.email})")
    
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        logger.warning(f"❌ Customer not found for note: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    
    note = models.Note(customer_id=customer.id, content=note_in.content, created_by=current_user.id)  # Yeni not oluştur
    db.add(note)  # Notu veritabanına ekle
    db.commit()  # Değişiklikleri kaydet
    db.refresh(note)  # Notu yenile (ID almak için)
    
    logger.info(f"✅ Note added: ID {note.id} for customer {customer.name}")
    return note  # Notu döndür

@app.get("/api/customers/{customer_id}/notes", response_model=List[schemas.NoteOut])
def list_notes(customer_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Müşterinin notlarını listeler"""
    logger.info(f"📋 Listing notes for customer ID: {customer_id} (User: {current_user.email})")
    
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        logger.warning(f"❌ Customer not found for notes: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    
    notes = db.query(models.Note).filter(models.Note.customer_id == customer.id).all()  # Müşterinin notlarını getir
    logger.info(f"✅ Listed {len(notes)} notes for customer: {customer.name}")
    return notes

@app.delete("/api/customers/{customer_id}/notes/{note_id}", status_code=204)
def delete_note(customer_id: int, note_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Müşteri notunu siler"""
    logger.info(f"🗑️ Deleting note ID: {note_id} for customer ID: {customer_id} (User: {current_user.email})")
    
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        logger.warning(f"❌ Customer not found for note deletion: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.customer_id == customer.id).first()  # Notu ID ve müşteri ile bul
    if not note:  # Not bulunamadıysa
        logger.warning(f"❌ Note not found: ID {note_id} for customer {customer.name}")
        raise HTTPException(status_code=404, detail="Note not found")  # 404 hatası
    
    db.delete(note)  # Notu sil
    db.commit()  # Değişiklikleri kaydet
    
    logger.info(f"✅ Note deleted: ID {note_id} for customer {customer.name}")
    return  # Boş döndür (204 No Content)
