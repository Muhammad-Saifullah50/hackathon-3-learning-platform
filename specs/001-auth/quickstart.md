# Quickstart: Authentication & Authorization

**Feature**: 001-auth | **Date**: 2026-03-14 | **Phase**: 1 (Design)

This guide walks you through setting up the authentication system locally for development and testing.

---

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ and npm/yarn installed
- PostgreSQL 14+ running locally or via Docker
- Git installed

---

## Backend Setup (FastAPI)

### 1. Clone and Navigate

```bash
cd backend/
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies**:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `alembic` - Database migrations
- `pyjwt[crypto]` - JWT with RS256 support
- `bcrypt` - Password hashing
- `httpx` - Async HTTP client (HaveIBeenPwned)
- `python-dotenv` - Environment variables
- `slowapi` - Rate limiting

### 4. Configure Environment Variables

Create `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/learnpybyai_dev

# JWT Configuration (RS256)
JWT_PRIVATE_KEY_PATH=./keys/jwt_private.pem
JWT_PUBLIC_KEY_PATH=./keys/jwt_public.pem
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration (Local Development - Mailhog)
EMAIL_BACKEND=smtp
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@learnpybyai.dev

# Email Configuration (Production - SendGrid)
# EMAIL_BACKEND=sendgrid
# SENDGRID_API_KEY=your_sendgrid_api_key
# EMAIL_FROM=noreply@learnpybyai.dev

# HaveIBeenPwned API
HIBP_API_URL=https://api.pwnedpasswords.com/range

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_ATTEMPTS=5
RATE_LIMIT_LOCKOUT_MINUTES=15

# CORS (for local frontend)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Environment
ENVIRONMENT=development
```

### 5. Generate RSA Key Pair for JWT

```bash
mkdir -p backend/keys
cd backend/keys

# Generate private key
openssl genrsa -out jwt_private.pem 2048

# Extract public key
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem

# Set permissions (Unix/Linux/Mac)
chmod 600 jwt_private.pem
chmod 644 jwt_public.pem

cd ../..
```

**Important**: Add `backend/keys/` to `.gitignore` to prevent committing private keys.

### 6. Setup Database

```bash
# Create database
createdb learnpybyai_dev

# Or using psql
psql -U postgres -c "CREATE DATABASE learnpybyai_dev;"
```

### 7. Run Migrations

```bash
cd backend/
alembic upgrade head
```

This creates the following tables:
- `users`
- `sessions`
- `password_reset_tokens`
- `email_verification_tokens`
- `rate_limit_counters`

### 8. Start Local Email Server (Mailhog)

For local development, use Mailhog to capture emails:

```bash
# Using Docker
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Or install via Homebrew (Mac)
brew install mailhog
mailhog
```

Access Mailhog UI at: http://localhost:8025

### 9. Start FastAPI Server

```bash
cd backend/
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API available at: http://localhost:8000
API docs (Swagger): http://localhost:8000/docs

---

## Frontend Setup (Next.js + Better Auth)

### 1. Navigate to Frontend

```bash
cd frontend/
```

### 2. Install Dependencies

```bash
npm install
# or
yarn install
```

**Key dependencies**:
- `next` - React framework
- `better-auth` - Authentication library
- `react` - UI library
- `typescript` - Type safety
- `tailwindcss` - Styling

### 3. Configure Environment Variables

Create `frontend/.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Better Auth Configuration
BETTER_AUTH_SECRET=your-secret-key-min-32-chars-long-change-in-production
BETTER_AUTH_URL=http://localhost:3000

# Environment
NODE_ENV=development
```

### 4. Start Next.js Development Server

```bash
npm run dev
# or
yarn dev
```

Frontend available at: http://localhost:3000

---

## Testing the Setup

### 1. Register a New User

**Using curl**:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePass123!",
    "display_name": "Test Student",
    "role": "student"
  }'
```

**Expected response**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "student@example.com",
  "role": "student",
  "email_verification_required": false,
  "message": "Registration successful. Please check your email to verify your account."
}
```

Check Mailhog (http://localhost:8025) for verification email.

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "550e8400-e29b-41d4-a716-446655440000",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@example.com",
    "role": "student",
    "display_name": "Test Student",
    "email_verified_at": null
  }
}
```

### 3. Access Protected Endpoint

```bash
# Replace <ACCESS_TOKEN> with token from login response
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Expected response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "student@example.com",
  "role": "student",
  "display_name": "Test Student",
  "email_verified_at": null
}
```

### 4. Test Rate Limiting

Try logging in with wrong password 6 times:

```bash
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{
      "email": "student@example.com",
      "password": "WrongPassword123!"
    }'
  echo "\nAttempt $i"
done
```

After 5 failures, you should see:
```json
{
  "error": "Too many failed attempts. Try again in 15 minutes"
}
```

### 5. Test Token Refresh

```bash
# Replace <REFRESH_TOKEN> with token from login response
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<REFRESH_TOKEN>"
  }'
```

**Expected response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "660e8400-e29b-41d4-a716-446655440001",
  "token_type": "Bearer",
  "expires_in": 900
}
```

Note: Old refresh token is now invalid (rotated).

---

## Running Tests

### Backend Tests

```bash
cd backend/

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/integration/test_auth_routes.py

# Run specific test
pytest tests/integration/test_auth_routes.py::test_register_user_success
```

### Frontend Tests

```bash
cd frontend/

# Run unit/component tests
npm test
# or
yarn test

# Run E2E tests (requires backend running)
npm run test:e2e
# or
yarn test:e2e
```

---

## Database Management

### View Database Tables

```bash
psql -U postgres -d learnpybyai_dev

# List tables
\dt

# View users
SELECT id, email, role, email_verified_at FROM users;

# View sessions
SELECT id, user_id, created_at, expires_at, revoked_at FROM sessions;

# Exit
\q
```

### Reset Database

```bash
# Drop and recreate database
dropdb learnpybyai_dev
createdb learnpybyai_dev

# Run migrations
cd backend/
alembic upgrade head
```

### Create New Migration

```bash
cd backend/
alembic revision --autogenerate -m "Add new column to users table"
alembic upgrade head
```

---

## Troubleshooting

### Issue: "Connection refused" when accessing backend

**Solution**: Ensure FastAPI server is running on port 8000:
```bash
cd backend/
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Issue: "Database does not exist"

**Solution**: Create the database:
```bash
createdb learnpybyai_dev
cd backend/
alembic upgrade head
```

### Issue: "Invalid JWT signature"

**Solution**: Ensure RSA keys are generated and paths in `.env` are correct:
```bash
cd backend/keys/
ls -la  # Should see jwt_private.pem and jwt_public.pem
```

### Issue: "HaveIBeenPwned API timeout"

**Solution**: Check internet connection or temporarily disable breach checking in code (for local dev only).

### Issue: "Email not sending"

**Solution**: Ensure Mailhog is running:
```bash
docker ps  # Should see mailhog container
# Or restart Mailhog
docker restart <mailhog_container_id>
```

### Issue: "CORS error in browser"

**Solution**: Ensure `CORS_ORIGINS` in backend `.env` includes frontend URL:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## Next Steps

1. **Run `/sp.tasks`** to generate implementation tasks
2. **Implement backend auth module** (models, repositories, services, routes)
3. **Implement frontend auth components** (login, register, password reset forms)
4. **Write tests** (TDD approach for auth flows)
5. **Integrate with Kong gateway** (F03 dependency)
6. **Deploy to staging** for integration testing

---

## Useful Commands Reference

```bash
# Backend
cd backend/
source venv/bin/activate
uvicorn src.main:app --reload
pytest --cov=src
alembic upgrade head

# Frontend
cd frontend/
npm run dev
npm test
npm run test:e2e

# Database
psql -U postgres -d learnpybyai_dev
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic downgrade -1

# Docker (Mailhog)
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
docker ps
docker logs <container_id>
```

---

## Security Checklist for Production

Before deploying to production, ensure:

- [ ] RSA private key is stored securely (not in version control)
- [ ] `.env` files are in `.gitignore`
- [ ] `BETTER_AUTH_SECRET` is strong (32+ characters)
- [ ] Database credentials are rotated and stored in secret manager
- [ ] SendGrid API key is configured (not SMTP)
- [ ] CORS origins are restricted to production domains only
- [ ] Rate limiting is enabled
- [ ] HTTPS is enforced (no HTTP)
- [ ] Database backups are configured
- [ ] Logging is configured (no sensitive data in logs)
- [ ] Error messages don't leak sensitive information
- [ ] Session cleanup job is scheduled (daily)

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Better Auth Documentation](https://better-auth.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [JWT.io](https://jwt.io/) - JWT debugger
- [HaveIBeenPwned API](https://haveibeenpwned.com/API/v3)
- [OpenAPI Specification](https://swagger.io/specification/)
