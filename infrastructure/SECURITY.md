# Security Guidelines for LearnPyByAI Infrastructure

## Secrets Management

### DO NOT commit these files to Git:
- `*.pem`, `*.key`, `*.pub` - Private/public keys
- `backend/keys/` - JWT keys directory
- `backend/auth-service/keys/` - Auth service keys
- `.env`, `.env.local`, `.env.production` - Environment files with secrets
- `NEON_DATABASE.md` - Database credentials
- `*-secret.yaml` - Kubernetes secret manifests
- `*.backup` - Backup files that may contain secrets

### Before First Deployment:

1. **Generate JWT Keys** (if not already done):
   ```bash
   mkdir -p backend/auth-service/keys
   ssh-keygen -t rsa -b 2048 -m PEM -f backend/auth-service/keys/jwt_key -N ""
   openssl rsa -in backend/auth-service/keys/jwt_key -pubout -outform PEM -out backend/auth-service/keys/jwt_key.pub
   ```

2. **Create Infrastructure Environment File**:
   ```bash
   cp infrastructure/.env.example infrastructure/.env
   # Edit infrastructure/.env with your actual secrets
   ```

3. **Set Strong Passwords**:
   - Kong PostgreSQL password (KONG_PG_PASSWORD)
   - Redis password (REDIS_PASSWORD)
   - Neon database URL (NEON_DATABASE_URL)

4. **Create Kubernetes Secrets**:
   ```bash
   # Kong database password
   kubectl create secret generic kong-postgresql \
     --from-literal=password=$KONG_PG_PASSWORD \
     -n kong

   # Redis password
   kubectl create secret generic redis-secret \
     --from-literal=password=$REDIS_PASSWORD \
     -n default

   # JWT public key for Kong
   kubectl create secret generic kong-jwt-public-key \
     --from-file=public_key.pem=backend/auth-service/keys/jwt_key.pub \
     -n kong
   ```

### Hardcoded Passwords to Replace:

The following files contain placeholder passwords that MUST be replaced before production:

1. **infrastructure/kubernetes/kong/values.yaml**
   - `pg_password: kong` → Use Kubernetes secret or environment variable

2. **infrastructure/kubernetes/redis/values.yaml**
   - `password: "changeme"` → Use Kubernetes secret or environment variable

3. **infrastructure/kubernetes/kong/rate-limit-plugin.yaml**
   - `redis_password: changeme` → Use Kubernetes secret or environment variable

### Using Kubernetes Secrets (Recommended):

Instead of hardcoding passwords in YAML files, reference Kubernetes secrets:

```yaml
# Example: Kong values.yaml
env:
  pg_password:
    valueFrom:
      secretKeyRef:
        name: kong-postgresql
        key: password
```

### Verification Before Commit:

Run these checks before committing:

```bash
# Check for untracked secret files
git status | grep -E "(\.pem|\.key|\.env|secret)"

# Check for hardcoded secrets in staged files
git diff --cached | grep -i "password\|secret\|token\|api_key"

# Verify .gitignore is protecting secrets
git check-ignore backend/keys/jwt_key
git check-ignore infrastructure/.env
```

### Emergency: Secret Leaked to Git

If you accidentally commit secrets:

1. **Immediately rotate the compromised credentials**
2. **Remove from Git history**:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/secret/file" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push** (coordinate with team first):
   ```bash
   git push origin --force --all
   ```

## Production Deployment Checklist

- [ ] All JWT keys generated and stored securely
- [ ] All passwords changed from defaults
- [ ] Kubernetes secrets created for all sensitive data
- [ ] `.env` files not committed to Git
- [ ] `NEON_DATABASE.md` not committed to Git
- [ ] No `*.pem` or `*.key` files in Git
- [ ] All YAML files use secret references, not hardcoded values
- [ ] `.gitignore` updated and tested
- [ ] Team members aware of secrets management policy

## Contact

For security concerns, contact the security team immediately.
