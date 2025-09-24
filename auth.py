from datetime import datetime, timedelta  # Tarih ve zaman işlemleri için
from typing import Optional  # Tip belirteçleri için
from jose import JWTError, jwt  # JWT token işlemleri için
from passlib.context import CryptContext  # Şifre hashleme için
import os  # Ortam değişkenleri için

# Gizli anahtar - ortam değişkeninden al veya varsayılan kullan (üretimde değiştir)
SECRET_KEY = os.getenv("CRM_SECRET_KEY", "change_this_secret_in_prod")
ALGORITHM = "HS256"  # JWT imzalama algoritması
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token geçerlilik süresi: 1 gün

# Şifre hashleme bağlamı - bcrypt şemasını kullan
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Şifreyi hash'leyerek güvenli şekilde saklar"""
    return pwd_context.hash(password)  # Şifreyi bcrypt ile hash'le

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Düz metin şifre ile hash'lenmiş şifreyi karşılaştırır"""
    return pwd_context.verify(plain_password, hashed_password)  # Şifre doğrulama

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
