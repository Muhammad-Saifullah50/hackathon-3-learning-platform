# Kong API Gateway JWT Configuration

**Feature**: 001-auth
**Date**: 2026-03-14
**Purpose**: Configure Kong API Gateway to validate JWT tokens issued by LearnPyByAI authentication service

---

## Overview

This document describes how to configure Kong API Gateway to validate JWT tokens issued by the LearnPyByAI authentication service. Kong will use the RSA public key from the auth service to verify token signatures without needing to call the auth service for every request.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Client    │─────▶│  Kong API    │─────▶│  Backend APIs   │
│             │      │   Gateway    │      │  (Protected)    │
└─────────────┘      └──────────────┘      └─────────────────┘
                            │
                            │ (One-time fetch)
                            ▼
                     ┌──────────────┐
                     │  Auth Service│
                     │  /public-key │
                     └──────────────┘
```

**Flow:**
1. Kong fetches the RSA public key from auth service on startup
2. Client sends JWT token in Authorization header
3. Kong validates token signature using cached public key
4. If valid, Kong forwards request to backend with user info in headers
5. If invalid, Kong returns 401 Unauthorized

---

## Public Key Endpoint

### GET /api/auth/public-key

**Description**: Returns the RSA public key used to verify JWT tokens

**Authentication**: None required (public endpoint)

**Response Format**:
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----\n",
  "algorithm": "RS256",
  "key_type": "RSA"
}
```

**Response Fields**:
- `public_key` (string): RSA public key in PEM format
- `algorithm` (string): JWT signing algorithm (always "RS256")
- `key_type` (string): Key type (always "RSA")

**Example Request**:
```bash
curl http://localhost:8000/api/auth/public-key
```

---

## Kong JWT Plugin Configuration

### Option 1: Using Kong Admin API

#### Step 1: Create a Consumer (Optional)
If you want to track which service is making requests:

```bash
curl -X POST http://localhost:8001/consumers \
  --data "username=learnpybyai-auth"
```

#### Step 2: Configure JWT Plugin on Route/Service

```bash
curl -X POST http://localhost:8001/routes/{route_id}/plugins \
  --data "name=jwt" \
  --data "config.key_claim_name=kid" \
  --data "config.secret_is_base64=false" \
  --data "config.run_on_preflight=false" \
  --data "config.claims_to_verify=exp"
```

#### Step 3: Add JWT Credential with Public Key

First, fetch the public key from auth service:

```bash
PUBLIC_KEY=$(curl -s http://localhost:8000/api/auth/public-key | jq -r '.public_key')
```

Then, add it to Kong:

```bash
curl -X POST http://localhost:8001/consumers/learnpybyai-auth/jwt \
  --data "algorithm=RS256" \
  --data "rsa_public_key=$PUBLIC_KEY" \
  --data "key=learnpybyai-auth-service"
```

### Option 2: Using Kong Declarative Configuration (kong.yml)

```yaml
_format_version: "3.0"

services:
  - name: learnpybyai-backend
    url: http://backend:8000
    routes:
      - name: protected-routes
        paths:
          - /api/
        strip_path: false
        plugins:
          - name: jwt
            config:
              key_claim_name: kid
              secret_is_base64: false
              run_on_preflight: false
              claims_to_verify:
                - exp
              header_names:
                - Authorization
              uri_param_names: []
              cookie_names: []

consumers:
  - username: learnpybyai-auth
    jwt_secrets:
      - algorithm: RS256
        key: learnpybyai-auth-service
        rsa_public_key: |
          -----BEGIN PUBLIC KEY-----
          MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
          -----END PUBLIC KEY-----
```

**Note**: Replace the `rsa_public_key` value with the actual public key from `/api/auth/public-key` endpoint.

---

## JWT Token Format

### Access Token Claims

LearnPyByAI issues JWT access tokens with the following claims:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "role": "student",
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "exp": 1710417159,
  "iat": 1710416259,
  "iss": "learnpybyai-auth"
}
```

**Standard Claims**:
- `sub` (subject): User ID (UUID)
- `exp` (expiration): Token expiration timestamp (15 minutes from issue)
- `iat` (issued at): Token issue timestamp
- `iss` (issuer): Always "learnpybyai-auth"

**Custom Claims**:
- `email` (string): User email address
- `role` (string): User role (student, teacher, admin)
- `session_id` (string): Session ID for logout tracking

### Token Validation

Kong will automatically validate:
- ✅ Token signature using RSA public key
- ✅ Token expiration (`exp` claim)
- ✅ Token format and structure

Kong will NOT validate:
- ❌ Session revocation (requires database check)
- ❌ Email verification status
- ❌ User account status

**Important**: For session revocation checks, backend services must call the auth service or check the database directly.

---

## Request Flow with Kong

### 1. Client Request with JWT

```http
GET /api/learning/modules HTTP/1.1
Host: api.learnpybyai.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. Kong Validates Token

Kong performs the following checks:
1. Extract token from Authorization header
2. Decode JWT header and payload
3. Verify signature using cached RSA public key
4. Check token expiration (`exp` claim)
5. If valid, forward request to backend

### 3. Kong Forwards Request with User Context

Kong adds the following headers to the backend request:

```http
GET /api/learning/modules HTTP/1.1
Host: backend:8000
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
X-Consumer-Username: learnpybyai-auth
X-Credential-Identifier: learnpybyai-auth-service
X-Anonymous-Consumer: false
```

**Optional**: Configure Kong to add custom headers with JWT claims:

```bash
curl -X POST http://localhost:8001/routes/{route_id}/plugins \
  --data "name=request-transformer" \
  --data "config.add.headers=X-User-Id:$(jwt.claims.sub)" \
  --data "config.add.headers=X-User-Email:$(jwt.claims.email)" \
  --data "config.add.headers=X-User-Role:$(jwt.claims.role)"
```

### 4. Backend Receives Request

Backend can extract user info from:
- JWT token (decode and verify, or trust Kong's validation)
- Custom headers added by Kong (if configured)

---

## Error Responses

### 401 Unauthorized - Missing Token

```json
{
  "message": "Unauthorized"
}
```

**Cause**: No Authorization header provided

### 401 Unauthorized - Invalid Token

```json
{
  "message": "Bad token; invalid JSON"
}
```

**Cause**: Malformed JWT token

### 401 Unauthorized - Invalid Signature

```json
{
  "message": "Invalid signature"
}
```

**Cause**: Token signature doesn't match public key (token was not issued by auth service or was tampered with)

### 401 Unauthorized - Expired Token

```json
{
  "message": "Token expired"
}
```

**Cause**: Token `exp` claim is in the past (access tokens expire after 15 minutes)

**Solution**: Client should refresh token using `/api/auth/refresh` endpoint

---

## Public Key Rotation Strategy

### Current Implementation (MVP)

- Single RSA key pair generated at setup
- Public key served via `/api/auth/public-key` endpoint
- Kong fetches key once on startup
- No automatic rotation

### Future Enhancement: Key Rotation

For production deployments, implement key rotation:

1. **Generate New Key Pair**:
   ```bash
   openssl genrsa -out keys/private_key_v2.pem 2048
   openssl rsa -in keys/private_key_v2.pem -pubout -out keys/public_key_v2.pem
   ```

2. **Update Auth Service**:
   - Support multiple public keys with key IDs (`kid` in JWT header)
   - Include `kid` in JWT header to identify which key was used
   - Serve all active public keys via `/api/auth/public-keys` endpoint

3. **Update Kong Configuration**:
   - Configure Kong to fetch keys periodically (e.g., every 5 minutes)
   - Or use Kong's JWKS (JSON Web Key Set) plugin for automatic key discovery

4. **Rotation Process**:
   - Add new key to auth service (both keys active)
   - Start issuing tokens with new key
   - Wait for old tokens to expire (15 minutes for access tokens)
   - Remove old key from auth service

**Recommended Rotation Schedule**: Every 90 days

---

## Testing Kong Configuration

### 1. Test Public Key Endpoint

```bash
curl http://localhost:8000/api/auth/public-key | jq
```

**Expected Output**:
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n",
  "algorithm": "RS256",
  "key_type": "RSA"
}
```

### 2. Get Valid JWT Token

```bash
# Login to get access token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"Student@1234"}' \
  | jq -r '.tokens.access_token')

echo "Access Token: $TOKEN"
```

### 3. Test Kong JWT Validation

```bash
# Request through Kong (should succeed)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/auth/me

# Request with invalid token (should fail with 401)
curl -H "Authorization: Bearer invalid.token.here" \
  http://localhost:8000/api/auth/me
```

### 4. Test Token Expiration

```bash
# Wait 16 minutes (access token expires after 15 minutes)
sleep 960

# Request with expired token (should fail with 401)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/auth/me
```

---

## Coordination with F03 Team

### Information to Share

1. **Public Key Endpoint**: `http://auth-service:8000/api/auth/public-key`
2. **JWT Algorithm**: RS256 (RSA with SHA-256)
3. **Token Location**: Authorization header with "Bearer" scheme
4. **Token Expiration**: 15 minutes for access tokens
5. **JWT Claims**: See "JWT Token Format" section above

### Integration Checklist

- [ ] F03 team has access to auth service public key endpoint
- [ ] Kong JWT plugin configured with correct public key
- [ ] Kong routes configured to protect backend APIs
- [ ] Token validation tested with valid and invalid tokens
- [ ] Error responses documented and handled by frontend
- [ ] Monitoring configured for JWT validation failures
- [ ] Key rotation strategy documented and agreed upon

### Contact Points

- **Auth Service Owner**: 001-auth team
- **Kong Configuration**: F03 team (API Gateway)
- **Public Key Endpoint**: `GET /api/auth/public-key` (no authentication required)

---

## Security Considerations

### ✅ Best Practices Implemented

1. **Asymmetric Encryption**: Using RS256 (RSA) instead of HS256 (HMAC) prevents key leakage
2. **Short-lived Tokens**: Access tokens expire after 15 minutes
3. **Public Key Distribution**: Public key served via dedicated endpoint
4. **Token Rotation**: Refresh tokens enable seamless token renewal

### ⚠️ Important Notes

1. **Session Revocation**: Kong cannot check if a session has been revoked (requires database check)
   - Backend services MUST validate session status for sensitive operations
   - Consider implementing a session revocation cache (Redis) for performance

2. **Public Key Security**: The public key endpoint is intentionally public
   - Public keys are safe to expose (they only verify signatures, not create them)
   - Private key MUST remain secure and never be exposed

3. **Token Replay**: JWT tokens can be replayed until they expire
   - Use HTTPS to prevent token interception
   - Consider implementing nonce or jti (JWT ID) for critical operations

4. **Rate Limiting**: Implement rate limiting on Kong to prevent abuse
   - Limit requests per IP address
   - Limit requests per user (based on JWT claims)

---

## Troubleshooting

### Issue: Kong returns "Invalid signature"

**Possible Causes**:
1. Kong is using wrong public key
2. Auth service rotated keys but Kong wasn't updated
3. Token was issued by different service

**Solution**:
```bash
# Fetch latest public key
curl http://localhost:8000/api/auth/public-key

# Update Kong JWT credential
curl -X PATCH http://localhost:8001/consumers/learnpybyai-auth/jwt/{jwt_id} \
  --data "rsa_public_key=$NEW_PUBLIC_KEY"
```

### Issue: Kong returns "Token expired"

**Cause**: Access token has expired (15 minutes)

**Solution**: Client should refresh token:
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

### Issue: Kong allows revoked session

**Cause**: Kong only validates token signature and expiration, not session status

**Solution**: Backend services must check session revocation:
```python
# In backend service
session = db.query(Session).filter(Session.id == session_id).first()
if session.revoked_at is not None:
    raise HTTPException(status_code=401, detail="Session has been revoked")
```

---

## References

- [Kong JWT Plugin Documentation](https://docs.konghq.com/hub/kong-inc/jwt/)
- [JWT.io - JWT Debugger](https://jwt.io/)
- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [LearnPyByAI Auth Service API Documentation](../spec.md)

---

**Last Updated**: 2026-03-14
**Version**: 1.0
**Status**: Ready for F03 Integration
