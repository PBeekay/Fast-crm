# FastCRM

Modern ve hızlı bir FastAPI tabanlı CRM MVP uygulaması. Kullanıcı yönetimi, müşteri takibi ve not sistemi ile tam özellikli bir CRM çözümü.

## ✨ Özellikler

### 🔐 Kimlik Doğrulama
- JWT tabanlı güvenli kullanıcı kaydı ve girişi
- Şifre hashleme (bcrypt)
- Token tabanlı API erişimi

### 👥 Müşteri Yönetimi
- Müşteri oluşturma, listeleme, görüntüleme ve silme
- Müşteri bilgileri (ad, email, telefon, şirket)
- Kullanıcı bazlı müşteri izolasyonu

### 📝 Not Sistemi
- Müşterilere not ekleme ve listeleme
- Not silme işlemleri
- Zaman damgalı not takibi

### 🎨 Modern Frontend
- Responsive ve modern kullanıcı arayüzü
- Tek sayfa uygulaması (SPA)
- Gerçek zamanlı veri güncellemeleri

### 📊 Logging ve Monitoring
- Detaylı HTTP istek/yanıt logları
- İşlem süreleri ve performans metrikleri
- Hata takibi ve güvenlik logları

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.10+ (3.13 önerilir)
- pip

### Kurulum
```bash
# Projeyi klonlayın
git clone <repository-url>
cd fastcrm

# Sanal ortam oluşturun (önerilir)
python -m venv venv

# Sanal ortamı aktifleştirin
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### Ortam Değişkenleri
`.env` dosyası oluşturun:
```bash
cp env.example .env
```

`.env` dosyasını düzenleyin:
```env
CRM_SECRET_KEY=your_very_secure_secret_key_here
DATABASE_URL=sqlite:///./crm.db
```

### Çalıştırma
```bash
# Geliştirme modu
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Uygulama çalıştığında:
- **Frontend**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Register**: http://localhost:8000/register

## 📚 API Dokümantasyonu

### Kimlik Doğrulama
- `POST /api/register` - Kullanıcı kaydı
- `POST /api/token` - Giriş yapma (JWT token al)
- `GET /api/me` - Mevcut kullanıcı bilgileri

### Müşteri İşlemleri
- `POST /api/customers` - Yeni müşteri oluştur
- `GET /api/customers` - Müşterileri listele
- `GET /api/customers/{id}` - Belirli müşteriyi getir
- `DELETE /api/customers/{id}` - Müşteriyi sil

### Not İşlemleri
- `POST /api/customers/{id}/notes` - Müşteriye not ekle
- `GET /api/customers/{id}/notes` - Müşteri notlarını listele
- `DELETE /api/customers/{id}/notes/{note_id}` - Notu sil

## 🏗️ Proje Yapısı

```
fastcrm/
├── main.py              # Ana FastAPI uygulaması
├── models.py            # SQLAlchemy veritabanı modelleri
├── schemas.py           # Pydantic şemaları
├── database.py          # Veritabanı bağlantısı
├── auth.py              # Kimlik doğrulama fonksiyonları
├── requirements.txt     # Python bağımlılıkları
├── env.example          # Ortam değişkenleri örneği
├── .gitignore           # Git ignore kuralları
├── README.md            # Bu dosya
└── static/              # Frontend dosyaları
    ├── index.html       # Ana sayfa
    ├── register.html    # Kayıt sayfası
    ├── app.js           # Ana JavaScript
    ├── register.js      # Kayıt JavaScript
    └── style.css        # CSS stilleri
```

## 🔧 Geliştirme

### Veritabanı
- Varsayılan: SQLite (`crm.db`)
- PostgreSQL, MySQL vb. için `DATABASE_URL` değiştirin
- Otomatik tablo oluşturma

### Logging
- Tüm HTTP istekleri loglanır
- İşlem süreleri ve durum kodları
- Emoji tabanlı görsel loglar

### Güvenlik
- JWT token tabanlı kimlik doğrulama
- Şifre hashleme (bcrypt)
- Kullanıcı bazlı veri izolasyonu

## 🚀 Deployment

### Production Ayarları
1. `CRM_SECRET_KEY` değerini güçlü bir değerle değiştirin
2. `DATABASE_URL` değerini production veritabanına ayarlayın
3. HTTPS kullanın
4. Environment variables ile konfigürasyonu yönetin

### Docker (Opsiyonel)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📞 İletişim

Sorularınız için issue açabilir veya iletişime geçebilirsiniz.

