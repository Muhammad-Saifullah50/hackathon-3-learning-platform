# Kong Setup Documentation

## Overview

This document describes the Kong API Gateway setup for the LearnPyByAI platform, including deployment, configuration, and troubleshooting.

## Architecture

Kong acts as the API Gateway for all LearnPyByAI microservices, providing:
- JWT authentication
- Rate limiting
- CORS handling
- Request transformation
- Health checks
- Load balancing

## Deployment

### Prerequisites

- Minikube cluster running
- Helm 3.x installed
- kubectl configured
- PostgreSQL deployed for Kong database

### Installation Steps

1. **Deploy PostgreSQL for Kong**:
   ```bash
   ./infrastructure/scripts/deploy-kong-postgres.sh
   ```

2. **Deploy Kong**:
   ```bash
   ./infrastructure/scripts/deploy-kong.sh
   ```

3. **Create JWT public key secret**:
   ```bash
   ./infrastructure/scripts/create-jwt-secret.sh
   ```

4. **Update Kong configuration with JWT key**:
   ```bash
   ./infrastructure/scripts/update-kong-jwt-key.sh
   ```

5. **Sync Kong configuration**:
   ```bash
   ./infrastructure/scripts/sync-kong-config.sh
   ```

6. **Verify Kong deployment**:
   ```bash
   ./infrastructure/scripts/verify-kong.sh
   ```

## Configuration

### Kong Helm Values

Location: `infrastructure/kubernetes/kong/values.yaml`

Key configurations:
- **Replicas**: 2 (for high availability)
- **Database**: PostgreSQL
- **Autoscaling**: 2-5 replicas based on CPU (70%)
- **Resources**: 250m CPU / 256Mi RAM (requests), 500m CPU / 512Mi RAM (limits)

### Plugins

#### JWT Authentication
- **File**: `infrastructure/kubernetes/kong/jwt-plugin.yaml`
- **Purpose**: Validates JWT tokens at gateway level
- **Configuration**:
  - Algorithm: RS256
  - Key claim: `iss`
  - Verified claims: `exp`
  - Header: `Authorization`

#### Request Transformer
- **File**: `infrastructure/kubernetes/kong/request-transformer-plugin.yaml`
- **Purpose**: Extracts JWT claims and forwards as headers
- **Headers added**:
  - `X-User-Id`: from `jwt.claims.sub`
  - `X-User-Email`: from `jwt.claims.email`
  - `X-User-Role`: from `jwt.claims.role`
  - `X-Session-Id`: from `jwt.claims.session_id`

#### CORS
- **File**: `infrastructure/kubernetes/kong/cors-plugin.yaml`
- **Purpose**: Enables cross-origin requests from frontend
- **Allowed origins**: `http://localhost:3000`, `https://learnpybyai.com`
- **Credentials**: Enabled

#### Rate Limiting
- **File**: `infrastructure/kubernetes/kong/rate-limit-plugin.yaml`
- **Purpose**: Prevents API abuse
- **Limits**: 10 requests/minute, 600 requests/hour per consumer
- **Backend**: Redis (for accuracy across replicas)

### Routes

Location: `infrastructure/kubernetes/kong/kong-configuration.yaml`

**Public routes** (no JWT required):
- `/api/auth/login` - POST
- `/api/auth/register` - POST
- `/api/auth/refresh` - POST
- `/api/auth/public-key` - GET

**Protected routes** (JWT required):
- `/api/auth/logout` - POST
- `/api/users/*` - All methods
- `/api/sandbox/*` - All methods
- `/api/llm/*` - All methods
- `/api/agents/*` - All methods
- `/api/teacher/*` - All methods

### Health Checks

Location: `infrastructure/kubernetes/kong/health-checks.yaml`

**Active health checks**:
- Interval: 5 seconds
- Success threshold: 3 consecutive successes
- Failure threshold: 3 consecutive failures
- Endpoint: `/health`
- Timeout: 1 second

**Passive health checks**:
- Success threshold: 5 successful requests
- Failure threshold: 5 failed requests
- Monitored status codes: 429, 500, 503 (unhealthy)

## Accessing Kong

### Admin API

Port-forward to access Admin API:
```bash
kubectl port-forward -n kong svc/kong-kong-admin 8001:8001
```

Then access: `http://localhost:8001`

### Proxy

Get proxy URL:
```bash
minikube service -n kong kong-kong-proxy --url
```

Or port-forward:
```bash
kubectl port-forward -n kong svc/kong-kong-proxy 8000:8000
```

## Troubleshooting

### Kong pods not starting

**Symptom**: Kong pods stuck in `CrashLoopBackOff` or `Pending`

**Possible causes**:
1. PostgreSQL not running
2. Database migrations not completed
3. Insufficient resources

**Solutions**:
```bash
# Check PostgreSQL
kubectl get pods -n kong -l app.kubernetes.io/name=postgresql

# Check Kong logs
kubectl logs -n kong -l app.kubernetes.io/name=kong --tail=50

# Run migrations manually
kubectl exec -n kong deployment/kong-kong -- kong migrations bootstrap
kubectl exec -n kong deployment/kong-kong -- kong migrations up

# Check resource usage
kubectl top pods -n kong
```

### JWT validation failing

**Symptom**: 401 Unauthorized on protected routes

**Possible causes**:
1. JWT public key not configured
2. Token expired
3. Invalid token format

**Solutions**:
```bash
# Verify JWT secret exists
kubectl get secret kong-jwt-public-key -n kong

# Check Kong JWT consumer
kubectl port-forward -n kong svc/kong-kong-admin 8001:8001
curl http://localhost:8001/consumers/learnpybyai-auth/jwt

# Test with valid token
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/users/me
```

### Rate limiting not working

**Symptom**: No 429 responses after exceeding limits

**Possible causes**:
1. Redis not accessible
2. Rate limiting plugin not applied
3. Wrong identifier (not using consumer)

**Solutions**:
```bash
# Test Redis connectivity from Kong
kubectl exec -n kong deployment/kong-kong -- redis-cli -h redis-master.default.svc.cluster.local -a changeme ping

# Verify rate limiting plugin
curl http://localhost:8001/plugins | jq '.data[] | select(.name=="rate-limiting")'

# Check Redis for rate limit keys
kubectl exec -n default redis-master-0 -- redis-cli -a changeme KEYS "ratelimit:*"
```

### Configuration sync failing

**Symptom**: `deck sync` command fails

**Possible causes**:
1. Invalid YAML syntax
2. Kong Admin API not accessible
3. Missing dependencies (consumers, services)

**Solutions**:
```bash
# Validate YAML syntax
yamllint infrastructure/kubernetes/kong/kong-configuration.yaml

# Test Admin API connectivity
curl http://localhost:8001/status

# Dry-run sync
deck sync --kong-addr http://localhost:8001 --state infrastructure/kubernetes/kong/kong-configuration.yaml --dry-run
```

## Monitoring

### Key Metrics

Monitor these Kong metrics:
- Request rate (requests/second)
- Latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active connections
- Upstream health status

### Logs

View Kong logs:
```bash
kubectl logs -n kong -l app.kubernetes.io/name=kong --tail=100 -f
```

### Health Status

Check Kong health:
```bash
curl http://localhost:8001/status
```

## References

- [Kong Documentation](https://docs.konghq.com/)
- [Kong Kubernetes Deployment](https://docs.konghq.com/kubernetes-ingress-controller/)
- [Kong Plugins](https://docs.konghq.com/hub/)
- [deck CLI](https://docs.konghq.com/deck/)
