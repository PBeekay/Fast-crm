# 🚀 FastCRM - Modern Customer Relationship Management

A modern, FastAPI-based CRM application with advanced authentication, role-based access control, and a beautiful responsive UI.

## ⚠️ Security Notice

**IMPORTANT**: Before deploying to production or sharing on GitHub:

1. ✅ **Never commit `.env` file** - It contains sensitive credentials
2. ✅ **Change the default SECRET_KEY** - Generate a new secure key
3. ✅ **Update CORS origins** - Don't use wildcard `*` in production
4. ✅ **Use HTTPS** - Always use TLS/SSL in production
5. ✅ **Review `SECURITY.md`** - Follow all security best practices

📖 **See [SECURITY.md](SECURITY.md) for comprehensive security guidelines**

## ✨ Features

- **🔐 OAuth2 Authentication** - Secure client credentials flow
- **👥 Role-Based Access Control** - Basic, Premium, and Admin users
- **📊 Customer Management** - Add, edit, delete customers with status tracking
- **📝 Notes System** - Track customer interactions and important information
- **🌙 Dark/Light Mode** - Beautiful responsive UI with theme switching
- **📱 Mobile Responsive** - Works perfectly on all devices
- **🛡️ Security** - Rate limiting, CORS protection, and secure headers
- **📈 Dashboard** - Real-time statistics and recent activity
- **🔧 Admin Panel** - Complete user and system management

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd fastcrm
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
# Copy the example environment file
cp env.example .env

# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env and update CRM_SECRET_KEY with the generated key
```

5. **Create admin user**
```bash
python create_admin.py
```

6. **Start the server**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

7. **Access the application**
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/docs (look for "👑 Admin Management")

## 👑 Admin Commands

### Create Admin User
```bash
python create_admin.py
```
This script will:
- Create a new admin user
- Set admin role
- Generate OAuth2 client credentials
- Show client_id and client_secret

### API Endpoints for Admin Management

#### User Management
- `GET /api/admin/users` - List all users
- `GET /api/admin/users/{user_id}` - Get specific user
- `PUT /api/admin/users/{user_id}` - Update user
- `POST /api/admin/users/{user_id}/promote` - **Promote user to admin**
- `POST /api/admin/users/{user_id}/toggle-status` - Toggle user status
- `DELETE /api/admin/users/{user_id}` - Delete user

#### Customer Management
- `GET /api/admin/customers` - List all customers

#### Statistics
- `GET /api/admin/stats` - Get admin statistics

### How to Give Admin Privileges

#### Method 1: Using the API (Recommended)
```bash
# First, you need to be logged in as an admin
# Then promote a user to admin:

POST /api/admin/users/{user_id}/promote
Content-Type: application/json
Authorization: Bearer {your_admin_token}

{
  "target_role": "admin"
}
```

#### Method 2: Using the create_admin.py script
```bash
python create_admin.py
```

### Example: Promote User to Admin
```bash
curl -X POST "http://localhost:8000/api/admin/users/123/promote" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{"target_role": "admin"}'
```

## 🔐 Authentication System

### OAuth2 Client Credentials Flow

FastCRM uses OAuth2 Client Credentials for API authentication. **No pre-created accounts** - everyone must register and get their own client credentials.

#### 1. User Registration
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "basic_user",
    "is_active": "true",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Registration successful! You can now login with your credentials. Your API access credentials have been created and can be viewed in the Swagger UI documentation."
}
```

**Note**: OAuth2 credentials are automatically created but not exposed in the response for security. Access them via:
- Login to the application
- Go to `/docs` (Swagger UI)
- Use `GET /api/auth/me/oauth2-credentials` endpoint

#### 2. Get Access Token (Using Client Credentials)
```bash
POST /api/auth/oauth2/token
Content-Type: application/json

{
  "client_id": "fcrm_abc123def456",
  "client_secret": "your-secret-here"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "refresh-token-here",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 3. Use Access Token for API Calls
```bash
GET /api/customers
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 👥 User Roles

- **`basic_user`** - Basic user (can only see own data)
- **`premium_user`** - Premium user (can add customers)
- **`admin`** - Admin (can manage all users and data)

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/token` - Login (get tokens)
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user info

### Customers (Premium+ required)
- `GET /api/customers` - List customers
- `POST /api/customers` - Create customer
- `GET /api/customers/{id}` - Get customer
- `PUT /api/customers/{id}` - Update customer
- `DELETE /api/customers/{id}` - Delete customer

### Notes
- `GET /api/customers/{id}/notes` - List customer notes
- `POST /api/customers/{id}/notes` - Create note
- `PUT /api/customers/{id}/notes/{note_id}` - Update note
- `DELETE /api/customers/{id}/notes/{note_id}` - Delete note

### System
- `GET /api/system/health` - Health check
- `GET /api/system/stats` - System statistics
- `GET /api/system/debug/database` - Database debug info

## 🛠️ Development

### Project Structure
```
fastcrm/
├── main.py                 # FastAPI application
├── database.py             # Database configuration
├── models.py               # SQLAlchemy models
├── schemas.py              # Pydantic schemas
├── auth.py                 # Authentication logic
├── dependencies.py         # FastAPI dependencies
├── create_admin.py         # Admin user creation script
├── routers/                # API route modules
│   ├── auth.py            # Authentication routes
│   ├── customers.py       # Customer management
│   ├── notes.py           # Notes management
│   ├── admin.py           # Admin operations
│   └── system.py          # System endpoints
├── static/                 # Frontend files
│   ├── index.html         # Main application
│   ├── register.html      # Registration page
│   ├── app.js             # Frontend JavaScript
│   └── style.css          # Styling
└── requirements.txt       # Python dependencies
```

### Running in Development
```bash
# Start with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use the batch file (Windows)
start_server.bat
```

### Database
- **Default**: SQLite (`crm.db`)
- **Production**: Set `DATABASE_URL` environment variable
- **Migrations**: Tables are created automatically on startup

## 🔧 Configuration

### Environment Variables

**IMPORTANT**: Always use `.env` file for configuration. Never commit `.env` to version control!

```bash
# Copy the example file
cp env.example .env
```

**Required Configuration:**
```bash
# SECURITY: JWT Secret Key (REQUIRED - Generate a new one!)
CRM_SECRET_KEY=your_secure_secret_key_here_minimum_32_characters

# Database
DATABASE_URL=sqlite:///./crm.db

# CORS (Update for production!)
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Environment
ENVIRONMENT=development
```

**See `env.example` for all available configuration options.**

### Security Features

#### Built-in Security
- ✅ **JWT Authentication** - Secure token-based auth
- ✅ **OAuth2 Client Credentials** - API access control
- ✅ **Rate Limiting** - Prevents abuse (configurable)
- ✅ **CORS Protection** - Configurable origins (no wildcards)
- ✅ **Security Headers** - XSS, CSRF, clickjacking protection
- ✅ **Input Validation** - Pydantic schemas with type checking
- ✅ **Role-Based Access Control** - Granular permissions
- ✅ **Password Hashing** - bcrypt with salt
- ✅ **SQL Injection Protection** - SQLAlchemy ORM
- ✅ **Session Management** - Refresh token rotation

#### Security Best Practices

**Before Deploying to Production:**

1. **Change the Secret Key**
   ```bash
   # Generate a new secure key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Update in .env
   CRM_SECRET_KEY=<generated-key>
   ```

2. **Use Production Database**
   ```bash
   # PostgreSQL (recommended)
   DATABASE_URL=postgresql://user:password@localhost:5432/fastcrm
   ```

3. **Configure CORS Properly**
   ```bash
   # Only allow your actual domains
   ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

4. **Enable HTTPS**
   - Use reverse proxy (nginx/Apache)
   - Valid SSL/TLS certificate
   - Redirect HTTP to HTTPS

5. **Set Production Environment**
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   ```

**📖 For detailed security information, see [SECURITY.md](SECURITY.md)**

## 📱 Frontend Features

### Responsive Design
- **Mobile-first** approach
- **Touch-friendly** interface
- **Adaptive layout** for all screen sizes

### Dark/Light Mode
- **Automatic theme detection**
- **Persistent theme storage**
- **Smooth transitions**
- **Keyboard shortcut**: `Ctrl+T`

### User Experience
- **Real-time notifications**
- **Loading states**
- **Error handling**
- **Auto-refresh** after operations
- **Keyboard shortcuts**

## 🚀 Deployment

### Production Setup
1. **Set environment variables**
2. **Use production database** (PostgreSQL recommended)
3. **Configure CORS origins**
4. **Set up reverse proxy** (nginx)
5. **Enable HTTPS**

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- **Documentation**: Check `/docs` endpoint
- **Issues**: Create GitHub issues
- **Admin Commands**: See `ADMIN_COMMANDS.md`

## 🎯 Roadmap

- [ ] Email notifications
- [ ] File attachments
- [ ] Advanced reporting
- [ ] Mobile app
- [ ] Multi-tenant support
- [ ] API rate limiting dashboard
- [ ] Audit logs
- [ ] Backup/restore functionality

---

**FastCRM** - Modern, Secure, and Scalable CRM Solution 🚀