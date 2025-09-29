from fastapi import FastAPI, Depends, HTTPException, status, Request  # FastAPI ve bağımlılık yönetimi
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer  # OAuth2 kimlik doğrulama
from fastapi.staticfiles import StaticFiles  # Statik dosya servisi için
from fastapi.responses import FileResponse, JSONResponse  # Dosya yanıtı için
from fastapi.middleware.cors import CORSMiddleware  # CORS middleware
from sqlalchemy.orm import Session  # Veritabanı oturumu
from typing import List  # Tip belirteçleri
import models, schemas  # Veritabanı modelleri ve şemalar
from database import SessionLocal, engine  # Veritabanı bağlantısı
from auth import get_password_hash, verify_password, create_access_token, decode_access_token  # Kimlik doğrulama fonksiyonları
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
    
    # İstek bilgilerini logla
    logger.info(f"🔵 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    # İsteği işle
    response = await call_next(request)
    
    # Yanıt bilgilerini logla
    process_time = time.time() - start_time
    status_emoji = "🟢" if response.status_code < 400 else "🔴" if response.status_code >= 500 else "🟡"
    
    logger.info(f"{status_emoji} {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
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
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Kullanıcı girişi - erişim token'ı oluşturur"""
    logger.info(f"🔐 Login attempt: {form_data.username}")
    
    user = authenticate_user(db, form_data.username, form_data.password)  # Kullanıcıyı doğrula
    if not user:  # Doğrulama başarısızsa
        logger.warning(f"❌ Login failed - Invalid credentials: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")  # 401 hatası
    
    access_token = create_access_token(data={"sub": str(user.id)})  # JWT token oluştur
    logger.info(f"✅ Login successful: {user.email} (ID: {user.id})")
    return {"access_token": access_token, "token_type": "bearer"}  # Token'ı döndür

@app.get("/api/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    """Mevcut kullanıcı bilgilerini getirir"""
    return current_user  # Giriş yapmış kullanıcıyı döndür

@app.post("/api/logout")
def logout(current_user: models.User = Depends(get_current_user)):
    """Kullanıcı çıkışı - token geçersizleştirme için"""
    logger.info(f"🚪 User logout: {current_user.email} (ID: {current_user.id})")
    return {"message": "Logged out successfully", "status": "success"}

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
def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Kullanıcının müşterilerini listeler (sayfalama ile)"""
    customers = db.query(models.Customer).filter(models.Customer.owner_id == current_user.id).offset(skip).limit(limit).all()  # Sahip kullanıcının müşterilerini getir
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
