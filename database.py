from sqlalchemy import create_engine  # Veritabanı motoru oluşturmak için
from sqlalchemy.orm import sessionmaker  # Veritabanı oturumu oluşturmak için
import os  # Ortam değişkenleri için

# Veritabanı URL'i - ortam değişkeninden al veya varsayılan SQLite kullan
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crm.db")

# SQLite için özel bağlantı argümanları
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Veritabanı motorunu oluştur - bağlantı argümanları ile
engine = create_engine(DATABASE_URL, connect_args=connect_args)
# Veritabanı oturum fabrikası oluştur - otomatik commit ve flush kapalı
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
