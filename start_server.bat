@echo off
echo Starting FastCRM Server...

REM Set environment variables
set CRM_SECRET_KEY=AGpjLBwns8polnJCg8kr2eig4ZKguWCo_zSGVvsOhnY
set DATABASE_URL=sqlite:///./crm.db
set ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000
set ENVIRONMENT=development

echo Environment variables set:
echo CRM_SECRET_KEY: SET
echo DATABASE_URL: %DATABASE_URL%
echo ALLOWED_ORIGINS: %ALLOWED_ORIGINS%
echo ENVIRONMENT: %ENVIRONMENT%

echo.
echo Starting FastCRM server...
echo Server will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
