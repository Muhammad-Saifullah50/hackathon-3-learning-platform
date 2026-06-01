# Data Model: API Gateway & Service Mesh Setup

**Feature**: 003-api-gateway-service-mesh
**Date**: 2026-03-15
**Status**: Complete

## Overview

This document defines the configuration entities and their relationships for Kong API Gateway and Dapr service mesh infrastructure.

---

## 1. Kong Configuration Entities

### 1.1 Service

Represents an upstream backend microservice.

**Attributes:**
- `id` (UUID) - Unique identifier
- `name` (string) - Service name (e.g., "auth-service")
- `url` (string) - Upstream URL (e.g., "http://auth-service:8000")
- `protocol` (enum) - Protocol: http, https, grpc, grpcs
- `connect_timeout` (integer) - Connection timeout in milliseconds (default: 60000)
- `write_timeout` (integer) - Write timeout in milliseconds (default: 60000)
- `read_timeout` (integer) - Read timeout in milliseconds (default: 60000)
- `retries` (integer) - Number of retries (default: 5)
- `tags` (array[string]) - Tags for organization

**Relationships:**
- Has many Routes
- Has many Plugins

**Validation Rules:**
- `name` must be unique
- `url` must be valid HTTP/HTTPS/gRPC URL
- Timeouts must be positive integers

---

### 1.2 Route

Defines how requests are routed to services.

**Attributes:**
- `id` (UUID) - Unique identifier
- `name` (string) - Route name (e.g., "auth-login")
- `paths` (array[string]) - URL paths (e.g., ["/api/auth/login"])
- `methods` (array[string]) - HTTP methods (e.g., ["GET", "POST"])
- `hosts` (array[string]) - Hostnames (e.g., ["api.learnpybyai.local"])
- `strip_path` (boolean) - Strip matched path before forwarding (default: false)
- `preserve_host` (boolean) - Preserve original Host header (default: false)
- `protocols` (array[string]) - Protocols: http, https, grpc, grpcs
- `service` (object) - Reference to Service entity
- `tags` (array[string]) - Tags for organization

**Relationships:**
- Belongs to one Service
- Has many Plugins

**Validation Rules:**
- Must have at least one of: paths, methods, hosts, headers
- `paths` must start with "/"
- `methods` must be valid HTTP methods
- Must reference an existing Service

---

### 1.3 Consumer

Represents an authenticated API consumer.

**Attributes:**
- `id` (UUID) - Unique identifier
- `username` (string) - Consumer username (e.g., "learnpybyai-auth")
- `custom_id` (string) - External system identifier
- `tags` (array[string]) - Tags for organization

**Relationships:**
- Has many Credentials (JWT, Key Auth, OAuth2, etc.)
- Has many Plugins (rate limiting, ACL, etc.)

**Validation Rules:**
- `username` must be unique
- `custom_id` must be unique if provided

---

### 1.4 JWT Credential

JWT authentication credential for a consumer.

**Attributes:**
- `id` (UUID) - Unique identifier
- `consumer` (object) - Reference to Consumer entity
- `key` (string) - JWT issuer identifier (e.g., "learnpybyai-jwt-issuer")
- `algorithm` (enum) - Algorithm: HS256, HS384, HS512, RS256, RS384, RS512, ES256, ES384, ES512
- `rsa_public_key` (string) - RSA public key (PEM format)
- `secret` (string) - HMAC secret (for HS* algorithms)
- `tags` (array[string]) - Tags for organization

**Relationships:**
- Belongs to one Consumer

**Validation Rules:**
- `key` must be unique
- `algorithm` must be valid JWT algorithm
- `rsa_public_key` required for RS* algorithms
- `secret` required for HS* algorithms
- Public key must be valid PEM format

---

### 1.5 Plugin

Extends Kong functionality (authentication, rate limiting, CORS, etc.).

**Attributes:**
- `id` (UUID) - Unique identifier
- `name` (string) - Plugin name (e.g., "jwt", "rate-limiting", "cors")
- `config` (object) - Plugin-specific configuration
- `enabled` (boolean) - Enable/disable plugin (default: true)
- `protocols` (array[string]) - Protocols to apply: http, https, grpc, grpcs
- `service` (object) - Reference to Service (optional)
- `route` (object) - Reference to Route (optional)
- `consumer` (object) - Reference to Consumer (optional)
- `tags` (array[string]) - Tags for organization

**Relationships:**
- Optionally belongs to one Service
- Optionally belongs to one Route
- Optionally belongs to one Consumer

**Validation Rules:**
- `name` must be a valid Kong plugin name
- `config` must match plugin schema
- At least one of service, route, consumer, or global scope

**Plugin Configurations:**

#### JWT Plugin Config
```yaml
key_claim_name: "iss"
secret_is_base64: false
run_on_preflight: false
claims_to_verify: ["exp"]
header_names: ["Authorization"]
```

#### Rate Limiting Plugin Config
```yaml
minute: 10
hour: 600
policy: "redis"
redis_host: "redis.default.svc.cluster.local"
redis_port: 6379
identifier: "consumer"
fault_tolerant: true
```

#### CORS Plugin Config
```yaml
allowed_origins: ["http://localhost:3000", "https://learnpybyai.com"]
allowed_methods: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
allowed_headers: ["Content-Type", "Authorization"]
credentials: true
max_age: 3600
```

#### Request Transformer Plugin Config
```yaml
add:
  headers:
    - "X-User-Id:$(jwt.claims.sub)"
    - "X-User-Email:$(jwt.claims.email)"
    - "X-User-Role:$(jwt.claims.role)"
    - "X-Session-Id:$(jwt.claims.session_id)"
```

---

### 1.6 Upstream

Represents a load-balanced backend with health checks.

**Attributes:**
- `id` (UUID) - Unique identifier
- `name` (string) - Upstream name (e.g., "auth-upstream")
- `algorithm` (enum) - Load balancing algorithm: round-robin, consistent-hashing, least-connections
- `hash_on` (enum) - Hash on: none, consumer, ip, header, cookie
- `healthchecks` (object) - Health check configuration
- `tags` (array[string]) - Tags for organization

**Relationships:**
- Has many Targets

**Health Check Configuration:**
```yaml
active:
  healthy:
    interval: 5
    successes: 3
  unhealthy:
    interval: 5
    http_failures: 3
    tcp_failures: 3
    timeouts: 3
  http_path: "/health"
  type: "http"
  timeout: 1
passive:
  healthy:
    successes: 5
  unhealthy:
    http_failures: 5
    tcp_failures: 5
    timeouts: 7
  type: "http"
```

---

### 1.7 Target

Backend instance within an upstream.

**Attributes:**
- `id` (UUID) - Unique identifier
- `upstream` (object) - Reference to Upstream entity
- `target` (string) - Target address (e.g., "auth-service:8000")
- `weight` (integer) - Load balancing weight (default: 100)
- `tags` (array[string]) - Tags for organization

**Relationships:**
- Belongs to one Upstream

**Validation Rules:**
- `target` must be valid hostname:port or IP:port
- `weight` must be between 0 and 1000

---

## 2. Dapr Configuration Entities

### 2.1 Component

Dapr building block component (pub/sub, state store, bindings, etc.).

**Attributes:**
- `apiVersion` (string) - API version: "dapr.io/v1alpha1"
- `kind` (string) - Kind: "Component"
- `metadata.name` (string) - Component name (e.g., "learnpybyai-pubsub")
- `metadata.namespace` (string) - Kubernetes namespace
- `spec.type` (string) - Component type (e.g., "pubsub.redis")
- `spec.version` (string) - Component version (e.g., "v1")
- `spec.metadata` (array[object]) - Component-specific configuration
- `auth.secretStore` (string) - Secret store for credentials

**Component Types:**
- `pubsub.redis` - Redis pub/sub
- `state.redis` - Redis state store
- `bindings.kafka` - Kafka binding
- `secretstores.kubernetes` - Kubernetes secrets

**Redis Pub/Sub Metadata:**
```yaml
- name: redisHost
  value: "redis-master.default.svc.cluster.local:6379"
- name: redisPassword
  secretKeyRef:
    name: redis-secret
    key: password
- name: consumerID
  value: "{podName}"
- name: enableTLS
  value: "false"
```

**Validation Rules:**
- `metadata.name` must be unique within namespace
- `spec.type` must be valid Dapr component type
- `spec.metadata` must match component schema

---

### 2.2 Subscription

Declarative pub/sub subscription.

**Attributes:**
- `apiVersion` (string) - API version: "dapr.io/v2alpha1"
- `kind` (string) - Kind: "Subscription"
- `metadata.name` (string) - Subscription name
- `metadata.namespace` (string) - Kubernetes namespace
- `spec.pubsubname` (string) - Reference to pub/sub component
- `spec.topic` (string) - Topic name
- `spec.routes` (object) - Message routing configuration
- `spec.deadLetterTopic` (string) - Dead letter topic name
- `spec.scopes` (array[string]) - App IDs allowed to use subscription

**Routes Configuration:**
```yaml
routes:
  default: "/webhooks/default"
  rules:
  - match: 'event.type == "OrderCreated"'
    path: "/webhooks/order-created"
  - match: 'event.type == "OrderCancelled"'
    path: "/webhooks/order-cancelled"
```

**Validation Rules:**
- `spec.pubsubname` must reference existing Component
- `spec.topic` must be non-empty string
- `spec.routes.default` must be valid HTTP path
- `spec.scopes` must contain valid app IDs

---

### 2.3 Configuration

Dapr runtime configuration (resiliency, tracing, metrics).

**Attributes:**
- `apiVersion` (string) - API version: "dapr.io/v1alpha1"
- `kind` (string) - Kind: "Configuration"
- `metadata.name` (string) - Configuration name
- `metadata.namespace` (string) - Kubernetes namespace
- `spec.tracing` (object) - Distributed tracing configuration
- `spec.metric` (object) - Metrics configuration
- `spec.resiliency` (object) - Resiliency policies

**Resiliency Configuration:**
```yaml
resiliency:
  policies:
    timeouts:
      general: 5s
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

**Validation Rules:**
- Timeout values must be valid duration strings
- Retry maxRetries must be non-negative integer
- Circuit breaker trip condition must be valid expression

---

### 2.4 Dapr Sidecar Annotations

Kubernetes pod annotations for Dapr sidecar injection.

**Attributes:**
- `dapr.io/enabled` (string) - Enable sidecar: "true" or "false"
- `dapr.io/app-id` (string) - Application identifier (no dots)
- `dapr.io/app-port` (string) - Application listening port
- `dapr.io/app-protocol` (string) - Protocol: http, grpc, https, grpcs, h2c
- `dapr.io/config` (string) - Reference to Configuration resource
- `dapr.io/log-level` (string) - Log level: debug, info, warn, error
- `dapr.io/enable-metrics` (string) - Enable metrics: "true" or "false"
- `dapr.io/metrics-port` (string) - Metrics port (default: 9090)
- `dapr.io/sidecar-cpu-limit` (string) - CPU limit (e.g., "500m")
- `dapr.io/sidecar-memory-limit` (string) - Memory limit (e.g., "512Mi")

**Example:**
```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "concepts-agent"
  dapr.io/app-port: "8000"
  dapr.io/app-protocol: "http"
  dapr.io/config: "resiliency-config"
  dapr.io/log-level: "info"
```

**Validation Rules:**
- `dapr.io/app-id` must not contain dots
- `dapr.io/app-port` must be valid port number
- `dapr.io/app-protocol` must be valid protocol
- `dapr.io/config` must reference existing Configuration

---

## 3. LearnPyByAI Service Topology

### 3.1 Microservices

| Service | App ID | Port | Dapr Enabled | Kong Route |
|---------|--------|------|--------------|------------|
| Auth Service | `auth-service` | 8000 | Yes | `/api/auth/*` |
| User Service | `user-service` | 8000 | Yes | `/api/users/*` |
| Sandbox Service | `sandbox-service` | 8000 | Yes | `/api/sandbox/*` |
| LLM Service | `llm-service` | 8000 | Yes | `/api/llm/*` |
| Triage Agent | `triage-agent` | 8000 | Yes | `/api/agents/triage/*` |
| Concepts Agent | `concepts-agent` | 8000 | Yes | `/api/agents/concepts/*` |
| Code Review Agent | `code-review-agent` | 8000 | Yes | `/api/agents/code-review/*` |
| Debug Agent | `debug-agent` | 8000 | Yes | `/api/agents/debug/*` |
| Exercise Agent | `exercise-agent` | 8000 | Yes | `/api/agents/exercise/*` |
| Progress Agent | `progress-agent` | 8000 | Yes | `/api/agents/progress/*` |
| Teacher Service | `teacher-service` | 8000 | Yes | `/api/teacher/*` |

---

### 3.2 Pub/Sub Topics

| Topic | Publisher(s) | Subscriber(s) | Purpose |
|-------|-------------|---------------|---------|
| `struggle-alerts` | debug-agent | teacher-service | Notify teachers of struggling students |
| `quiz-completed` | exercise-agent | progress-agent | Update mastery scores after quiz |
| `code-submitted` | sandbox-service | code-review-agent, progress-agent | Trigger code review and progress update |
| `mastery-updated` | progress-agent | user-service | Sync mastery scores to user profile |

---

### 3.3 Service Invocation Patterns

| Caller | Callee | Method | Purpose |
|--------|--------|--------|---------|
| triage-agent | concepts-agent | `/explain` | Route concept explanation requests |
| triage-agent | debug-agent | `/analyze-error` | Route debugging requests |
| triage-agent | code-review-agent | `/review` | Route code review requests |
| concepts-agent | llm-service | `/generate` | Generate concept explanations |
| debug-agent | llm-service | `/generate` | Generate debugging hints |
| code-review-agent | llm-service | `/generate` | Generate code review feedback |
| exercise-agent | llm-service | `/generate` | Generate coding exercises |
| progress-agent | user-service | `/update-mastery` | Update user mastery scores |
| teacher-service | exercise-agent | `/generate-exercise` | Generate custom exercises |

---

## 4. State Transitions

### 4.1 Kong Route State

```
Created → Enabled → Disabled → Deleted
```

- **Created**: Route configured but not yet active
- **Enabled**: Route actively routing traffic
- **Disabled**: Route exists but not routing traffic
- **Deleted**: Route removed from configuration

---

### 4.2 Dapr Subscription State

```
Pending → Active → Failed → Deleted
```

- **Pending**: Subscription created, waiting for component
- **Active**: Subscription receiving messages
- **Failed**: Subscription component unavailable
- **Deleted**: Subscription removed

---

### 4.3 Health Check State

```
Unknown → Healthy → Unhealthy → Healthy
```

- **Unknown**: Initial state, no checks performed
- **Healthy**: Service passing health checks
- **Unhealthy**: Service failing health checks
- **Healthy**: Service recovered after failure

---

## 5. Entity Relationship Diagram

```
Kong Configuration:
  Service (1) ──< (N) Route
  Service (1) ──< (N) Plugin
  Route (1) ──< (N) Plugin
  Consumer (1) ──< (N) JWT Credential
  Consumer (1) ──< (N) Plugin
  Upstream (1) ──< (N) Target
  Service (1) ──> (1) Upstream

Dapr Configuration:
  Component (1) ──< (N) Subscription
  Configuration (1) ──< (N) Pod Annotation
  Subscription (N) ──> (1) Component

LearnPyByAI Topology:
  Kong Route (1) ──> (1) Microservice
  Microservice (1) ──> (1) Dapr Sidecar
  Microservice (N) ──> (N) Pub/Sub Topic
  Microservice (N) ──> (N) Service Invocation
```

---

## 6. Validation Summary

**Kong Entities:**
- All names must be unique within their scope
- URLs must be valid and reachable
- Plugin configurations must match plugin schemas
- JWT credentials must have valid keys/secrets

**Dapr Entities:**
- Component names must be unique within namespace
- Subscriptions must reference existing components
- App IDs must not contain dots
- Resiliency policies must have valid durations

**LearnPyByAI Services:**
- All services must expose `/health` endpoint
- All services must listen on port 8000
- All services must have Dapr sidecar enabled
- All services must be registered in Kong routes

---

## Summary

This data model defines the configuration entities for Kong API Gateway and Dapr service mesh, including their attributes, relationships, and validation rules. The model supports the LearnPyByAI platform's 11 microservices with secure routing, rate limiting, service invocation, and pub/sub messaging.
