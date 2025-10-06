"""
FastCRM Main Application
Modüler FastAPI uygulaması - Router tabanlı yapı
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import time
import traceback

# Models ve database
import models
from database import engine

# Routers
from routers import auth_router, customers_router, notes_router, system_router, admin_router

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("fastcrm")

# Veritabanı tablolarını oluştur - hata kontrolü ile
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully")
except Exception as e:
    logger.error(f"❌ Database creation failed: {e}")
    raise e

# SECURITY: Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# FastAPI uygulamasını oluştur
app = FastAPI(
    title="🚀 FastCRM",
    description="Modern FastAPI-based CRM application with advanced authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# SECURITY: Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - SECURITY: Restrict origins in production
import os
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
if os.getenv("ENVIRONMENT") == "development":
    ALLOWED_ORIGINS.extend(["http://localhost:8000", "http://127.0.0.1:8000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # SECURITY: No wildcard origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type", 
        "Authorization", 
        "Accept", 
        "Origin", 
        "User-Agent", 
        "Cache-Control"
    ],
)

# SECURITY: Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; img-src 'self' data:; connect-src 'self'"
    
    return response

# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """HTTP isteklerini ve yanıtlarını logla"""
    start_time = time.time()
    
    # Client bilgilerini al
    client_ip = request.client.host if request.client else 'unknown'
    user_agent = request.headers.get('user-agent', 'unknown')[:50]
    
    # İstek bilgilerini logla
    method_emoji = {
        'GET': '📖',
        'POST': '📝', 
        'PUT': '✏️',
        'DELETE': '🗑️',
        'PATCH': '🔧',
        'HEAD': '👁️',
        'OPTIONS': '⚙️'
    }.get(request.method, '🔵')
    
    logger.info(f"{method_emoji} {request.method} {request.url.path} - Client: {client_ip}")
    
    # İsteği işle
    response = await call_next(request)
    
    # Yanıt bilgilerini logla
    process_time = time.time() - start_time
    
    # Status code'a göre emoji
    if response.status_code < 300:
        status_emoji = "🟢"
    elif response.status_code < 400:
        status_emoji = "🟡"
    elif response.status_code < 500:
        status_emoji = "🟠"
    else:
        status_emoji = "🔴"
    
    logger.info(f"{status_emoji} {request.method} {request.url.path} → {response.status_code} ({process_time:.3f}s)")
    
    return response

# Global exception handler - SECURITY: Don't expose internal errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler to ensure JSON responses"""
    logger.error(f"❌ Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # SECURITY: Don't expose internal error details to clients
    return {
            "detail": "Internal server error",
            "path": str(request.url)
        }

# Statik dosyaları servis et
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache-busting middleware for development
@app.middleware("http")
async def add_cache_control_header(request, call_next):
    """Add cache control headers to prevent caching during development"""
    response = await call_next(request)
    
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["ETag"] = str(int(time.time()))
    
    return response

# Ana sayfa ve kayıt sayfası
@app.get("/")
async def read_root():
    """Ana sayfa - giriş ekranını servis et"""
    return FileResponse("static/index.html")

@app.get("/register")
async def read_register():
    """Kayıt sayfası"""
    return FileResponse("static/register.html")

# Router'ları dahil et
app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(notes_router)
app.include_router(system_router)
app.include_router(admin_router)

# Backward compatibility için eski endpoint'leri yönlendir
@app.get("/api/health")
async def health_redirect():
    """Eski health endpoint'ini yeni system/health'e yönlendir"""
    from fastapi import RedirectResponse
    return RedirectResponse(url="/api/system/health")

@app.get("/api/debug/database")
async def debug_redirect():
    """Eski debug endpoint'ini yeni system/debug/database'e yönlendir"""
    from fastapi import RedirectResponse
    return RedirectResponse(url="/api/system/debug/database")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Uygulama başlatma eventi"""
    logger.info("🚀 FastCRM starting up...")
    logger.info("📊 Router endpoints loaded:")
    logger.info("  🔐 Authentication: /api/auth/*")
    logger.info("  👥 Customers: /api/customers/* (Premium+ required)")
    logger.info("  📝 Notes: /api/customers/*/notes/*")
    logger.info("  🛠️ System: /api/system/*")
    logger.info("  👑 Admin: /api/admin/* (Admin only)")
    logger.info("✅ FastCRM ready!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapatma eventi"""
    logger.info("🛑 FastCRM shutting down...")
    logger.info("👋 Goodbye!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
