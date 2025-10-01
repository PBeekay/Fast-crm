"""
Admin Router
Admin kullanıcı yönetimi endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

import models
import schemas
from dependencies import get_db, get_admin_user, get_user

# Router oluştur
router = APIRouter(
    prefix="/api/admin",
    tags=["👑 Admin Management"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger("fastcrm")

@router.get("/users", response_model=List[schemas.UserOut])
def list_all_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    """Tüm kullanıcıları listeler (sadece admin)"""
    logger.info(f"👑 Admin {admin_user.email} listing all users")
    
    users = db.query(models.User).offset(skip).limit(limit).all()
    logger.info(f"📋 Listed {len(users)} users")
    return users

@router.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user_by_id(
    user_id: int, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    """Belirli bir kullanıcıyı getirir (sadece admin)"""
    logger.info(f"👑 Admin {admin_user.email} getting user ID: {user_id}")
    
    user = get_user(db, user_id)
    if not user:
        logger.warning(f"❌ User not found: ID {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"✅ User retrieved: {user.email} (ID: {user.id})")
    return user

@router.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int, 
    user_update: schemas.UserUpdate, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    """Kullanıcı bilgilerini günceller (sadece admin)"""
    logger.info(f"👑 Admin {admin_user.email} updating user ID: {user_id}")
    
    user = get_user(db, user_id)
    if not user:
        logger.warning(f"❌ User not found: ID {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Kendini deaktif edemez
    if user_id == admin_user.id and user_update.is_active == "false":
        logger.warning(f"❌ Admin cannot deactivate themselves: {admin_user.email}")
        raise HTTPException(
            status_code=400, 
            detail="Cannot deactivate your own account"
        )
    
    # Sadece sağlanan alanları güncelle
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"✅ User updated: {user.email} (ID: {user.id})")
    return user

@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    """Kullanıcıyı siler (sadece admin)"""
    logger.info(f"👑 Admin {admin_user.email} deleting user ID: {user_id}")
    
    # Kendini silemez
    if user_id == admin_user.id:
        logger.warning(f"❌ Admin cannot delete themselves: {admin_user.email}")
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete your own account"
        )
    
    user = get_user(db, user_id)
    if not user:
        logger.warning(f"❌ User not found: ID {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    user_email = user.email
    db.delete(user)
    db.commit()
    
    logger.info(f"✅ User deleted: {user_email} (ID: {user_id})")
    return

@router.get("/customers", response_model=List[schemas.CustomerOut])
def list_all_customers(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    """Tüm müşterileri listeler (sadece admin)"""
    logger.info(f"👑 Admin {admin_user.email} listing all customers")
    
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    logger.info(f"📋 Listed {len(customers)} customers")
    return customers

@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    """Admin istatistikleri"""
    logger.info(f"👑 Admin {admin_user.email} getting stats")
    
    try:
        # Kullanıcı istatistikleri
        total_users = db.query(models.User).count()
        active_users = db.query(models.User).filter(models.User.is_active == "true").count()
        basic_users = db.query(models.User).filter(models.User.role == models.UserRole.BASIC_USER).count()
        premium_users = db.query(models.User).filter(models.User.role == models.UserRole.PREMIUM_USER).count()
        admin_users = db.query(models.User).filter(models.User.role == models.UserRole.ADMIN).count()
        
        # Müşteri istatistikleri
        total_customers = db.query(models.Customer).count()
        active_customers = db.query(models.Customer).filter(
            models.Customer.status == models.CustomerStatus.ACTIVE
        ).count()
        
        # Not istatistikleri
        total_notes = db.query(models.Note).count()
        
        # Token istatistikleri
        active_tokens = db.query(models.RefreshToken).filter(
            models.RefreshToken.is_active == "true"
        ).count()
        
        # Son 24 saatteki aktivite
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_users = db.query(models.User).filter(
            models.User.created_at >= yesterday
        ).count()
        
        recent_customers = db.query(models.Customer).filter(
            models.Customer.created_at >= yesterday
        ).count()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "by_role": {
                    "basic": basic_users,
                    "premium": premium_users,
                    "admin": admin_users
                }
            },
            "customers": {
                "total": total_customers,
                "active": active_customers
            },
            "notes": {
                "total": total_notes
            },
            "sessions": {
                "active_tokens": active_tokens
            },
            "recent_activity": {
                "new_users_24h": recent_users,
                "new_customers_24h": recent_customers
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Admin stats error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Could not retrieve admin statistics"
        )

@router.post("/users/{user_id}/promote")
def promote_user(
    user_id: int, 
    target_role: schemas.UserRoleEnum, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    """Kullanıcı rolünü yükseltir"""
    logger.info(f"👑 Admin {admin_user.email} promoting user {user_id} to {target_role.value}")
    
    user = get_user(db, user_id)
    if not user:
        logger.warning(f"❌ User not found: ID {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.role
    user.role = models.UserRole(target_role.value)
    db.commit()
    db.refresh(user)
    
    logger.info(f"✅ User role updated: {user.email} ({old_role.value} → {target_role.value})")
    return {
        "message": f"User role updated successfully",
        "user_email": user.email,
        "old_role": old_role.value,
        "new_role": target_role.value
    }

@router.post("/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    """Kullanıcı durumunu aktif/pasif yapar"""
    logger.info(f"👑 Admin {admin_user.email} toggling status for user {user_id}")
    
    # Kendini deaktif edemez
    if user_id == admin_user.id:
        logger.warning(f"❌ Admin cannot toggle their own status: {admin_user.email}")
        raise HTTPException(
            status_code=400, 
            detail="Cannot change your own account status"
        )
    
    user = get_user(db, user_id)
    if not user:
        logger.warning(f"❌ User not found: ID {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Durumu değiştir
    new_status = "false" if user.is_active == "true" else "true"
    user.is_active = new_status
    db.commit()
    db.refresh(user)
    
    status_text = "activated" if new_status == "true" else "deactivated"
    logger.info(f"✅ User {status_text}: {user.email}")
    
    return {
        "message": f"User {status_text} successfully",
        "user_email": user.email,
        "is_active": new_status == "true"
    }
