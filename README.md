# FastCRM

Basit bir FastAPI tabanlı CRM MVP uygulaması.

## Özellikler
- Kullanıcı kaydı ve JWT ile oturum açma
- Müşteri oluşturma, listeleme, görüntüleme ve silme
- Müşteri notları ekleme ve listeleme

## Gereksinimler
- Python 3.13 (veya 3.10+)
- Pip

## Kurulum
```bash
# Sanal ortam (opsiyonel ama tavsiye edilir)
python -m venv venv
./venv/Scripts/activate  # Windows PowerShell

# Bağımlılıkları yükle
pip install -r requirements.txt
```

## Ortam Değişkenleri
`.env` dosyası oluşturup aşağıdakileri tanımlayın (örnek için `env.example` dosyasına bakın):
- `CRM_SECRET_KEY`: JWT için gizli anahtar (rastgele güçlü bir değer kullanın)
- `DATABASE_URL`: Varsayılan `sqlite:///./crm.db`

## Çalıştırma
```bash
# Geliştirme
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Uygulama ayakta olduğunda Swagger dokümantasyonu:
- `http://localhost:8000/docs`

## API Akışı (Hızlı Başlangıç)
1. `POST /register` ile kullanıcı oluşturun
2. `POST /token` ile `access_token` alın
3. `GET /me` ile token doğrulayın
4. `POST /customers` ile müşteri oluşturun
5. `GET /customers` ile müşterileri listeleyin
6. `POST /customers/{id}/notes` ile not ekleyin

## Veritabanı
Varsayılan olarak SQLite kullanır. Başka bir veritabanı kullanmak için `DATABASE_URL` değerini değiştirin.

## Notlar
- Üretimde `CRM_SECRET_KEY` değerini mutlaka değiştirin.
- `auth.py`, `models.py`, `schemas.py`, `database.py` ve `main.py` dosyaları satır içi Türkçe yorumlarla açıklanmıştır.

