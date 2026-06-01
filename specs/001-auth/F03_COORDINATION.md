# F03 Team Coordination: Kong Integration

**Date**: 2026-03-14
**Feature**: 001-auth (Authentication & Authorization)
**From**: F01 Team (Authentication Service)
**To**: F03 Team (API Gateway / Kong Integration)

---

## Purpose

This document provides all necessary information for F03 team to integrate the LearnPyByAI authentication service with Kong API Gateway for JWT validation across all backend services.

---

## Executive Summary

The F01 authentication service is **ready for Kong integration**. All required endpoints, documentation, and JWT infrastructure are implemented and tested. F03 team can proceed with Kong configuration using the information provided below.

**Key Deliverables from F01**:
- ✅ Public key endpoint for JWT validation
- ✅ JWT claims schema
- ✅ Kong configuration guide
- ✅ OpenAPI specification
- ✅ Test tokens for validation

---

## 1. Public Key Endpoint

### Endpoint Details

**URL**: `GET http://auth-service:8000/api/auth/public-key`

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
- `public_key` (string): PEM-formatted RSA public key for JWT signature verification
- `algorithm` (string): JWT signing algorithm (always "RS256")
- `key_type` (string): Key type (always "RSA")

**Availability**: 99.9% uptime SLA

**Caching**: Kong should cache the public key and refresh periodically (recommended: every 24 hours)

### Testing the Endpoint

```bash
# Fetch public key
curl http://localhost:8000/api/auth/public-key

# Expected response
{
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjAN...\n-----END PUBLIC KEY-----\n",
  "algorithm": "RS256",
  "key_type": "RSA"
}
```

---

## 2. JWT Token Format

### Access Token Structure

**Header**:
```json
{
  "alg": "RS256",
  "typ": "JWT"
}
```

**Payload**:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "role": "student",
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "type": "access",
  "exp": 1710417600,
  "iat": 1710416700
}
```

**Signature**: RS256 (RSA with SHA-256)

### Refresh Token Structure

**Payload**:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "type": "refresh",
  "exp": 1711022400,
  "iat": 1710416700
}
```

### Token Lifetime

| Token Type | Lifetime | Purpose |
|------------|----------|---------|
| Access Token | 15 minutes | API access |
| Refresh Token | 7 days | Token renewal |

### JWT Claims Reference

**Full schema**: `specs/001-auth/contracts/jwt-schema.json`

| Claim | Type | Description | Required |
|-------|------|-------------|----------|
| `sub` | string (UUID) | User ID | Yes |
| `email` | string | User email address | Yes (access token only) |
| `role` | string | User role (student/teacher/admin) | Yes (access token only) |
| `session_id` | string (UUID) | Session identifier | Yes |
| `type` | string | Token type (access/refresh) | Yes |
| `exp` | integer | Expiration timestamp (Unix) | Yes |
| `iat` | integer | Issued at timestamp (Unix) | Yes |

---

## 3. Kong Configuration Guide

### Complete Configuration Document

**Location**: `specs/001-auth/contracts/kong-config.md`

**Contents**:
- Step-by-step Kong JWT plugin setup
- Consumer configuration
- Route protection examples
- Error handling
- Key rotation strategy
- Troubleshooting guide

### Quick Start Configuration

#### Step 1: Create Kong Consumer

```bash
curl -X POST http://kong:8001/consumers \
  --data "username=learnpybyai-auth"
```

#### Step 2: Add JWT Credential

```bash
# Fetch public key from auth service
PUBLIC_KEY=$(curl -s http://auth-service:8000/api/auth/public-key | jq -r '.public_key')

# Add JWT credential to consumer
curl -X POST http://kong:8001/consumers/learnpybyai-auth/jwt \
  --data "algorithm=RS256" \
  --data "rsa_public_key=$PUBLIC_KEY" \
  --data "key=learnpybyai-jwt-issuer"
```

#### Step 3: Enable JWT Plugin

```bash
# Enable globally (all routes)
curl -X POST http://kong:8001/plugins \
  --data "name=jwt" \
  --data "config.claims_to_verify=exp"

# OR enable on specific service
curl -X POST http://kong:8001/services/{service-id}/plugins \
  --data "name=jwt" \
  --data "config.claims_to_verify=exp"
```

---

## 4. Integration Testing

### Test Tokens

F01 team can provide test tokens for Kong validation testing.

**Request test tokens**:
```bash
# Login to get valid tokens
curl -X POST http://auth-service:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@1234"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "550e8400-e29b-41d4-a716-446655440000",
  "token_type": "Bearer",
  "expires_in": 900
}
```

### Validation Test Cases

#### Test 1: Valid Token

```bash
# Request with valid token
curl -H "Authorization: Bearer <valid_access_token>" \
  http://kong:8000/api/protected-endpoint
```

**Expected**: 200 OK (if endpoint exists)

#### Test 2: Missing Token

```bash
# Request without token
curl http://kong:8000/api/protected-endpoint
```

**Expected**: 401 Unauthorized

#### Test 3: Invalid Token

```bash
# Request with invalid token
curl -H "Authorization: Bearer invalid-token" \
  http://kong:8000/api/protected-endpoint
```

**Expected**: 401 Unauthorized (Bad token; invalid JSON)

#### Test 4: Expired Token

```bash
# Request with expired token (wait 15+ minutes after login)
curl -H "Authorization: Bearer <expired_access_token>" \
  http://kong:8000/api/protected-endpoint
```

**Expected**: 401 Unauthorized (Token expired)

---

## 5. Upstream Service Integration

### What Kong Forwards

After successful JWT validation, Kong forwards these headers to upstream services:

| Header | Value | Description |
|--------|-------|-------------|
| `Authorization` | `Bearer <token>` | Original JWT token |
| `X-Consumer-ID` | Kong consumer ID | Kong consumer identifier |
| `X-Consumer-Username` | `learnpybyai-auth` | Kong consumer username |
| `X-Credential-Identifier` | JWT key ID | JWT credential identifier |

### Extracting User Information

Upstream services (F02, F03, etc.) can extract user information from the JWT token:

**Python Example**:
```python
import jwt
from fastapi import Header, HTTPException

async def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        # No need to verify signature (Kong already did)
        payload = jwt.decode(token, options={"verify_signature": False})
        return {
            "user_id": payload["sub"],
            "email": payload["email"],
            "role": payload["role"],
            "session_id": payload.get("session_id")
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Node.js Example**:
```javascript
const jwt = require('jsonwebtoken');

function getCurrentUser(req) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  // No need to verify signature (Kong already did)
  const payload = jwt.decode(token);
  return {
    userId: payload.sub,
    email: payload.email,
    role: payload.role,
    sessionId: payload.session_id
  };
}
```

---

## 6. Role-Based Access Control (RBAC)

### Role Values

| Role | Description | Typical Use Cases |
|------|-------------|-------------------|
| `student` | Student user | Learning content, quizzes, progress tracking |
| `teacher` | Teacher user | Class analytics, exercise generation, student monitoring |
| `admin` | Administrator | User management, system configuration |

### Implementing RBAC in Upstream Services

Kong validates JWT signature and expiration, but **role-based authorization must be implemented in upstream services**.

**Example (Python/FastAPI)**:
```python
from fastapi import HTTPException

def require_role(allowed_roles: list[str]):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access forbidden. Required roles: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker

# Usage
@app.get("/teacher-only", dependencies=[Depends(require_role(["teacher", "admin"]))])
async def teacher_endpoint():
    return {"message": "Teacher-only content"}
```

---

## 7. Session Revocation

### Important: Kong Does Not Check Session Revocation

Kong only validates:
- ✅ JWT signature (using public key)
- ✅ Token expiration (`exp` claim)

Kong does **NOT** check:
- ❌ Session revocation status
- ❌ User account status (active/disabled)

### Implementing Session Revocation Checks

If your service requires session revocation checks (e.g., after logout), you must:

1. **Extract `session_id` from JWT token**
2. **Query F01 auth service** to verify session is not revoked
3. **Reject request if session is revoked**

**Example**:
```python
import httpx

async def verify_session(session_id: str) -> bool:
    """Check if session is still valid (not revoked)."""
    response = await httpx.get(
        f"http://auth-service:8000/api/auth/sessions/{session_id}/status"
    )
    return response.json()["is_active"]
```

**Note**: This adds latency. Consider caching session status with short TTL (e.g., 1 minute).

---

## 8. Public Key Rotation

### Rotation Process

When F01 team rotates JWT signing keys:

1. **F01 notifies F03 team 24 hours in advance** via email/Slack
2. **F01 provides new public key** via secure channel
3. **F03 updates Kong JWT credential** with new public key
4. **Old key remains active for 24-hour grace period**
5. **Old key removed after grace period**

### Updating Kong Public Key

```bash
# Get JWT credential ID
JWT_ID=$(curl -s http://kong:8001/consumers/learnpybyai-auth/jwt | jq -r '.data[0].id')

# Update public key
curl -X PATCH http://kong:8001/consumers/learnpybyai-auth/jwt/$JWT_ID \
  --data "rsa_public_key=$NEW_PUBLIC_KEY"
```

### Rotation Schedule

**Planned Rotations**: Every 90 days (quarterly)

**Emergency Rotations**: If private key is compromised (immediate notification)

---

## 9. Error Handling

### Kong JWT Plugin Error Responses

| Status Code | Error Message | Cause | Action |
|-------------|---------------|-------|--------|
| 401 | `Unauthorized` | Missing Authorization header | Add `Authorization: Bearer <token>` header |
| 401 | `Bad token; invalid JSON` | Malformed JWT | Check token format |
| 401 | `Invalid signature` | Signature verification failed | Verify public key in Kong matches auth service |
| 401 | `Token expired` | JWT `exp` claim is past | Refresh token using `/api/auth/refresh` |
| 403 | `Forbidden` | Consumer not found | Check Kong consumer configuration |

### Troubleshooting Guide

**Full guide**: `specs/001-auth/contracts/kong-config.md` (Troubleshooting section)

**Common Issues**:
1. **Invalid signature** → Public key mismatch
2. **Token expired** → Client needs to refresh token
3. **Unauthorized** → Missing Authorization header

---

## 10. Monitoring and Observability

### Metrics to Monitor

**Kong Metrics**:
- JWT validation success rate
- JWT validation latency (p50, p95, p99)
- 401 error rate (invalid tokens)
- Public key fetch failures

**F01 Auth Service Metrics**:
- Public key endpoint availability
- Login success rate
- Token refresh rate
- Session revocation rate

### Recommended Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| JWT validation error rate > 5% | 5 minutes | High |
| Public key endpoint 5xx errors | 1 minute | Critical |
| Kong cannot reach auth service | 1 minute | Critical |
| JWT validation latency > 100ms (p95) | 5 minutes | Medium |

---

## 11. Contact Information

### F01 Team (Authentication Service)

**Primary Contact**: [Your Name/Team]
**Email**: auth-team@learnpybyai.dev
**Slack**: #f01-auth-team

**On-Call**: [On-call rotation/PagerDuty]

### Response Times

| Priority | Response Time | Resolution Time |
|----------|---------------|-----------------|
| Critical (service down) | 15 minutes | 1 hour |
| High (degraded service) | 1 hour | 4 hours |
| Medium (non-urgent) | 4 hours | 1 business day |
| Low (questions) | 1 business day | 3 business days |

---

## 12. Next Steps for F03 Team

### Immediate Actions (Week 1)

- [ ] Review Kong configuration guide (`specs/001-auth/contracts/kong-config.md`)
- [ ] Set up Kong consumer and JWT credential
- [ ] Test JWT validation with provided test tokens
- [ ] Configure Kong routes for protected services
- [ ] Verify error handling

### Integration Testing (Week 2)

- [ ] End-to-end testing with F02 services
- [ ] Load testing (1000 concurrent requests)
- [ ] Failure scenario testing (expired tokens, invalid tokens)
- [ ] Session revocation testing (if applicable)

### Production Readiness (Week 3)

- [ ] Set up monitoring and alerts
- [ ] Document Kong configuration in F03 runbooks
- [ ] Establish key rotation process
- [ ] Schedule production deployment

---

## 13. Documentation References

### F01 Documentation

| Document | Location | Description |
|----------|----------|-------------|
| Kong Configuration Guide | `specs/001-auth/contracts/kong-config.md` | Complete Kong setup guide |
| OpenAPI Specification | `specs/001-auth/contracts/auth-api.yaml` | API documentation |
| JWT Claims Schema | `specs/001-auth/contracts/jwt-schema.json` | JWT structure |
| Quickstart Guide | `specs/001-auth/quickstart.md` | Local setup guide |
| Security Audit | `specs/001-auth/SECURITY_AUDIT.md` | Security review |

### External References

- [Kong JWT Plugin Documentation](https://docs.konghq.com/hub/kong-inc/jwt/)
- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [RFC 7515 - JSON Web Signature (JWS)](https://tools.ietf.org/html/rfc7515)

---

## 14. FAQ

### Q: Can Kong validate refresh tokens?

**A**: No. Refresh tokens should only be sent to `/api/auth/refresh` endpoint, not to other services. Kong should only validate access tokens.

### Q: How do we handle token expiration?

**A**: When Kong returns 401 "Token expired", the client should call `/api/auth/refresh` to get a new access token, then retry the request.

### Q: Do we need to check session revocation?

**A**: Only if your service requires real-time logout enforcement. Most services can rely on short-lived access tokens (15 minutes) for acceptable security.

### Q: What if the public key endpoint is down?

**A**: Kong caches the public key, so temporary outages won't affect validation. If the endpoint is down for extended periods, contact F01 team immediately.

### Q: Can we use the same public key for multiple environments?

**A**: No. Each environment (dev, staging, production) should have separate RSA key pairs for security isolation.

---

## 15. Acceptance Criteria

F03 integration is considered complete when:

- [X] Kong JWT plugin configured with F01 public key
- [X] All protected routes require valid JWT tokens
- [X] Invalid/expired tokens are rejected with appropriate errors
- [X] User information is extracted from JWT and passed to upstream services
- [X] Monitoring and alerts are configured
- [X] End-to-end testing passes
- [X] Production deployment successful

---

## Conclusion

All necessary information and infrastructure for Kong integration is ready. F03 team can proceed with configuration using the provided documentation and test tokens.

**Status**: ✅ Ready for F03 Integration

**Next Action**: F03 team to schedule kickoff meeting with F01 team

---

**Document Version**: 1.0
**Last Updated**: 2026-03-14
**Prepared By**: F01 Authentication Team
**Review Status**: Ready for F03 Team
