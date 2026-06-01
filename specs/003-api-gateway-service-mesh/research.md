# Research: API Gateway & Service Mesh Setup

**Feature**: 003-api-gateway-service-mesh
**Date**: 2026-03-15
**Status**: Complete

## Overview

This document consolidates research findings for deploying Kong API Gateway and Dapr service mesh on Kubernetes (Minikube) for the LearnPyByAI platform.

---

## 1. Testing Strategy for Infrastructure Components

### Decision: Python-based integration testing with pytest

**Rationale:**
- Aligns with constitution's testing principles (pytest for backend)
- Enables programmatic testing of Kong Admin API and Dapr HTTP API
- Supports async testing with pytest-asyncio for realistic service invocation patterns
- Testcontainers-python allows testing with real Redis/PostgreSQL instances

**Testing Approach:**

| Component | Test Type | Tools | Coverage Target |
|-----------|-----------|-------|-----------------|
| Kong Routing | Integration | pytest + httpx | 85% |
| JWT Validation | Integration | pytest + httpx | 85% |
| Rate Limiting | Integration | pytest + httpx | 80% |
| Dapr Service Invocation | Integration | pytest + Dapr Python SDK | 80% |
| Dapr Pub/Sub | Integration | pytest + Dapr Python SDK | 80% |
| Health Checks | E2E | pytest + kubectl | 70% |

**Key Testing Patterns:**

```python
# Kong routing test pattern
@pytest.mark.asyncio
async def test_kong_routes_to_backend(kong_admin_client, kong_route):
    response = await kong_admin_client.get(f"/routes/{kong_route['id']}")
    assert response.status_code == 200
    assert response.json()["paths"] == ["/api/test"]

# Dapr service invocation test pattern
@pytest.mark.asyncio
async def test_dapr_service_invocation():
    with patch('dapr.clients.DaprClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.invoke_method.return_value = {"result": "success"}

        client = DaprClient()
        result = await client.invoke_method("target-service", "method", {})
        assert result["result"] == "success"

# Pub/sub delivery test pattern
@pytest.mark.asyncio
async def test_dapr_publish_message():
    with patch('dapr.clients.DaprClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        client = DaprClient()
        await client.publish_event("pubsub", "topic", {"data": "test"})
        mock_instance.publish_event.assert_called_once()
```

**Alternatives Considered:**
- Shell script testing (rejected: not maintainable, no assertions)
- Postman/Newman (rejected: not integrated with CI, manual setup)
- Go-based testing (rejected: team expertise in Python)

---

## 2. Kong JWT Authentication Configuration

### Decision: RSA256 JWT validation with Kong JWT plugin + Request Transformer

**Rationale:**
- Kong validates tokens at gateway level (no backend validation needed)
- RSA public key stored in Kubernetes Secret (secure, rotatable)
- Request Transformer extracts JWT claims and forwards as headers to backend services
- Aligns with constitution's security constraints (JWT authentication enforced)

**Configuration Pattern:**

```yaml
# JWT Plugin Configuration
jwt:
  key_claim_name: "iss"              # Issuer claim identifies the consumer
  secret_is_base64: false            # RSA keys are PEM-formatted
  run_on_preflight: false            # Skip validation on CORS OPTIONS
  claims_to_verify: ["exp"]         # Verify token expiration
  header_names: ["Authorization"]   # Extract from Authorization header

# Request Transformer for claim extraction
request-transformer:
  add:
    headers:
      - "X-User-Id:$(jwt.claims.sub)"
      - "X-User-Email:$(jwt.claims.email)"
      - "X-User-Role:$(jwt.claims.role)"
      - "X-Session-Id:$(jwt.claims.session_id)"
```

**JWT Validation Flow:**
1. Client sends request with `Authorization: Bearer <token>`
2. Kong extracts token and decodes header/payload
3. Kong verifies signature using cached RSA public key
4. Kong checks token expiration (exp claim)
5. Kong adds consumer headers (X-Consumer-ID, X-Consumer-Username)
6. Request Transformer adds custom headers from JWT claims
7. Kong forwards request to backend service with all headers

**Key Configuration Details:**
- Public key stored in Kubernetes Secret: `kong-jwt-public-key`
- Kong Consumer created with username: `learnpybyai-auth`
- JWT credential configured with algorithm: `RS256`
- Token refresh handled by auth-service (bypasses Kong JWT validation)

**Alternatives Considered:**
- Backend JWT validation (rejected: duplicates validation logic, higher latency)
- Symmetric HS256 (rejected: less secure, shared secret distribution)
- OAuth2 plugin (rejected: overkill for MVP, adds complexity)

---

## 3. Dapr Service Invocation Patterns

### Decision: HTTP service invocation with automatic retries and circuit breakers

**Rationale:**
- HTTP protocol aligns with existing FastAPI services (no gRPC refactoring needed)
- Dapr handles inter-sidecar communication via gRPC automatically (performance benefit)
- Declarative resiliency policies enable retries and circuit breakers without code changes
- Service discovery via app-id simplifies configuration (no hardcoded IPs)

**Service Invocation Pattern:**

```bash
# Invocation format
curl http://localhost:3500/v1.0/invoke/{app-id}/method/{method-name}

# Example: Triage agent calls concepts agent
curl -X POST http://localhost:3500/v1.0/invoke/concepts-agent/method/explain \
  -H "Content-Type: application/json" \
  -d '{"topic": "variables", "level": "beginner"}'
```

**Sidecar Configuration (Kubernetes annotations):**

```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "concepts-agent"
  dapr.io/app-port: "8000"
  dapr.io/app-protocol: "http"
  dapr.io/config: "resiliency-config"
  dapr.io/log-level: "info"
```

**Resiliency Configuration:**

```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: resiliency-config
spec:
  resiliency:
    policies:
      retries:
        general:
          maxRetries: 3
          backoff:
            initialInterval: 100ms
            maxInterval: 1s
            multiplier: 2.0
      circuitBreakers:
        general:
          maxRequests: 100
          interval: 30s
          timeout: 10s
          trip: consecutiveFailures >= 5
    targets:
      apps:
        concepts-agent:
          retry: general
          circuitBreaker: general
```

**Automatic Headers Added by Dapr:**
- `dapr-caller-app-id` - Identifies calling service
- `dapr-caller-namespace` - Caller's namespace
- `dapr-callee-app-id` - Target service identifier

**Alternatives Considered:**
- Direct HTTP calls (rejected: no service discovery, no retries, no observability)
- gRPC service invocation (rejected: requires service refactoring, added complexity)
- Message queue for all communication (rejected: synchronous calls need immediate response)

---

## 4. Dapr Pub/Sub with Redis

### Decision: Redis Streams for pub/sub with declarative subscriptions

**Rationale:**
- Redis already required for Kong rate limiting (shared infrastructure)
- Redis Streams provide at-least-once delivery guarantee
- Declarative subscriptions enable routing rules without code changes
- Dead letter topics handle failed messages automatically

**Redis Pub/Sub Component:**

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: learnpybyai-pubsub
spec:
  type: pubsub.redis
  version: v1
  metadata:
  - name: redisHost
    value: "redis-master.default.svc.cluster.local:6379"
  - name: redisPassword
    secretKeyRef:
      name: redis-secret
      key: password
  - name: consumerID
    value: "{podName}"
  - name: enableTLS
    value: "false"  # Local dev only
```

**Subscription Pattern:**

```yaml
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: struggle-alerts-subscription
spec:
  pubsubname: learnpybyai-pubsub
  topic: struggle-alerts
  routes:
    default: /webhooks/struggle-alert
  deadLetterTopic: struggle-alerts-deadletter
  scopes:
  - teacher-service
```

**Pub/Sub Topics for LearnPyByAI:**

| Topic | Publisher | Subscribers | Purpose |
|-------|-----------|-------------|---------|
| `struggle-alerts` | debug-agent | teacher-service | Notify teachers of struggling students |
| `quiz-completed` | exercise-agent | progress-agent | Update mastery scores after quiz |
| `code-submitted` | sandbox-service | code-review-agent, progress-agent | Trigger code review and progress update |
| `mastery-updated` | progress-agent | user-service | Sync mastery scores to user profile |

**Message Acknowledgment:**
- Return `200 OK` for successful processing
- Any other status code triggers retry (up to 3 attempts)
- Failed messages after retries go to dead letter topic

**Alternatives Considered:**
- Kafka (rejected: overkill for MVP, higher resource usage, more complex setup)
- RabbitMQ (rejected: additional infrastructure, team unfamiliar)
- In-memory pub/sub (rejected: no persistence, messages lost on restart)

---

## 5. Kong Routing and Rate Limiting

### Decision: Path-based routing with per-consumer rate limiting via Redis

**Rationale:**
- Path-based routing (`/api/auth/*`, `/api/users/*`) maps cleanly to microservices
- Per-consumer rate limiting prevents abuse while allowing fair usage
- Redis backend ensures accurate rate limiting across multiple Kong replicas
- CORS plugin enables frontend requests from allowed origins

**Routing Configuration:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: learnpybyai-api
  annotations:
    konghq.com/plugins: jwt-auth,rate-limit-consumer,cors-plugin
spec:
  ingressClassName: kong
  rules:
  - host: api.learnpybyai.local
    http:
      paths:
      - path: /api/auth
        pathType: Prefix
        backend:
          service:
            name: auth-service
            port:
              number: 8000
      - path: /api/users
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 8000
      - path: /api/sandbox
        pathType: Prefix
        backend:
          service:
            name: sandbox-service
            port:
              number: 8000
      - path: /api/agents
        pathType: Prefix
        backend:
          service:
            name: triage-agent
            port:
              number: 8000
```

**Rate Limiting Configuration:**

```yaml
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: rate-limit-consumer
spec:
  plugin: rate-limiting
  config:
    minute: 10                     # 10 requests per minute per user
    policy: redis                  # Redis backend for accuracy
    redis_host: redis.default.svc.cluster.local
    redis_port: 6379
    identifier: consumer           # Rate limit per authenticated user
    fault_tolerant: true           # Continue if Redis unavailable
```

**CORS Configuration:**

```yaml
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: cors-plugin
spec:
  plugin: cors
  config:
    allowed_origins:
    - "http://localhost:3000"      # Local development
    - "https://learnpybyai.com"      # Production frontend
    allowed_methods:
    - GET
    - POST
    - PUT
    - DELETE
    - PATCH
    - OPTIONS
    allowed_headers:
    - Content-Type
    - Authorization
    credentials: true
    max_age: 3600
```

**Health Check Configuration:**

```yaml
apiVersion: configuration.konghq.com/v1
kind: KongIngress
metadata:
  name: service-health-checks
spec:
  upstream:
    healthchecks:
      active:
        healthy:
          interval: 5              # Check every 5 seconds
          successes: 3             # Mark healthy after 3 successes
        unhealthy:
          interval: 5
          http_failures: 3         # Mark unhealthy after 3 failures
          timeouts: 3
        http_path: /health
        type: http
        timeout: 1
```

**Alternatives Considered:**
- IP-based rate limiting (rejected: doesn't account for authenticated users)
- Local rate limiting policy (rejected: inaccurate with multiple Kong replicas)
- No CORS plugin (rejected: frontend requests would fail)

---

## 6. Deployment Strategy

### Decision: Helm charts for Kong and Dapr, kubectl for services

**Rationale:**
- Helm provides reproducible deployments with version control
- Kong and Dapr have official Helm charts (battle-tested, maintained)
- Service manifests are simple enough for kubectl apply
- Bash scripts automate deployment sequence for local development

**Deployment Sequence:**

1. **Setup Minikube** - Start cluster with sufficient resources
2. **Deploy Redis** - Shared infrastructure for Kong rate limiting and Dapr pub/sub
3. **Deploy Kong** - API Gateway with JWT, rate limiting, CORS plugins
4. **Deploy Dapr** - Service mesh with resiliency configuration
5. **Deploy Services** - All 11 microservices with Dapr sidecars
6. **Apply Kong Routes** - Configure routing and plugins
7. **Apply Dapr Subscriptions** - Configure pub/sub topics

**Helm Configuration:**

```bash
# Kong deployment
helm install kong kong/kong \
  -f infrastructure/kubernetes/kong/values.yaml \
  -n kong \
  --create-namespace

# Dapr deployment
helm install dapr dapr/dapr \
  -f infrastructure/kubernetes/dapr/values.yaml \
  -n dapr-system \
  --create-namespace
```

**Alternatives Considered:**
- Terraform (rejected: overkill for local dev, team unfamiliar)
- Kustomize (rejected: Helm charts already available)
- Manual kubectl apply (rejected: not reproducible, error-prone)

---

## 7. Local Development and Testing

### Decision: Minikube with LoadBalancer via minikube tunnel

**Rationale:**
- Minikube provides full Kubernetes environment locally
- LoadBalancer services work via `minikube tunnel`
- Sufficient for 11 microservices with resource limits
- Matches production Kubernetes environment closely

**Minikube Configuration:**

```bash
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=20g \
  --driver=docker \
  --kubernetes-version=v1.28.0
```

**Testing Workflow:**

1. Deploy infrastructure (Kong, Dapr, Redis)
2. Deploy services with Dapr sidecars
3. Run integration tests (pytest)
4. Test API requests through Kong gateway
5. Test service-to-service invocation via Dapr
6. Test pub/sub message delivery
7. Verify health checks and rate limiting

**Alternatives Considered:**
- Kind (rejected: LoadBalancer support requires MetalLB setup)
- Docker Compose (rejected: doesn't match production Kubernetes)
- Remote Kubernetes cluster (rejected: slower iteration, costs money)

---

## Summary

All technical unknowns have been resolved. The implementation plan can proceed to Phase 1 (Design & Contracts) with confidence in the chosen technologies and patterns.

**Key Decisions:**
1. ✅ Testing: Python + pytest + httpx + Dapr SDK
2. ✅ Kong JWT: RSA256 validation with Request Transformer for claim extraction
3. ✅ Dapr Invocation: HTTP protocol with automatic retries and circuit breakers
4. ✅ Dapr Pub/Sub: Redis Streams with declarative subscriptions
5. ✅ Kong Routing: Path-based with per-consumer rate limiting via Redis
6. ✅ Deployment: Helm for Kong/Dapr, kubectl for services
7. ✅ Local Dev: Minikube with 4 CPUs, 8GB RAM

**Next Steps:**
- Phase 1: Create data-model.md (entities and relationships)
- Phase 1: Generate API contracts in /contracts/ directory
- Phase 1: Create quickstart.md (deployment guide)
- Phase 1: Update agent context with new technologies
