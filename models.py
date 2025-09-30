from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func  # Veritabanı sütun türleri ve fonksiyonlar
from sqlalchemy.ext.declarative import declarative_base  # Model taban sınıfı için
from sqlalchemy.orm import relationship  # Tablolar arası ilişkiler için

# Tüm model sınıfları için temel sınıf
Base = declarative_base()

class User(Base):
    """Kullanıcı modeli - sistem kullanıcılarını temsil eder"""
    __tablename__ = "users"  # Veritabanı tablo adı
    id = Column(Integer, primary_key=True, index=True)  # Birincil anahtar, indeksli
    email = Column(String, unique=True, index=True, nullable=False)  # E-posta, benzersiz, indeksli, zorunlu
    hashed_password = Column(String, nullable=False)  # Hash'lenmiş şifre, zorunlu
    full_name = Column(String, nullable=True)  # Tam ad, isteğe bağlı
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Oluşturulma tarihi, otomatik

    # İlişkiler - bir kullanıcının birden fazla müşterisi olabilir
    customers = relationship("Customer", back_populates="owner")

class Customer(Base):
    """Müşteri modeli - CRM müşterilerini temsil eder"""
    __tablename__ = "customers"  # Veritabanı tablo adı
    id = Column(Integer, primary_key=True, index=True)  # Birincil anahtar, indeksli
    name = Column(String, nullable=False)  # Müşteri adı, zorunlu
    email = Column(String, nullable=True)  # E-posta, isteğe bağlı
    phone = Column(String, nullable=True)  # Telefon, isteğe bağlı
    company = Column(String, nullable=True)  # Şirket, isteğe bağlı
    status = Column(String, nullable=True, default="Active")  # Müşteri durumu, varsayılan "Active"
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
