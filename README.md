# 🚀 FastCRM

A modern, secure, and scalable FastAPI-based CRM application with role-based access control, advanced authentication, and comprehensive customer management.

## ✨ Features

*** ### Before start the project remove the "crm.db" file ### ***

### 🔐 Advanced Authentication
- JWT-based secure user registration and login
- Password hashing with bcrypt
- Access token + Refresh token system
- Multi-device session management
- Automatic token refresh
- Secure logout with token invalidation

### 👥 Role-Based Access Control
- **Basic User**: View-only access to own data
- **Premium User**: Full customer and note management
- **Admin**: Complete system administration

### 🎯 Customer Management
- Create, list, update, and delete customers
- Customer search functionality
- Customer status tracking (Active, Inactive, Lead, Prospect, Converted)
- Customer information (name, email, phone, company)
- User-based customer isolation
- Premium user feature

### 📝 Note System
- Add, list, and delete customer notes
- Timestamped note tracking
- User attribution for notes
- Customer-specific note organization

### 👑 Admin Features
- User management (list, view, update, delete users)
- User role promotion/demotion
- User activation/deactivation
- View all customers across all users
- System statistics and analytics
- Active session monitoring

### 🎨 Modern Frontend
- Responsive and modern user interface
- Single Page Application (SPA)
- Real-time data updates
- Dark/Light theme support
- Cache-busting for development

### 📊 Comprehensive Logging
- Detailed HTTP request/response logs with emojis
- Processing times and performance metrics
- Security event tracking
- User action logging
- Error tracking with stack traces

## 🚀 Quick Start

### Requirements
- Python 3.10+ (3.13 recommended)
- pip

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd fastcrm

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
Create `.env` file:
```bash
cp env.example .env
```

Edit `.env` file:
```env
CRM_SECRET_KEY=your_very_secure_secret_key_here
DATABASE_URL=sqlite:///./crm.db
```

### Running the Application
```bash
# Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python main.py
```

When the application is running:
- **Frontend**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Register**: http://localhost:8000/register
- **Health Check**: http://localhost:8000/api/system/health

### Creating Admin User

After starting the application, create your first admin user:

**Option 1: Interactive Mode**
```bash
python create_admin.py
```
Follow the prompts to create an admin user with custom credentials.

**Option 2: Quick Promotion**
```bash
# First, register a user via the web interface
# Then promote them to admin:
python make_admin.py user@example.com
```

This will:
- Promote the user to admin role
- Grant access to all admin endpoints
- Enable user management capabilities

## 📚 API Documentation

FastCRM uses a modular router-based architecture. Visit `/docs` for interactive API documentation.

### 🔐 Authentication (`/api/auth`)
- `POST /api/auth/register` - User registration
- `POST /api/auth/token` - Login (get access + refresh tokens)
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Current user information
- `GET /api/auth/me/tokens` - List active sessions
- `DELETE /api/auth/me/tokens/{token_id}` - Revoke specific session
- `POST /api/auth/logout` - Logout (invalidate current session)
- `POST /api/auth/logout-all` - Logout from all devices

### 👥 Customer Operations (`/api/customers`) - Premium+ Required
- `POST /api/customers` - Create new customer
- `GET /api/customers` - List customers (with search & pagination)
- `GET /api/customers/{id}` - Get specific customer
- `PUT /api/customers/{id}` - Update customer
- `DELETE /api/customers/{id}` - Delete customer

### 📝 Note Operations (`/api/customers/{id}/notes`)
- `POST /api/customers/{customer_id}/notes` - Add note to customer
- `GET /api/customers/{customer_id}/notes` - List customer notes
- `DELETE /api/customers/{customer_id}/notes/{note_id}` - Delete note

### 👑 Admin Operations (`/api/admin`) - Admin Only
**User Management:**
- `GET /api/admin/users` - List all users
- `GET /api/admin/users/{user_id}` - Get user details
- `PUT /api/admin/users/{user_id}` - Update user
- `DELETE /api/admin/users/{user_id}` - Delete user
- `POST /api/admin/users/{user_id}/promote` - Change user role
- `POST /api/admin/users/{user_id}/toggle-status` - Activate/deactivate user

**System Management:**
- `GET /api/admin/customers` - List all customers
- `GET /api/admin/stats` - System statistics

### 🛠️ System Operations (`/api/system`)
- `GET /api/system/health` - Health check
- `GET /api/system/debug/database` - Database debug info
- `GET /api/system/stats` - Basic system statistics

## 🏗️ Project Structure

```
fastcrm/
├── main.py              # Main FastAPI application with middleware
├── models.py            # SQLAlchemy database models (User, Customer, Note, RefreshToken)
├── schemas.py           # Pydantic schemas for validation
├── database.py          # Database connection and session management
├── auth.py              # JWT authentication and password hashing
├── dependencies.py      # Shared dependencies and access control
├── create_admin.py      # Interactive admin user creation script
├── make_admin.py        # Quick admin promotion utility
├── requirements.txt     # Python dependencies
├── env.example          # Environment variables template
├── .gitignore           # Git ignore rules
├── README.md            # This documentation
├── routers/             # Modular API routers
│   ├── __init__.py      # Router exports
│   ├── auth.py          # Authentication endpoints
│   ├── customers.py     # Customer management endpoints
│   ├── notes.py         # Note management endpoints
│   ├── admin.py         # Admin-only endpoints
│   └── system.py        # System health and debugging
└── static/              # Frontend files
    ├── index.html       # Main application page
    ├── register.html    # User registration page
    ├── app.js           # Main JavaScript logic
    ├── register.js      # Registration form handler
    └── style.css        # Application styles
```

## 🔧 Development

### Database Models
- **User**: Authentication and authorization
- **Customer**: CRM customer records with status tracking
- **Note**: Customer interaction history
- **RefreshToken**: Secure session management

Default: SQLite (`crm.db`)
- For PostgreSQL/MySQL: change `DATABASE_URL` in `.env`
- Automatic table creation on startup
- SQLAlchemy ORM for database operations

### Logging System
- **Request Logging**: All HTTP requests with method, path, client IP
- **Response Logging**: Status codes, processing times, error details
- **Security Events**: Failed login attempts, unauthorized access
- **User Actions**: Customer creation, updates, deletions
- **Emoji-based Visual Logs**: Easy to scan and understand

### Security Features
- **JWT Tokens**: Access (short-lived) + Refresh (long-lived)
- **Password Security**: bcrypt hashing with salt
- **Role-Based Access Control**: Three-tier user hierarchy
- **Data Isolation**: Users can only access their own data
- **Session Management**: Multi-device support with revocation
- **Token Rotation**: Automatic refresh token rotation on use

### API Architecture
- **Modular Routers**: Organized by feature domain
- **Dependency Injection**: Clean separation of concerns
- **Pydantic Validation**: Automatic request/response validation
- **OpenAPI Docs**: Auto-generated interactive documentation
- **CORS Enabled**: Configurable cross-origin requests

## 🎯 Using the API

### Authenticating in FastAPI Docs

1. Go to http://localhost:8000/docs
2. Click the **"Authorize"** button (🔓 icon at top right)
3. Enter your credentials:
   - **Username**: your email address
   - **Password**: your password
   - Leave `client_id` and `client_secret` empty
4. Click **"Authorize"**
5. You can now test all authenticated endpoints!

### Testing with curl

```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123","full_name":"Test User"}'

# 2. Login
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=pass123&grant_type=password"

# 3. Use the access token
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🚀 Deployment

### Production Checklist
1. ✅ Generate strong `CRM_SECRET_KEY` (use: `openssl rand -hex 32`)
2. ✅ Configure production database in `DATABASE_URL`
3. ✅ Enable HTTPS with SSL/TLS certificates
4. ✅ Set proper CORS origins (remove wildcard `*`)
5. ✅ Configure environment variables securely
6. ✅ Set up application monitoring and logging
7. ✅ Regular database backups
8. ✅ Rate limiting configuration

### Docker Deployment
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t fastcrm .
docker run -p 8000:8000 -e CRM_SECRET_KEY=your-secret fastcrm
```

### Production Server (using Gunicorn)
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 🔍 Troubleshooting

### Common Issues

**"401 Unauthorized" when accessing endpoints**
- Make sure you're authenticated in the FastAPI docs
- Check if your token has expired (access tokens expire after 24 hours)
- Try logging in again to get a fresh token

**"403 Forbidden - Premium user privileges required"**
- Customer management requires Premium or Admin role
- Use `python make_admin.py your@email.com` to promote your account
- Or ask an admin to promote you via the admin panel

**"500 Internal Server Error" on customer endpoints**
- This might be caused by old database data
- Check logs for enum validation errors
- Database status values should be: ACTIVE, INACTIVE, LEAD, PROSPECT, CONVERTED

**Registration not working**
- Check that the endpoint is `/api/auth/register` (not `/api/register`)
- Verify password is at least 6 characters
- Check server logs for detailed error messages

**Can't access admin features**
- Ensure your account has admin role
- Use `python make_admin.py your@email.com` to promote
- Re-login after promotion to refresh your token

### Useful Commands

```bash
# Check if server is running
curl http://localhost:8000/api/system/health

# View all users in database
python -c "from database import SessionLocal; import models; db=SessionLocal(); print([u.email + ' - ' + u.role.value for u in db.query(models.User).all()])"

# Promote user to admin
python make_admin.py user@example.com

# Create fresh admin account
python create_admin.py

# Check application logs
# (Look in your terminal where uvicorn is running)
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 💡 Tips

- **Theme Toggle**: Use the theme button in the UI to switch between light/dark mode
- **Search Customers**: Use the search box in customer list for quick filtering
- **Multi-device Login**: You can login from multiple devices, manage sessions in `/api/auth/me/tokens`
- **Interactive API Docs**: Use `/docs` for testing all endpoints without writing code
- **Database Inspection**: SQLite database can be viewed with tools like DB Browser for SQLite

## 📞 Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the API documentation at `/docs`
- Check the troubleshooting section above

---

**Built with ❤️ using FastAPI, SQLAlchemy, and modern web technologies.**