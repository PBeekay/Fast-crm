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
            
        admin_password = input("Admin password (min 6 chars): ").strip()
        if not admin_password:
            admin_password = "admin123"
            
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
        
        print(f"🎉 Admin user created successfully!")
        print(f"📧 Email: {admin_user.email}")
        print(f"👤 Name: {admin_user.full_name}")
        print(f"👑 Role: {admin_user.role.value}")
        print(f"🆔 ID: {admin_user.id}")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def create_sample_users():
    """Örnek kullanıcılar oluşturur"""
    db = SessionLocal()
    try:
        # Premium user
        premium_user = models.User(
            email="premium@fastcrm.com",
            hashed_password=get_password_hash("premium123"),
            full_name="Premium User",
            role=models.UserRole.PREMIUM_USER,
            is_active="true"
        )
        
        # Basic user
        basic_user = models.User(
            email="basic@fastcrm.com",
            hashed_password=get_password_hash("basic123"),
            full_name="Basic User",
            role=models.UserRole.BASIC_USER,
            is_active="true"
        )
        
        db.add(premium_user)
        db.add(basic_user)
        db.commit()
        
        print(f"✅ Sample users created:")
        print(f"  📧 Premium: premium@fastcrm.com / premium123")
        print(f"  📧 Basic: basic@fastcrm.com / basic123")
        
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
