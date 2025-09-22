# Gerekli kütüphaneleri import ediyoruz
from fastapi import FastAPI, Depends, HTTPException, status  # FastAPI ve bağımlılık yönetimi
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer  # OAuth2 kimlik doğrulama
from sqlalchemy.orm import Session  # Veritabanı oturumu
from typing import List  # Tip belirteçleri
import models, schemas  # Veritabanı modelleri ve şemalar
from database import SessionLocal, engine  # Veritabanı bağlantısı
from auth import get_password_hash, verify_password, create_access_token, decode_access_token  # Kimlik doğrulama fonksiyonları
import auth as auth_module  # Kimlik doğrulama modülü

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

# FastAPI uygulamasını oluştur
app = FastAPI(title="Simple CRM MVP")

# OAuth2 şemasını tanımla - token URL'i belirt
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
@app.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Kullanıcı kaydı - yeni kullanıcı oluşturur"""
    existing = get_user_by_email(db, user_in.email)  # E-posta zaten kayıtlı mı kontrol et
    if existing:  # Eğer kayıtlıysa
        raise HTTPException(status_code=400, detail="Email already registered")  # 400 hatası döndür
    hashed = get_password_hash(user_in.password)  # Şifreyi hash'le
    user = models.User(email=user_in.email, hashed_password=hashed, full_name=user_in.full_name)  # Yeni kullanıcı oluştur
    db.add(user)  # Kullanıcıyı veritabanına ekle
    db.commit()  # Değişiklikleri kaydet
    db.refresh(user)  # Kullanıcıyı yenile (ID almak için)
    return user  # Kullanıcıyı döndür

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Kullanıcı girişi - erişim token'ı oluşturur"""
    user = authenticate_user(db, form_data.username, form_data.password)  # Kullanıcıyı doğrula
    if not user:  # Doğrulama başarısızsa
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")  # 401 hatası
    access_token = create_access_token(data={"sub": str(user.id)})  # JWT token oluştur
    return {"access_token": access_token, "token_type": "bearer"}  # Token'ı döndür

@app.get("/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    """Mevcut kullanıcı bilgilerini getirir"""
    return current_user  # Giriş yapmış kullanıcıyı döndür

# --- Müşteri Endpoint'leri ---
@app.post("/customers", response_model=schemas.CustomerOut)
def create_customer(customer_in: schemas.CustomerCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Yeni müşteri oluşturur"""
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
    return customer  # Müşteriyi döndür

@app.get("/customers", response_model=List[schemas.CustomerOut])
def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Kullanıcının müşterilerini listeler (sayfalama ile)"""
    return db.query(models.Customer).filter(models.Customer.owner_id == current_user.id).offset(skip).limit(limit).all()  # Sahip kullanıcının müşterilerini getir

@app.get("/customers/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Belirli bir müşteriyi getirir"""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    return customer  # Müşteriyi döndür

@app.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Müşteriyi siler"""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    db.delete(customer)  # Müşteriyi sil
    db.commit()  # Değişiklikleri kaydet
    return  # Boş döndür (204 No Content)

# --- Not Endpoint'leri ---
@app.post("/customers/{customer_id}/notes", response_model=schemas.NoteOut)
def add_note(customer_id: int, note_in: schemas.NoteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Müşteriye not ekler"""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    note = models.Note(customer_id=customer.id, content=note_in.content, created_by=current_user.id)  # Yeni not oluştur
    db.add(note)  # Notu veritabanına ekle
    db.commit()  # Değişiklikleri kaydet
    db.refresh(note)  # Notu yenile (ID almak için)
    return note  # Notu döndür

@app.get("/customers/{customer_id}/notes", response_model=List[schemas.NoteOut])
def list_notes(customer_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Müşterinin notlarını listeler"""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.owner_id == current_user.id).first()  # Müşteriyi ID ve sahip ile bul
    if not customer:  # Müşteri bulunamadıysa
        raise HTTPException(status_code=404, detail="Customer not found")  # 404 hatası
    return db.query(models.Note).filter(models.Note.customer_id == customer.id).all()  # Müşterinin notlarını getir
