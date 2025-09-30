from pydantic import BaseModel, EmailStr, validator  # Veri doğrulama ve e-posta formatı için
from typing import Optional, List  # Tip belirteçleri için
from datetime import datetime  # Tarih ve zaman işlemleri için

# --- Kullanıcı Şemaları ---
class UserCreate(BaseModel):
    """Kullanıcı oluşturma şeması - yeni kullanıcı kaydı için"""
    email: EmailStr  # E-posta adresi, doğrulanmış format
    password: str  # Şifre
    full_name: Optional[str] = None  # Tam ad, isteğe bağlı
    
    @validator('password')
    def validate_password(cls, v):
        """Şifre doğrulama - bcrypt 72 byte limiti için"""
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 characters due to security limitations')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserOut(BaseModel):
    """Kullanıcı çıktı şeması - kullanıcı bilgilerini döndürmek için"""
    id: int  # Kullanıcı ID'si
    email: EmailStr  # E-posta adresi
    full_name: Optional[str]  # Tam ad
    created_at: Optional[datetime]  # Oluşturulma tarihi

    class Config:
        from_attributes = True  # ORM nesnelerinden veri alabilir

# --- Token Şemaları ---
class Token(BaseModel):
    """JWT token şeması - kimlik doğrulama token'ı için"""
    access_token: str  # Erişim token'ı
    refresh_token: str  # Yenileme token'ı
    token_type: str = "bearer"  # Token türü, varsayılan "bearer"
    expires_in: int = 1440  # Access token geçerlilik süresi (dakika)

class TokenRefresh(BaseModel):
    """Token yenileme şeması"""
    refresh_token: str  # Yenileme token'ı

class RefreshTokenOut(BaseModel):
    """Refresh token çıktı şeması"""
    id: int
    token: str
    user_id: int
    expires_at: datetime
    is_active: str
    created_at: datetime
    last_used_at: Optional[datetime]
    device_info: Optional[str]

    class Config:
        from_attributes = True

# --- Müşteri Şemaları ---
class CustomerBase(BaseModel):
    """Müşteri temel şeması - ortak müşteri alanları"""
    name: str  # Müşteri adı, zorunlu
    email: Optional[EmailStr] = None  # E-posta, isteğe bağlı
    phone: Optional[str] = None  # Telefon, isteğe bağlı
    company: Optional[str] = None  # Şirket, isteğe bağlı
    status: Optional[str] = "Active"  # Müşteri durumu, varsayılan "Active"

class CustomerCreate(CustomerBase):
    """Müşteri oluşturma şeması - yeni müşteri ekleme için"""
    pass  # Temel şemadan tüm alanları al

class CustomerUpdate(BaseModel):
    """Müşteri güncelleme şeması - müşteri düzenleme için"""
    name: Optional[str] = None  # Müşteri adı, isteğe bağlı
    email: Optional[EmailStr] = None  # E-posta, isteğe bağlı
    phone: Optional[str] = None  # Telefon, isteğe bağlı
    company: Optional[str] = None  # Şirket, isteğe bağlı
    status: Optional[str] = None  # Müşteri durumu, isteğe bağlı

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
