from datetime import datetime, timedelta  # Tarih ve zaman işlemleri için
from typing import Optional  # Tip belirteçleri için
from jose import JWTError, jwt  # JWT token işlemleri için
from passlib.context import CryptContext  # Şifre hashleme için
import os  # Ortam değişkenleri için
import secrets  # Güvenli rastgele string üretimi için

# .env dosyasından ortam değişkenlerini yükle
from dotenv import load_dotenv
load_dotenv()

# GÜVENLİK: Uygun doğrulama ile gizli anahtar yönetimi
# Gizli anahtarı almak için birden fazla yöntem dene
SECRET_KEY = os.getenv("CRM_SECRET_KEY")
if not SECRET_KEY:
    # .env dosyasından açık yol ile tekrar yüklemeyi dene
    load_dotenv(".env")
    SECRET_KEY = os.getenv("CRM_SECRET_KEY")
    
if not SECRET_KEY:
    # Geri dönüş: .env dosyasından doğrudan okumaya çalış
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("CRM_SECRET_KEY="):
                    SECRET_KEY = line.split("=", 1)[1].strip()
                    break
    except FileNotFoundError:
        pass

if not SECRET_KEY:
    raise ValueError("CRM_SECRET_KEY environment variable must be set for security")
if len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters long for security")
if SECRET_KEY == "change_this_secret_in_prod":
    raise ValueError("SECRET_KEY must be changed from default value for security")
ALGORITHM = "HS256"  # JWT imzalama algoritması
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Access token geçerlilik süresi: 1 saat
REFRESH_TOKEN_EXPIRE_DAYS = 30  # Refresh token geçerlilik süresi: 30 gün

# Şifre hashleme bağlamı - bcrypt şemasını kullan
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as e:
    # Bcrypt başarısız olursa daha basit bir yapılandırmaya geri dön
    pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

def get_password_hash(password: str) -> str:
    """Şifreyi hash'leyerek güvenli şekilde saklar"""
    # GÜVENLİK: İşlemeden önce şifre uzunluğunu doğrula
    if len(password.encode('utf-8')) > 72:
        raise ValueError("Password too long (max 72 characters)")
    if len(password) < 8:
        raise ValueError("Password too short (min 8 characters)")
    
    try:
        return pwd_context.hash(password)  # Şifreyi bcrypt ile hash'le
    except Exception as e:
        # GÜVENLİK: Zayıf hashleme'ye geri dönüş yok
        raise ValueError("Password hashing failed - please try again")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Düz metin şifre ile hash'lenmiş şifreyi karşılaştırır"""
    try:
        # GÜVENLİK: Şifre uzunluğunu doğrula
        if len(plain_password.encode('utf-8')) > 72:
            return False  # Kesme, uzun şifreleri reddet
        return pwd_context.verify(plain_password, hashed_password)  # Şifre doğrulama
    except Exception as e:
        # GÜVENLİK: Zayıf doğrulamaya geri dönüş yok
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT erişim token'ı oluşturur"""
    to_encode = data.copy()  # Veriyi kopyala
    if expires_delta:  # Eğer özel süre verilmişse
        expire = datetime.utcnow() + expires_delta  # Şu an + verilen süre
    else:  # Varsayılan süre kullan
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Şu an + 1 gün
    to_encode.update({"exp": expire})  # Son kullanma tarihini ekle
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # JWT token'ı oluştur
    return encoded_jwt  # Token'ı döndür

def decode_access_token(token: str):
    """JWT token'ı çözer ve içeriğini döndürür"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # Token'ı çöz
        return payload  # Token içeriğini döndür
    except JWTError:  # Token geçersizse
        return None  # None döndür

def create_refresh_token() -> str:
    """Güvenli refresh token oluşturur"""
    return secrets.token_urlsafe(32)  # 32 byte güvenli rastgele string

def create_token_pair(user_id: int) -> dict:
    """Access ve refresh token çifti oluşturur"""
    # Access token oluştur
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id)}, 
        expires_delta=access_token_expires
    )
    
    # Refresh token oluştur
    refresh_token = create_refresh_token()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Saniye cinsinden
    }

def get_refresh_token_expire_time() -> datetime:
    """Refresh token son kullanma tarihini döndürür"""
    return datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
