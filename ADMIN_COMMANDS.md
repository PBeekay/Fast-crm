# FastCRM OAuth2 API Documentation

## OAuth2 Client Credentials Flow

FastCRM now uses OAuth2 Client Credentials for API authentication. **No pre-created accounts** - everyone must register and get their own client credentials.

### 1. User Registration (Gets OAuth2 Credentials)
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
  "oauth2_client": {
    "client_id": "fcrm_abc123def456",
    "client_secret": "your-secret-here",
    "message": "Save these credentials securely! You'll need them to access the API."
  }
}
```

### 2. Get Access Token (Using Client Credentials)
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

### 3. Use Access Token for API Calls
```bash
GET /api/customers
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Available Admin Commands

### 1. Create Admin User (Command Line)
```bash
python create_admin.py
```
This script will:
- Create a new admin user
- Set admin role
- Generate OAuth2 client credentials
- Show client_id and client_secret

### 2. API Endpoints for Admin Management

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

### 3. How to Give Admin Privileges

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

### 4. Access API Documentation
Visit: `http://localhost:8000/docs`

### 5. User Roles Available
- `basic_user` - Basic user (can only see own data)
- `premium_user` - Premium user (can add customers)
- `admin` - Admin (can manage all users and data)

### 6. Example: Promote User to Admin
```bash
curl -X POST "http://localhost:8000/api/admin/users/123/promote" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{"target_role": "admin"}'
```

### 7. Security Notes
- Only existing admins can promote users to admin
- Admins cannot delete or deactivate themselves
- All admin operations are logged
- Rate limiting is applied to prevent abuse
