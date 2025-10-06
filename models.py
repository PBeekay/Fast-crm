from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func, Enum  # Veritabanı sütun türleri ve fonksiyonlar
from sqlalchemy.ext.declarative import declarative_base  # Model taban sınıfı için
from sqlalchemy.orm import relationship  # Tablolar arası ilişkiler için
import enum  # Python enum desteği

# Tüm model sınıfları için temel sınıf
Base = declarative_base()

# Kullanıcı rolleri enum
class UserRole(enum.Enum):
    """Kullanıcı rolleri"""
    BASIC_USER = "basic_user"        # Temel kullanıcı - sadece kendi verilerini görür
    PREMIUM_USER = "premium_user"    # Premium kullanıcı - müşteri ekleyebilir, gelişmiş özellikler
    ADMIN = "admin"                  # Admin - tüm kullanıcıları yönetebilir

# Müşteri durumları enum
class CustomerStatus(enum.Enum):
    """Müşteri durumları"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LEAD = "LEAD"
    PROSPECT = "PROSPECT"
    CONVERTED = "CONVERTED"

class User(Base):
    """Kullanıcı modeli - sistem kullanıcılarını temsil eder"""
    __tablename__ = "users"  # Veritabanı tablo adı
    id = Column(Integer, primary_key=True, index=True)  # Birincil anahtar, indeksli
    email = Column(String, unique=True, index=True, nullable=False)  # E-posta, benzersiz, indeksli, zorunlu
    hashed_password = Column(String, nullable=False)  # Hash'lenmiş şifre, zorunlu
    full_name = Column(String, nullable=True)  # Tam ad, isteğe bağlı
    role = Column(Enum(UserRole), default=UserRole.BASIC_USER, nullable=False)  # Kullanıcı rolü, varsayılan basic_user
    is_active = Column(String, default="true", nullable=False)  # Kullanıcı aktif mi (true/false string)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Oluşturulma tarihi, otomatik
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Güncellenme tarihi, otomatik

    # İlişkiler - bir kullanıcının birden fazla müşterisi olabilir
    customers = relationship("Customer", back_populates="owner")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")  # Refresh token'lar ile ilişki
    oauth2_clients = relationship("OAuth2Client", back_populates="user", cascade="all, delete-orphan")  # OAuth2 client'lar ile ilişki

class Customer(Base):
    """Müşteri modeli - CRM müşterilerini temsil eder"""
    __tablename__ = "customers"  # Veritabanı tablo adı
    id = Column(Integer, primary_key=True, index=True)  # Birincil anahtar, indeksli
    name = Column(String, nullable=False)  # Müşteri adı, zorunlu
    email = Column(String, nullable=True)  # E-posta, isteğe bağlı
    phone = Column(String, nullable=True)  # Telefon, isteğe bağlı
    company = Column(String, nullable=True)  # Şirket, isteğe bağlı
    status = Column(Enum(CustomerStatus), default=CustomerStatus.ACTIVE, nullable=False)  # Müşteri durumu, varsayılan "Active"
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Sahip kullanıcı ID'si, yabancı anahtar
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Oluşturulma tarihi, otomatik
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Güncellenme tarihi, otomatik

    # İlişkiler
    owner = relationship("User", back_populates="customers")  # Sahip kullanıcı ile ilişki
    notes = relationship("Note", back_populates="customer", cascade="all, delete-orphan")  # Notlar ile ilişki, silme kaskadı

class Note(Base):
    """Not modeli - müşteri notlarını temsil eder"""
    __tablename__ = "notes"  # Veritabanı tablo adı
    id = Column(Integer, primary_key=True, index=True)  # Birincil anahtar, indeksli
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)  # Müşteri ID'si, yabancı anahtar, zorunlu
    content = Column(Text, nullable=False)  # Not içeriği, zorunlu
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Oluşturan kullanıcı ID'si, yabancı anahtar
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Oluşturulma tarihi, otomatik

    # İlişkiler
    customer = relationship("Customer", back_populates="notes")  # Müşteri ile ilişki

class RefreshToken(Base):
    """Refresh Token modeli - güvenli token yenileme için"""
    __tablename__ = "refresh_tokens"  # Veritabanı tablo adı
    id = Column(Integer, primary_key=True, index=True)  # Birincil anahtar, indeksli
    token = Column(String, unique=True, index=True, nullable=False)  # Refresh token, benzersiz, indeksli
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Kullanıcı ID'si, yabancı anahtar
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Token son kullanma tarihi
    is_active = Column(String, default="true", nullable=False)  # Token aktif mi (true/false string olarak)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Oluşturulma tarihi
    last_used_at = Column(DateTime(timezone=True), nullable=True)  # Son kullanım tarihi
    device_info = Column(String, nullable=True)  # Cihaz bilgisi (opsiyonel)

    # İlişkiler
    user = relationship("User", back_populates="refresh_tokens")  # Kullanıcı ile ilişki

class OAuth2Client(Base):
    """OAuth2 Client Credentials - API erişimi için"""
    __tablename__ = "oauth2_clients"  # Veritabanı tablo adı
    id = Column(Integer, primary_key=True, index=True)  # Birincil anahtar, indeksli
    client_id = Column(String, unique=True, index=True, nullable=False)  # Client ID, benzersiz, indeksli
    client_secret = Column(String, nullable=False)  # Client Secret, zorunlu
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Kullanıcı ID'si, yabancı anahtar
    is_active = Column(String, default="true", nullable=False)  # Client aktif mi (true/false string)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Oluşturulma tarihi, otomatik
    last_used_at = Column(DateTime(timezone=True), nullable=True)  # Son kullanım tarihi
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Son kullanma tarihi (opsiyonel)

    # İlişkiler
    user = relationship("User", back_populates="oauth2_clients")  # Kullanıcı ile ilişki
