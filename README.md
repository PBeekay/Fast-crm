# FastCRM

A modern and fast FastAPI-based CRM MVP application. Complete CRM solution with user management, customer tracking, and note system.

## ✨ Features

### 🔐 Authentication
- JWT-based secure user registration and login
- Password hashing (bcrypt)
- Token-based API access

### 👥 Customer Management
- Create, list, view, and delete customers
- Customer information (name, email, phone, company)
- User-based customer isolation

### 📝 Note System
- Add and list notes for customers
- Delete note operations
- Timestamped note tracking

### 🎨 Modern Frontend
- Responsive and modern user interface
- Single Page Application (SPA)
- Real-time data updates

### 📊 Logging and Monitoring
- Detailed HTTP request/response logs
- Processing times and performance metrics
- Error tracking and security logs

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
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

When the application is running:
- **Frontend**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Register**: http://localhost:8000/register

## 📚 API Documentation

### Authentication
- `POST /api/register` - User registration
- `POST /api/token` - Login (get JWT token)
- `GET /api/me` - Current user information
- `POST /api/logout` - User logout

### Customer Operations
- `POST /api/customers` - Create new customer
- `GET /api/customers` - List customers
- `GET /api/customers/{id}` - Get specific customer
- `DELETE /api/customers/{id}` - Delete customer

### Note Operations
- `POST /api/customers/{id}/notes` - Add note to customer
- `GET /api/customers/{id}/notes` - List customer notes
- `DELETE /api/customers/{id}/notes/{note_id}` - Delete note

## 🏗️ Project Structure

```
fastcrm/
├── main.py              # Main FastAPI application
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic schemas
├── database.py          # Database connection
├── auth.py              # Authentication functions
├── requirements.txt     # Python dependencies
├── env.example          # Environment variables example
├── .gitignore           # Git ignore rules
├── README.md            # This file
└── static/              # Frontend files
    ├── index.html       # Main page
    ├── register.html    # Registration page
    ├── app.js           # Main JavaScript
    ├── register.js      # Registration JavaScript
    └── style.css        # CSS styles
```

## 🔧 Development

### Database
- Default: SQLite (`crm.db`)
- For PostgreSQL, MySQL etc., change `DATABASE_URL`
- Automatic table creation

### Logging
- All HTTP requests are logged
- Processing times and status codes
- Emoji-based visual logs

### Security
- JWT token-based authentication
- Password hashing (bcrypt)
- User-based data isolation

## 🚀 Deployment

### Production Settings
1. Change `CRM_SECRET_KEY` to a strong value
2. Set `DATABASE_URL` to production database
3. Use HTTPS
4. Manage configuration with environment variables

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Contact

For questions, please open an issue or contact us.