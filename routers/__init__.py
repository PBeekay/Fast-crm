"""
FastCRM Routers Package
Modüler API endpoint'leri
"""

from .auth import router as auth_router
from .customers import router as customers_router
from .notes import router as notes_router
from .system import router as system_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "customers_router", 
    "notes_router",
    "system_router",
    "admin_router"
]
