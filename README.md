## 🇹🇷 Türkçe Kullanım Rehberi

### 📖 **Adım Adım Kurulum**

#### **1. Projeyi Klonlayın**
```bash
git clone <repository-url>
cd Fast-crm
```

#### **2. Sanal Ortam Oluşturun**
```bash
# Sanal ortamı oluştur
python -m venv venv

# Windows için aktifleştir
venv\Scripts\activate

# Linux/Mac için
source venv/bin/activate
```

#### **3. Bağımlılıkları Yükleyin**
```bash
pip install -r requirements.txt
```

#### **4. Ortam Değişkenlerini Ayarlayın**
```bash
# env.example'ı kopyalayın
copy env.example .env  # Windows
cp env.example .env    # Linux/Mac

# Güvenli bir gizli anahtar oluşturun
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Çıktıyı kopyalayın ve .env dosyasında CRM_SECRET_KEY değerini güncelleyin
```

**Örnek .env dosyası:**
```env
CRM_SECRET_KEY=sizin_güvenli_anahtarınız_buraya
DATABASE_URL=sqlite:///./crm.db
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
ENVIRONMENT=development
```

#### **5. İlk Admin Hesabını Oluşturun**
```bash
python create_admin.py
```

**Script sizden şunları soracak:**
- E-posta adresi (örn: admin@example.com)
- Şifre (en az 8 karakter)
- Tam adınız

**Çıktı örneği:**
```
Admin kullanıcısı başarıyla oluşturuldu!
E-posta: admin@example.com
Client ID: fcrm_abc123def456
Client Secret: xyz789_guvenlı_secret
```

⚠️ **ÖNEMLİ**: Client ID ve Secret'ı kaydedin! API erişimi için gerekli.

#### **6. Sunucuyu Başlatın**
```bash
# Geliştirme modunda
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# veya Windows'ta
start_server.bat

# veya Python script ile
python start_server.py
```

#### **7. Uygulamaya Erişin**
- **Ana Sayfa**: http://localhost:8000
- **API Dokümantasyonu**: http://localhost:8000/docs
- **Alternatif Dokümantasyon**: http://localhost:8000/redoc

---

### 👤 **Kullanıcı İşlemleri**

#### **Yeni Hesap Oluşturma**

**Web Arayüzü ile:**
1. http://localhost:8000 adresine gidin
2. **"Register"** butonuna tıklayın
3. Formu doldurun:
   - E-posta adresi
   - Şifre (en az 8 karakter)
   - Tam adınız
4. **"Register"** butonuna tıklayın
5. Otomatik olarak giriş sayfasına yönlendirileceksiniz

**API ile:**
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "guvenli_sifre123",
    "full_name": "Ahmet Yılmaz"
  }'
```

**Cevap:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Ahmet Yılmaz",
    "role": "basic_user",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Kayıt başarılı! Artık giriş yapabilirsiniz."
}
```

#### **Giriş Yapma**

**Web Arayüzü ile:**
1. Ana sayfada e-posta ve şifrenizi girin
2. **"Login"** butonuna tıklayın
3. Başarılı girişten sonra dashboard açılacak

**API ile:**
```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=guvenli_sifre123"
```

**Cevap:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "abc123def456...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### 🎭 **Kullanıcı Rolleri ve Yetkileri**

#### **1. Basic User (Temel Kullanıcı)**
- ✅ Kendi profilini görüntüleyebilir
- ✅ Şifresini değiştirebilir
- ❌ Müşteri ekleyemez
- ❌ Not oluşturamaz

**Kayıt olduğunuzda otomatik olarak bu role sahip olursunuz.**

#### **2. Premium User (Premium Kullanıcı)**
- ✅ Basic User'ın tüm yetkileri
- ✅ Müşteri ekleyebilir
- ✅ Müşterilerini düzenleyebilir
- ✅ Müşterilerine not ekleyebilir
- ❌ Diğer kullanıcıları göremez/düzenleyemez

**Bu role nasıl yükseltilirsiniz:**
- Admin bir kullanıcıyı premium'a yükseltmelidir
- Veya ödeme sistemi entegre edilirse (gelecek özellik)

#### **3. Admin (Yönetici)**
- ✅ Premium User'ın tüm yetkileri
- ✅ Tüm kullanıcıları görüntüleyebilir
- ✅ Kullanıcıların rollerini değiştirebilir
- ✅ Kullanıcıları aktif/pasif yapabilir
- ✅ Kullanıcı silebilir
- ✅ Tüm müşterileri görüntüleyebilir
- ✅ Sistem istatistiklerini görebilir

---

### 👑 **Admin İşlemleri**

#### **Kullanıcıyı Premium'a Yükseltme**

**API Dokümantasyonu üzerinden (Önerilen):**
1. http://localhost:8000/docs adresine gidin
2. Admin hesabı ile giriş yapın (Authorize butonu)
3. **"Admin Management"** bölümünü bulun
4. **POST /api/admin/users/{user_id}/promote** endpoint'ini açın
5. `user_id` girin (örn: 2)
6. Request body:
   ```json
   {
     "target_role": "premium_user"
   }
   ```
7. **"Execute"** butonuna tıklayın

**Komut satırı ile:**
```bash
curl -X POST "http://localhost:8000/api/admin/users/2/promote" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN_BURAYA" \
  -d '{"target_role": "premium_user"}'
```

#### **Kullanıcıyı Admin'e Yükseltme**

⚠️ **DİKKAT**: Sadece mevcut adminler yeni admin oluşturabilir!

**Yöntem 1: API ile**
```bash
curl -X POST "http://localhost:8000/api/admin/users/2/promote" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"target_role": "admin"}'
```

**Yöntem 2: Script ile**
```bash
python create_admin.py
```
Bu komut tamamen yeni bir admin hesabı oluşturur.

#### **Kullanıcıyı Aktif/Pasif Yapma**

```bash
curl -X POST "http://localhost:8000/api/admin/users/2/toggle-status" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

#### **Tüm Kullanıcıları Listeleme**

```bash
curl -X GET "http://localhost:8000/api/admin/users" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

### 👥 **Müşteri Yönetimi**

⚠️ **NOT**: Müşteri işlemleri için **Premium** veya **Admin** rolüne sahip olmalısınız!

#### **Müşteri Ekleme**

**Web Arayüzü ile:**
1. Giriş yapın (Premium veya Admin hesap)
2. Dashboard'da **"Add Customer"** butonuna tıklayın
3. Formu doldurun:
   - Ad
   - E-posta
   - Telefon
   - Şirket
   - Durum (Active/Inactive/Pending)
4. **"Save"** butonuna tıklayın

**API ile:**
```bash
curl -X POST "http://localhost:8000/api/customers" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Mehmet Demir",
    "email": "mehmet@example.com",
    "phone": "+90 555 123 4567",
    "company": "Demir AŞ",
    "status": "active"
  }'
```

#### **Müşteri Düzenleme**

**Web Arayüzü ile:**
1. Müşteri listesinde düzenlemek istediğiniz müşterinin yanındaki **"Edit"** butonuna tıklayın
2. Bilgileri güncelleyin
3. **"Update"** butonuna tıklayın

**API ile:**
```bash
curl -X PUT "http://localhost:8000/api/customers/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Mehmet Demir",
    "email": "mehmet.yeni@example.com",
    "phone": "+90 555 999 8888",
    "company": "Demir Holding",
    "status": "active"
  }'
```

#### **Müşteri Silme**

```bash
curl -X DELETE "http://localhost:8000/api/customers/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 📝 **Not Sistemi**

#### **Müşteriye Not Ekleme**

**Web Arayüzü ile:**
1. Müşteri detay sayfasına gidin
2. **"Add Note"** butonuna tıklayın
3. Not içeriğini yazın
4. **"Save"** butonuna tıklayın

**API ile:**
```bash
curl -X POST "http://localhost:8000/api/customers/1/notes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "content": "Müşteri ile görüşme yapıldı. Yeni proje için teklif hazırlanacak."
  }'
```

#### **Notları Listeleme**

```bash
curl -X GET "http://localhost:8000/api/customers/1/notes" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 📊 **Dashboard ve İstatistikler**

#### **Kendi İstatistiklerinizi Görme (Tüm Kullanıcılar)**

```bash
curl -X GET "http://localhost:8000/api/system/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### **Sistem Geneli İstatistikler (Sadece Admin)**

```bash
curl -X GET "http://localhost:8000/api/admin/stats" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Dönen Bilgiler:**
- Toplam kullanıcı sayısı
- Aktif kullanıcı sayısı
- Toplam müşteri sayısı
- Rol dağılımı
- Son aktiviteler

---

### 🔐 **Güvenlik İpuçları**

#### **Güçlü Şifre Oluşturma**
- En az 8 karakter
- Büyük ve küçük harf karışımı
- Sayı içermeli
- Özel karakter içermeli (!, @, #, $, vb.)

**Örnek güçlü şifreler:**
- `Crm@2024!Guvenli`
- `MyP@ssw0rd!123`
- `Admin#Secure$99`

#### **Token Güvenliği**
- Access token'ları güvenli bir yerde saklayın
- Token'ları kimseyle paylaşmayın
- Token süresi dolduğunda refresh token ile yenileyin

#### **Hesap Güvenliği**
- Admin şifrelerini düzenli olarak değiştirin
- Gereksiz admin hesapları oluşturmayın
- Kullanılmayan hesapları pasif yapın

---

### 🎨 **Arayüz Özellikleri**

#### **Dark/Light Tema**
- **Tema Değiştirme**: Sağ üstteki ay/güneş ikonuna tıklayın
- **Klavye Kısayolu**: `Ctrl + T`
- Seçilen tema tarayıcıda kaydedilir

#### **Mobil Uyumlu**
- Tüm cihazlarda sorunsuz çalışır
- Dokunmatik ekranlar için optimize edilmiştir
- Responsive tasarım

#### **Klavye Kısayolları**
- `Ctrl + T`: Tema değiştir
- `Esc`: Modal/form kapat

---

### 🚨 **Sorun Giderme**

#### **"CRM_SECRET_KEY must be set" Hatası**
```bash
# .env dosyasını kontrol edin
# CRM_SECRET_KEY satırının doğru ayarlandığından emin olun

# Yeni bir key oluşturun:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Çıktıyı .env dosyasına ekleyin
```

#### **"Database locked" Hatası**
```bash
# Sunucuyu durdurun
# crm.db dosyasını silin
# Sunucuyu tekrar başlatın (otomatik olarak yeniden oluşturulacak)

rm crm.db  # Linux/Mac
del crm.db  # Windows
```

#### **Admin Hesabına Erişemiyorum**
```bash
# Yeni bir admin hesabı oluşturun
python create_admin.py
```

#### **Port 8000 Kullanımda**
```bash
# Farklı bir port kullanın
python -m uvicorn main:app --reload --port 8001
```

---

### 📞 **Destek ve İletişim**

- **API Dokümantasyonu**: http://localhost:8000/docs
- **GitHub Issues**: Sorunlarınızı GitHub'da bildirin
- **E-posta**: Projenizin destek e-postası

---

**FastCRM** - Modern, Secure, and Scalable CRM Solution 🚀