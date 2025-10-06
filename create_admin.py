#!/usr/bin/env python3
"""
FastCRM Admin User Creator
İlk admin kullanıcısını oluşturmak için script
"""

import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from auth import get_password_hash

def create_admin_user():
    """İlk admin kullanıcısını oluşturur"""
    
    # Veritabanı tablolarını oluştur
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Mevcut admin var mı kontrol et
        existing_admin = db.query(models.User).filter(
            models.User.role == models.UserRole.ADMIN
        ).first()
        
        if existing_admin:
            print(f"✅ Admin user already exists: {existing_admin.email}")
            return existing_admin
        
        # Admin kullanıcı bilgileri
        admin_email = input("Admin email: ").strip()
        if not admin_email:
            admin_email = "admin@fastcrm.com"
            
        admin_password = input("Admin password (min 8 chars): ").strip()
        if not admin_password:
            admin_password = "admin123456"
            
        admin_name = input("Admin full name (optional): ").strip()
        if not admin_name:
            admin_name = "System Administrator"
        
        # Şifreyi hash'le
        hashed_password = get_password_hash(admin_password)
        
        # Admin kullanıcı oluştur
        admin_user = models.User(
            email=admin_email,
            hashed_password=hashed_password,
            full_name=admin_name,
            role=models.UserRole.ADMIN,
            is_active="true"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # OAuth2 Client Credentials oluştur
        import secrets
        import uuid
        client_id = f"fcrm_{uuid.uuid4().hex[:16]}"
        client_secret = secrets.token_urlsafe(32)
        
        oauth2_client = models.OAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            user_id=admin_user.id,
            is_active="true"
        )
        db.add(oauth2_client)
        db.commit()
        
        print(f"🎉 Admin user created successfully!")
        print(f"📧 Email: {admin_user.email}")
        print(f"👤 Name: {admin_user.full_name}")
        print(f"👑 Role: {admin_user.role.value}")
        print(f"🆔 ID: {admin_user.id}")
        print(f"🔑 OAuth2 Client ID: {client_id}")
        print(f"🔐 OAuth2 Client Secret: {client_secret}")
        print(f"⚠️  Save these OAuth2 credentials securely!")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def create_sample_users():
    """Örnek kullanıcılar oluşturur - OAuth2 client credentials ile"""
    import secrets
    import uuid
    
    db = SessionLocal()
    try:
        created_any = False

        # Premium user
        existing_premium = db.query(models.User).filter(
            models.User.email == "premium@fastcrm.com"
        ).first()
        if not existing_premium:
            premium_user = models.User(
                email="premium@fastcrm.com",
                hashed_password=get_password_hash("premium123"),
                full_name="Premium User",
                role=models.UserRole.PREMIUM_USER,
                is_active="true"
            )
            db.add(premium_user)
            db.commit()
            db.refresh(premium_user)
            
            # OAuth2 Client Credentials oluştur
            client_id = f"fcrm_{uuid.uuid4().hex[:16]}"
            client_secret = secrets.token_urlsafe(32)
            
            oauth2_client = models.OAuth2Client(
                client_id=client_id,
                client_secret=client_secret,
                user_id=premium_user.id,
                is_active="true"
            )
            db.add(oauth2_client)
            created_any = True
        else:
            print("ℹ️ Premium user already exists: premium@fastcrm.com")

        # Basic user
        existing_basic = db.query(models.User).filter(
            models.User.email == "basic@fastcrm.com"
        ).first()
        if not existing_basic:
            basic_user = models.User(
                email="basic@fastcrm.com",
                hashed_password=get_password_hash("basic123"),
                full_name="Basic User",
                role=models.UserRole.BASIC_USER,
                is_active="true"
            )
            db.add(basic_user)
            db.commit()
            db.refresh(basic_user)
            
            # OAuth2 Client Credentials oluştur
            client_id = f"fcrm_{uuid.uuid4().hex[:16]}"
            client_secret = secrets.token_urlsafe(32)
            
            oauth2_client = models.OAuth2Client(
                client_id=client_id,
                client_secret=client_secret,
                user_id=basic_user.id,
                is_active="true"
            )
            db.add(oauth2_client)
            created_any = True
        else:
            print("ℹ️ Basic user already exists: basic@fastcrm.com")

        if created_any:
            db.commit()
            print(f"✅ Sample users ensured with OAuth2 credentials:")
            print(f"  📧 Premium: premium@fastcrm.com / premium123")
            print(f"  📧 Basic: basic@fastcrm.com / basic123")
            print(f"  🔑 Each user has OAuth2 client credentials for API access")
        else:
            print("✅ Sample users already exist. No changes made.")
        
    except Exception as e:
        print(f"❌ Error creating sample users: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Ana fonksiyon"""
    print("🚀 FastCRM Admin User Creator")
    print("=" * 40)
    
    # Admin kullanıcı oluştur
    admin = create_admin_user()
    
    if admin:
        # Örnek kullanıcılar oluşturmak istiyor mu?
        create_samples = input("\nCreate sample users? (y/N): ").strip().lower()
        if create_samples in ['y', 'yes']:
            create_sample_users()
        
        print("\n🎯 Next steps:")
        print("1. Start the server: python -m uvicorn main:app --reload")
        print("2. Go to: http://localhost:8000")
        print("3. Login with admin credentials")
        print("4. Access admin panel: http://localhost:8000/docs")
        print("5. Look for '👑 Admin Management' section")
        
    else:
        print("❌ Failed to create admin user")
        sys.exit(1)

if __name__ == "__main__":
    main()
