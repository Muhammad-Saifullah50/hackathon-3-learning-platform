# Feature Specification: Authentication & Authorization

**Feature Branch**: `001-auth`
**Created**: 2026-03-14
**Status**: Draft
**Input**: User description: "F01 Authentication & Authorization - Secure authentication using Better Auth (frontend) and FastAPI JWT (backend) with role-based access control"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New User Registration (Priority: P1)

A new user (student, teacher, or admin) needs to create an account to access the LearnPyByAI platform. The system collects their email, password, and role, validates the input, and creates a verified account.

**Why this priority**: Registration is the entry point to the platform. Without it, no other features are accessible. This is the foundation of user identity.

**Independent Test**: Can be fully tested by submitting registration form with valid credentials and verifying account creation in database. Delivers a working registration flow that can be demonstrated standalone.

**Acceptance Scenarios**:

1. **Given** a user is on the registration page, **When** they submit valid email, password (8+ chars with non-alpha), and role, **Then** an account is created, verification email is sent, and user is redirected to email verification prompt
2. **Given** a user submits a password from HaveIBeenPwned breach database, **When** registration is attempted, **Then** system rejects the password with message "This password has been compromised in a data breach. Please choose a different one"
3. **Given** a user submits an already-registered email, **When** registration is attempted, **Then** system returns error "An account with this email already exists"
4. **Given** a user submits invalid email format, **When** registration is attempted, **Then** system returns error "Please enter a valid email address"

---

### User Story 2 - User Login with JWT Tokens (Priority: P1)

A registered user needs to log in to access their account. The system validates credentials, issues access and refresh tokens, and establishes a session.

**Why this priority**: Login is required for all authenticated features. This story delivers the core authentication mechanism that all other features depend on.

**Independent Test**: Can be fully tested by logging in with valid credentials and verifying JWT tokens are issued and accepted by protected endpoints. Delivers working authentication that can be demonstrated standalone.

**Acceptance Scenarios**:

1. **Given** a user with verified email enters correct credentials, **When** they submit login form, **Then** system issues 15-minute access token and 7-day refresh token, stores session in database, and redirects to dashboard
2. **Given** a user with unverified email (teacher/admin) attempts login, **When** they submit credentials, **Then** system blocks login and displays "Please verify your email before logging in"
3. **Given** a user enters incorrect password, **When** they submit login form, **Then** system increments failure counter and returns "Invalid email or password"
4. **Given** a user has 5 failed login attempts from same IP or email, **When** they attempt 6th login, **Then** system locks account for 15 minutes and returns "Too many failed attempts. Try again in 15 minutes"
5. **Given** a user with valid refresh token requests new access token, **When** refresh endpoint is called, **Then** system issues new access token, rotates refresh token (invalidates old, issues new), and updates session record

---

### User Story 3 - Password Reset via Magic Link (Priority: P2)

A user who forgot their password needs to reset it securely without contacting support. The system sends a time-limited magic link to their email.

**Why this priority**: Password reset is essential for user retention but not required for initial platform launch. Users can still register new accounts if needed.

**Independent Test**: Can be fully tested by requesting password reset, clicking magic link, and setting new password. Delivers self-service password recovery that can be demonstrated standalone.

**Acceptance Scenarios**:

1. **Given** a user enters their registered email on password reset page, **When** they submit the form, **Then** system generates single-use token (15-minute expiry), stores hash in password_reset_tokens table, and sends magic link email
2. **Given** a user clicks valid magic link within 15 minutes, **When** they access the link, **Then** system displays password reset form with token pre-filled
3. **Given** a user submits new password on reset form, **When** they submit, **Then** system validates password requirements, updates password hash, invalidates reset token, and redirects to login with success message
4. **Given** a user clicks expired or already-used magic link, **When** they access the link, **Then** system displays "This reset link has expired or been used. Please request a new one"

---

### User Story 4 - Email Verification (Priority: P2)

Teachers and admins must verify their email before accessing the platform. Students receive optional verification prompts but can access the platform immediately.

**Why this priority**: Email verification prevents abuse for privileged roles (teacher/admin) but shouldn't block student onboarding. This balances security with user friction.

**Independent Test**: Can be fully tested by registering as teacher/admin, receiving verification email, clicking link, and confirming email_verified_at timestamp is set. Delivers email verification flow that can be demonstrated standalone.

**Acceptance Scenarios**:

1. **Given** a teacher/admin registers, **When** account is created, **Then** system sends verification email with single-use token (24-hour expiry) and sets email_verified_at to NULL
2. **Given** a teacher/admin clicks verification link, **When** token is valid, **Then** system sets email_verified_at timestamp, invalidates token, and displays "Email verified! You can now log in"
3. **Given** a student registers, **When** account is created, **Then** system sends verification email but allows immediate login with banner "Please verify your email"
4. **Given** a user requests new verification email, **When** they click "Resend verification", **Then** system invalidates old token, generates new one, and sends new email

---

### User Story 5 - Role-Based Access Control (Priority: P1)

The system must enforce role-based permissions (student, teacher, admin) to protect sensitive endpoints and data. Each role has specific capabilities.

**Why this priority**: RBAC is critical for security and data isolation. Without it, students could access teacher analytics or admin functions. This is a security requirement that must be in place from day one.

**Independent Test**: Can be fully tested by attempting to access role-restricted endpoints with different user tokens and verifying 403 Forbidden responses. Delivers working authorization that can be demonstrated standalone.

**Acceptance Scenarios**:

1. **Given** a student token is used to access teacher-only endpoint, **When** request is made, **Then** system returns 403 Forbidden with message "Insufficient permissions"
2. **Given** an admin token is used to access any endpoint, **When** request is made, **Then** system allows access (admin has all permissions)
3. **Given** a teacher token is used to access student data for their class, **When** request is made, **Then** system allows access
4. **Given** a teacher token is used to access student data outside their class, **When** request is made, **Then** system returns 403 Forbidden

---

### User Story 6 - Session Management & Logout (Priority: P2)

Users need to securely log out from current device or all devices. The system must revoke tokens and clear sessions.

**Why this priority**: Session management is important for security but not blocking for initial launch. Users can simply close browser if logout isn't available initially.

**Independent Test**: Can be fully tested by logging in, calling logout endpoint, and verifying token is rejected on subsequent requests. Delivers session revocation that can be demonstrated standalone.

**Acceptance Scenarios**:

1. **Given** a logged-in user clicks logout, **When** logout endpoint is called, **Then** system marks session as revoked (sets revoked_at timestamp), invalidates refresh token, and returns success
2. **Given** a user with multiple active sessions clicks "Logout all devices", **When** endpoint is called, **Then** system revokes all sessions for that user_id and returns count of revoked sessions
3. **Given** a user attempts to use revoked refresh token, **When** refresh endpoint is called, **Then** system returns 401 Unauthorized with message "Session has been revoked"
4. **Given** a user's access token expires, **When** they access protected endpoint, **Then** system returns 401 Unauthorized with message "Token expired. Please refresh"

---

### User Story 7 - Current User Profile Retrieval (Priority: P1)

Authenticated users need to retrieve their own profile information to display in UI (dashboard, navbar, settings).

**Why this priority**: Every authenticated page needs to display user info (name, role, email). This is required for basic UI functionality across the platform.

**Independent Test**: Can be fully tested by calling /api/auth/me with valid token and verifying correct user data is returned. Delivers user profile retrieval that can be demonstrated standalone.

**Acceptance Scenarios**:

1. **Given** a user with valid access token calls /api/auth/me, **When** request is made, **Then** system returns user profile with id, email, role, display_name, email_verified_at
2. **Given** a user with expired token calls /api/auth/me, **When** request is made, **Then** system returns 401 Unauthorized
3. **Given** a user with tampered token calls /api/auth/me, **When** request is made, **Then** system returns 401 Unauthorized with message "Invalid token signature"

---

### Edge Cases

- What happens when a user's session is revoked while they have a valid access token? (Access token remains valid until expiry; refresh will fail)
- How does system handle concurrent login attempts from same user? (Both succeed; multiple sessions allowed)
- What happens when refresh token is used twice (replay attack)? (Second use fails; token already rotated and invalidated)
- How does system handle password reset for non-existent email? (Returns generic success message to prevent email enumeration)
- What happens when user changes password while having active sessions? (All sessions remain valid; user must manually logout all devices if desired)
- How does system handle rate limiting across distributed instances? (Rate limit counters stored in shared database with user_id/IP as key)
- What happens when JWT secret key is rotated? (All existing tokens become invalid; users must re-login)
- How does system handle timezone differences for token expiry? (All timestamps stored in UTC; expiry calculated server-side)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to register with email, password, and role (student/teacher/admin)
- **FR-002**: System MUST validate email format and reject invalid addresses
- **FR-003**: System MUST enforce password requirements: minimum 8 characters with at least one non-alphanumeric character
- **FR-004**: System MUST reject passwords found in HaveIBeenPwned breach database
- **FR-005**: System MUST hash passwords using bcrypt or Argon2 before storage (never store plaintext)
- **FR-006**: System MUST send verification email upon registration with single-use token (24-hour expiry)
- **FR-007**: System MUST require email verification before login for teacher and admin roles
- **FR-008**: System MUST allow students to login without email verification (with persistent banner prompt)
- **FR-009**: System MUST issue JWT access tokens with 15-minute expiry upon successful login
- **FR-010**: System MUST issue JWT refresh tokens with 7-day expiry upon successful login
- **FR-011**: System MUST store refresh token hash (not plaintext) in sessions table with user_id, device/user_agent, created_at, expires_at, revoked_at
- **FR-012**: System MUST rotate refresh tokens on every use (invalidate old, issue new)
- **FR-013**: System MUST enforce rate limiting: 5 failed login attempts per IP or email triggers 15-minute lockout
- **FR-014**: System MUST increment separate rate limit counters for both IP and email (lockout if either threshold hit)
- **FR-015**: System MUST support password reset via magic link with 15-minute expiry and single-use token
- **FR-016**: System MUST store password reset token hash in password_reset_tokens table
- **FR-017**: System MUST prevent email enumeration by returning generic success message for password reset regardless of email existence
- **FR-018**: System MUST enforce role-based access control with roles: student, teacher, admin
- **FR-019**: System MUST include role claim in JWT payload for authorization checks
- **FR-020**: System MUST validate role permissions in FastAPI middleware (not Kong)
- **FR-021**: System MUST support logout by marking session as revoked (set revoked_at timestamp)
- **FR-022**: System MUST support "logout all devices" by revoking all sessions for user_id
- **FR-023**: System MUST reject refresh token requests for revoked sessions
- **FR-024**: System MUST provide /api/auth/me endpoint returning id, email, role, display_name, email_verified_at
- **FR-025**: System MUST include nullable permissions JSONB column in users table for future permission expansion
- **FR-026**: System MUST include mfa_enabled boolean and mfa_secret (nullable) columns in users table for future MFA support
- **FR-027**: System MUST store email_verified_at as timestamp (not boolean) in users table
- **FR-028**: System MUST define JWT claims schema: sub (user_id), role, email, iat, exp as minimum required claims
- **FR-029**: System MUST use RS256 algorithm for JWT signing to enable Kong validation with public key
- **FR-030**: System MUST provide public key endpoint for Kong to validate JWT signatures

### Key Entities

- **User**: Represents a platform user with email, password_hash, role (student/teacher/admin), display_name, email_verified_at timestamp, mfa_enabled boolean, mfa_secret (nullable), permissions JSONB (nullable), created_at, updated_at
- **Session**: Represents an active user session with user_id (foreign key), refresh_token_hash, device/user_agent string, created_at, expires_at, revoked_at (nullable)
- **PasswordResetToken**: Represents a password reset request with user_id (foreign key), token_hash, created_at, expires_at, used_at (nullable)
- **EmailVerificationToken**: Represents an email verification request with user_id (foreign key), token_hash, created_at, expires_at, used_at (nullable)
- **RateLimitCounter**: Represents rate limiting state with identifier (IP or email), attempt_count, lockout_until (nullable), last_attempt_at

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete registration in under 2 minutes from landing page to email verification
- **SC-002**: Users can log in and access dashboard in under 10 seconds with valid credentials
- **SC-003**: System prevents 100% of brute force attacks by enforcing rate limiting after 5 failed attempts
- **SC-004**: System prevents 100% of compromised password usage by rejecting HaveIBeenPwned matches
- **SC-005**: Password reset flow completes in under 3 minutes from request to successful login
- **SC-006**: System handles 1000 concurrent authentication requests without degradation
- **SC-007**: Token refresh operations complete in under 500ms
- **SC-008**: Zero unauthorized access incidents due to role-based access control enforcement
- **SC-009**: 95% of users successfully complete registration on first attempt without errors
- **SC-010**: System maintains 99.9% uptime for authentication endpoints
- **SC-011**: All authentication operations are logged for security audit with timestamp, user_id, action, IP, result
- **SC-012**: JWT tokens are validated by Kong gateway with zero false positives or false negatives

## Assumptions

- Users have access to email for verification and password reset
- Frontend (Next.js) will handle Better Auth integration for session/cookie management
- Backend (FastAPI) will handle all token issuance and validation logic
- Kong API Gateway (F03) will validate JWT signatures using public key provided by auth service
- PostgreSQL database is available and configured (F02 dependency)
- HaveIBeenPwned API is accessible for password breach checking (fallback: skip check if API unavailable)
- Email service (SMTP or SendGrid) is configured for sending verification and reset emails
- System clock is synchronized across all instances for accurate token expiry validation
- Rate limiting counters are stored in PostgreSQL (not Redis) for MVP simplicity
- Single-region deployment for MVP (no cross-region token validation concerns)
- JWT secret key rotation is manual process for MVP (not automated)
- Session cleanup (expired sessions) is handled by scheduled job (not real-time)

## Out of Scope

- Multi-factor authentication (MFA) - infrastructure prepared but not implemented in MVP
- OAuth2/SSO integration (Google, GitHub, etc.) - only email/password for MVP
- Biometric authentication (fingerprint, face ID)
- Account recovery without email access (security questions, SMS)
- Granular permission system beyond role-based access (permissions JSONB prepared but unused)
- Real-time session monitoring dashboard
- Automated JWT secret key rotation
- Redis-based rate limiting (using PostgreSQL for MVP)
- Cross-region token validation and session replication
- Account lockout after repeated password reset requests
- IP geolocation-based suspicious login detection
- Device fingerprinting and trusted device management
- Session activity history and audit trail UI

## Dependencies

- **F02 (Database Schema & Migrations)**: Required for users, sessions, password_reset_tokens, email_verification_tokens, rate_limit_counters tables
- **F03 (API Gateway & Service Mesh)**: Required for Kong JWT validation configuration and public key distribution
- Email service configuration (SMTP/SendGrid) for verification and reset emails
- HaveIBeenPwned API access for password breach checking

## Risks

- **Kong JWT contract undefined**: If JWT claims schema is not agreed upon with F03 team before implementation, downstream services will fail validation. **Mitigation**: Define and document JWT claims schema in this spec (FR-028) and share with F03 team immediately.
- **Rate limiting in PostgreSQL may not scale**: Using database for rate limit counters could become bottleneck under high load. **Mitigation**: Accept for MVP; plan Redis migration if performance issues arise.
- **HaveIBeenPwned API downtime**: If API is unavailable, password breach checking fails. **Mitigation**: Implement fallback to skip check with warning log; consider caching breach database locally in future.
- **Token rotation complexity**: Refresh token rotation adds complexity and potential for race conditions. **Mitigation**: Use database transactions and unique constraints on refresh_token_hash to prevent double-use.
- **Email deliverability**: Verification and reset emails may land in spam. **Mitigation**: Use reputable email service (SendGrid), configure SPF/DKIM, include clear sender identity.

## Notes

- This specification is technology-agnostic and focuses on WHAT the system must do, not HOW to implement it
- Implementation details (FastAPI, Better Auth, Kong, PostgreSQL) are mentioned only for context and dependency tracking
- The planning phase (/sp.plan) will determine the technical architecture and implementation approach
- All security requirements follow OWASP best practices and NIST password guidelines
- JWT claims schema (FR-028) must be finalized and communicated to F03 team before any implementation begins
