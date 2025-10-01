#!/usr/bin/env python3
"""
Quick script to make a user admin (non-interactive)
Usage: python make_admin.py <user_email>
Example: python make_admin.py admin@example.com
"""

import sys
from database import SessionLocal
import models

def make_admin(email: str):
    """Make a user admin by email"""
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            print("\n📋 Available users:")
            users = db.query(models.User).all()
            for u in users:
                print(f"  - {u.email} (Role: {u.role.value})")
            return False
        
        if user.role == models.UserRole.ADMIN:
            print(f"✅ User {email} is already an admin!")
            return True
        
        old_role = user.role.value
        user.role = models.UserRole.ADMIN
        db.commit()
        
        print(f"✅ User promoted to admin!")
        print(f"📧 Email: {email}")
        print(f"🔄 Role: {old_role} → admin")
        print(f"\n🎯 How to use in FastAPI Docs:")
        print(f"1. Go to: http://localhost:8000/docs")
        print(f"2. Click 'Authorize' button (🔓 at top right)")
        print(f"3. Username: {email}")
        print(f"4. Password: <your password>")
        print(f"5. Click 'Authorize'")
        print(f"6. Now you can execute admin endpoints!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        # Default to admin@example.com if no argument
        email = "admin@example.com"
        print(f"No email provided, using default: {email}")
    
    make_admin(email)

