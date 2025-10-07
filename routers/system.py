"""
System Router
Sistem yönetimi ve debug endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
import time
import os

import models
from dependencies import get_db
from database import DATABASE_URL

# Router oluştur
router = APIRouter(
    prefix="/api/system",
    tags=["🛠️ System & Debug"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger("fastcrm")

@router.get("/health")
async def health_check():
    """System health check endpoint"""
    try:
        # Test database connection
        from database import SessionLocal
        db = SessionLocal()
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            db_status = "connected"
            
            # Check table existence
            user_count = db.query(models.User).count()
            customer_count = db.query(models.Customer).count()
            token_count = db.query(models.RefreshToken).count()
            
            return {
                "status": "healthy",
                "message": "FastCRM API is running",
                "timestamp": time.time(),
                "database": {
                    "status": db_status,
                    "users": user_count,
                    "customers": customer_count,
                    "refresh_tokens": token_count
                }
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}",
            "timestamp": time.time(),
            "database": {
                "status": "error",
                "error": str(e)
            }
        }

@router.get("/debug/database")
async def debug_database():
    """Database debug information - SECURITY: Only available in development"""
    import os
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404, detail="Debug endpoint not available in production")
    
    try:
        db_file_path = "crm.db"
        
        return {
            "database_url": DATABASE_URL,
            "database_file_exists": os.path.exists(db_file_path),
            "database_file_size": os.path.getsize(db_file_path) if os.path.exists(db_file_path) else 0,
            "working_directory": os.getcwd(),
            "environment": {
                "DATABASE_URL": os.getenv("DATABASE_URL", "not_set"),
                "CRM_SECRET_KEY": "SET" if os.getenv("CRM_SECRET_KEY") else "NOT_SET"
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Debug information could not be retrieved"
        }

@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Sistem istatistikleri"""
    try:
        # Veritabanı istatistikleri
        total_users = db.query(models.User).count()
        total_customers = db.query(models.Customer).count()
        total_notes = db.query(models.Note).count()
        active_tokens = db.query(models.RefreshToken).filter(
            models.RefreshToken.is_active == "true"
        ).count()
        
        # Son 24 saatteki aktivite (basit versiyon)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_users = db.query(models.User).filter(
            models.User.created_at >= yesterday
        ).count()
        
        recent_customers = db.query(models.Customer).filter(
            models.Customer.created_at >= yesterday
        ).count()
        
        recent_notes = db.query(models.Note).filter(
            models.Note.created_at >= yesterday
        ).count()
        
        return {
            "total_stats": {
                "users": total_users,
                "customers": total_customers,
                "notes": total_notes,
                "active_sessions": active_tokens
            },
            "recent_activity": {
                "new_users_24h": recent_users,
                "new_customers_24h": recent_customers,
                "new_notes_24h": recent_notes
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return {
            "error": str(e),
            "message": "Could not retrieve system statistics"
        }

@router.post("/cleanup")
async def cleanup_expired_tokens(db: Session = Depends(get_db)):
    """Süresi dolmuş token'ları temizle"""
    try:
        from dependencies import cleanup_expired_tokens
        deleted_count = cleanup_expired_tokens(db)
        
        logger.info(f"🧹 Cleanup completed: {deleted_count} expired tokens removed")
        return {
            "message": "Cleanup completed successfully",
            "deleted_tokens": deleted_count,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")
        return {
            "error": str(e),
            "message": "Cleanup operation failed"
        }

# Import SessionLocal here to avoid circular imports
from database import SessionLocal
