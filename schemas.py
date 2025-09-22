# Gerekli kütüphaneleri import ediyoruz
from pydantic import BaseModel, EmailStr  # Veri doğrulama ve e-posta formatı için
from typing import Optional, List  # Tip belirteçleri için
from datetime import datetime  # Tarih ve zaman işlemleri için

# --- Kullanıcı Şemaları ---
class UserCreate(BaseModel):
    """Kullanıcı oluşturma şeması - yeni kullanıcı kaydı için"""
    email: EmailStr  # E-posta adresi, doğrulanmış format
    password: str  # Şifre
    full_name: Optional[str] = None  # Tam ad, isteğe bağlı

class UserOut(BaseModel):
    """Kullanıcı çıktı şeması - kullanıcı bilgilerini döndürmek için"""
    id: int  # Kullanıcı ID'si
    email: EmailStr  # E-posta adresi
    full_name: Optional[str]  # Tam ad
    created_at: Optional[datetime]  # Oluşturulma tarihi

    class Config:
        from_attributes = True  # ORM nesnelerinden veri alabilir

# --- Token Şeması ---
class Token(BaseModel):
    """JWT token şeması - kimlik doğrulama token'ı için"""
    access_token: str  # Erişim token'ı
    token_type: str = "bearer"  # Token türü, varsayılan "bearer"

# --- Müşteri Şemaları ---
class CustomerBase(BaseModel):
    """Müşteri temel şeması - ortak müşteri alanları"""
    name: str  # Müşteri adı, zorunlu
    email: Optional[EmailStr] = None  # E-posta, isteğe bağlı
    phone: Optional[str] = None  # Telefon, isteğe bağlı
    company: Optional[str] = None  # Şirket, isteğe bağlı

class CustomerCreate(CustomerBase):
    """Müşteri oluşturma şeması - yeni müşteri ekleme için"""
    pass  # Temel şemadan tüm alanları al

class CustomerOut(CustomerBase):
    """Müşteri çıktı şeması - müşteri bilgilerini döndürmek için"""
    id: int  # Müşteri ID'si
    owner_id: Optional[int]  # Sahip kullanıcı ID'si
    created_at: Optional[datetime]  # Oluşturulma tarihi
    updated_at: Optional[datetime]  # Güncellenme tarihi

    class Config:
        from_attributes = True  # ORM nesnelerinden veri alabilir

# --- Not Şemaları ---
class NoteCreate(BaseModel):
    """Not oluşturma şeması - yeni not ekleme için"""
    content: str  # Not içeriği, zorunlu

class NoteOut(BaseModel):
    """Not çıktı şeması - not bilgilerini döndürmek için"""
    id: int  # Not ID'si
    customer_id: int  # Müşteri ID'si
    content: str  # Not içeriği
    created_by: Optional[int]  # Oluşturan kullanıcı ID'si
    created_at: Optional[datetime]  # Oluşturulma tarihi

    class Config:
        from_attributes = True  # ORM nesnelerinden veri alabilir
