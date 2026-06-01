# Service Mesh Patterns for LearnPyByAI

## Overview

This document describes common service mesh patterns used in the LearnPyByAI platform with Kong API Gateway and Dapr service mesh.

## Pattern 1: API Gateway Pattern

### Description
All external traffic flows through Kong API Gateway, which handles authentication, rate limiting, and routing to backend services.

### Flow
```
Client → Kong Gateway → Backend Service
```

### Implementation
- Kong validates JWT tokens
- Kong extracts user claims and forwards as headers
- Kong enforces rate limits per user
- Kong routes to appropriate backend service
- Backend service receives authenticated request with user context

### Example
```bash
# Client request
curl -H "Authorization: Bearer <jwt-token>" \
  https://api.learnpybyai.com/api/users/me

# Kong validates JWT and forwards to user-service with headers:
# X-User-Id: user-123
# X-User-Email: student@example.com
# X-User-Role: student
```

### Benefits
- Centralized authentication
- Consistent rate limiting
- Single entry point for all APIs
- Simplified client logic

## Pattern 2: Service-to-Service Invocation

### Description
Backend services communicate with each other through Dapr service invocation, which provides automatic retries, circuit breakers, and service discovery.

### Flow
```
Service A → Dapr Sidecar A → Dapr Sidecar B → Service B
```

### Implementation
- Service A calls `localhost:3500/v1.0/invoke/service-b/method/endpoint`
- Dapr sidecar A discovers service B via Kubernetes DNS
- Dapr sidecars communicate via gRPC (efficient)
- Dapr sidecar B forwards request to service B on port 8000
- Response flows back through sidecars

### Example
```python
# Triage agent calls concepts agent
from dapr.clients import DaprClient

with DaprClient() as client:
    response = client.invoke_method(
        app_id="concepts-agent",
        method_name="explain",
        data={"topic": "variables", "level": "beginner"}
    )
```

### Benefits
- Automatic service discovery
- Built-in retries and circuit breakers
- Distributed tracing
- No hardcoded service URLs

## Pattern 3: Pub/Sub Event Distribution

### Description
Services publish events to topics, and multiple subscribers can receive and process events asynchronously.

### Flow
```
Publisher → Dapr Sidecar → Redis Stream → Dapr Sidecar → Subscriber(s)
```

### Implementation
- Publisher publishes event to topic via Dapr
- Dapr writes event to Redis stream
- Dapr delivers event to all subscribers
- Subscribers process event via webhook endpoint
- Failed deliveries go to dead letter queue

### Example
```python
# Sandbox service publishes code-submitted event
from dapr.clients import DaprClient

with DaprClient() as client:
    client.publish_event(
        pubsub_name="learnpybyai-pubsub",
        topic_name="code-submitted",
        data={
            "student_id": "123",
            "code": "print('hello')",
            "timestamp": "2026-03-15T10:00:00Z"
        }
    )

# Both code-review-agent and progress-agent receive the event
@app.post("/webhooks/code-submitted")
async def handle_code_submitted(event: dict):
    # Process event
    return {"status": "ok"}
```

### Benefits
- Decoupled services
- Multiple subscribers per topic
- Guaranteed delivery (at-least-once)
- Dead letter queue for failed messages

## Pattern 4: Request-Response with Timeout

### Description
Service A calls service B and waits for response with a timeout to prevent hanging requests.

### Flow
```
Service A → Dapr (with timeout) → Service B
```

### Implementation
- Dapr applies timeout policy from resiliency configuration
- If service B doesn't respond within timeout, Dapr returns error
- Service A handles timeout error gracefully

### Example
```yaml
# Resiliency configuration
timeouts:
  general: 5s
  llm: 60s

targets:
  apps:
    llm-service:
      timeout: llm  # 60s timeout for LLM calls
    user-service:
      timeout: general  # 5s timeout for user calls
```

### Benefits
- Prevents cascading failures
- Predictable response times
- Resource protection

## Pattern 5: Circuit Breaker Pattern

### Description
When a service fails repeatedly, Dapr opens the circuit breaker to prevent further calls and allow the service to recover.

### Flow
```
Service A → Dapr (circuit breaker) → Service B (failing)
```

### States
1. **Closed**: Normal operation, requests flow through
2. **Open**: Service failing, requests immediately return error
3. **Half-Open**: Testing if service recovered, limited requests allowed

### Implementation
```yaml
# Resiliency configuration
circuitBreakers:
  general:
    maxRequests: 100
    interval: 30s
    timeout: 10s
    trip: consecutiveFailures >= 5

targets:
  apps:
    concepts-agent:
      circuitBreaker: general
```

### Example Scenario
1. Concepts agent fails 5 times in a row
2. Circuit breaker opens
3. Next 30 seconds: all calls to concepts agent fail immediately
4. After 30 seconds: circuit breaker enters half-open state
5. If next call succeeds: circuit breaker closes
6. If next call fails: circuit breaker opens again for 30 seconds

### Benefits
- Prevents cascading failures
- Allows failing services to recover
- Fast failure for clients

## Pattern 6: Retry with Exponential Backoff

### Description
When a service call fails, Dapr automatically retries with increasing delays between attempts.

### Flow
```
Service A → Dapr (retry) → Service B (temporary failure)
```

### Implementation
```yaml
# Resiliency configuration
retries:
  exponential:
    policy: exponential
    maxInterval: 5s
    maxRetries: 5
    initialInterval: 100ms
    randomization: 0.5

targets:
  apps:
    sandbox-service:
      retry: exponential
```

### Retry Schedule
- Attempt 1: Immediate
- Attempt 2: 100ms delay
- Attempt 3: 200ms delay
- Attempt 4: 400ms delay
- Attempt 5: 800ms delay
- Attempt 6: 1600ms delay (capped at 5s)

### Benefits
- Handles transient failures
- Reduces load on failing service
- Increases success rate

## Pattern 7: Dead Letter Queue

### Description
When pub/sub message delivery fails after retries, the message is moved to a dead letter queue for manual inspection.

### Flow
```
Publisher → Topic → Subscriber (fails) → Dead Letter Topic
```

### Implementation
```yaml
# Subscription configuration
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

### Handling Dead Letters
```bash
# Check dead letter queue
kubectl exec -n default redis-master-0 -- \
  redis-cli -a changeme XLEN "learnpybyai-pubsub-struggle-alerts-deadletter"

# Read dead letter messages
kubectl exec -n default redis-master-0 -- \
  redis-cli -a changeme XREAD COUNT 10 STREAMS "learnpybyai-pubsub-struggle-alerts-deadletter" 0
```

### Benefits
- No message loss
- Failed messages can be inspected and reprocessed
- Prevents blocking of message queue

## Pattern 8: Health Check Pattern

### Description
Kong actively monitors backend service health and stops routing to unhealthy instances.

### Flow
```
Kong → /health endpoint → Service (every 5s)
```

### Implementation
```yaml
# Kong health check configuration
healthchecks:
  active:
    healthy:
      interval: 5
      successes: 3
    unhealthy:
      interval: 5
      http_failures: 3
    http_path: /health
    type: http
    timeout: 1
```

### Service Health Endpoint
```python
@app.get("/health")
async def health_check():
    # Check dependencies (database, Redis, etc.)
    return {"status": "healthy"}
```

### Benefits
- Automatic failover to healthy instances
- Prevents routing to failing services
- Improves overall reliability

## Pattern 9: Request Correlation

### Description
Each request gets a unique correlation ID that flows through all services for distributed tracing.

### Flow
```
Client → Kong (adds X-Request-ID) → Service A → Service B → Service C
```

### Implementation
Kong automatically adds correlation headers:
- `X-Request-ID`: Unique request identifier
- `X-Correlation-ID`: Correlation identifier

Services should propagate these headers in downstream calls.

### Example
```python
# Service A receives request with X-Request-ID
request_id = request.headers.get("X-Request-ID")

# Service A calls Service B with same request ID
response = client.invoke_method(
    app_id="service-b",
    method_name="process",
    data={"data": "value"},
    metadata=(("X-Request-ID", request_id),)
)
```

### Benefits
- End-to-end request tracing
- Easier debugging
- Performance analysis

## Pattern 10: Rate Limiting per User

### Description
Kong enforces rate limits per authenticated user to prevent abuse and ensure fair usage.

### Flow
```
User → Kong (checks rate limit) → Service
```

### Implementation
```yaml
# Rate limiting plugin
rate-limiting:
  minute: 10
  hour: 600
  policy: redis
  identifier: consumer
```

### Rate Limit Headers
Kong returns these headers:
- `X-RateLimit-Limit`: Total allowed requests
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time until limit resets

### Benefits
- Prevents API abuse
- Fair resource allocation
- Protects backend services

## Best Practices

### 1. Always Use Service Invocation for Sync Calls
Don't hardcode service URLs. Use Dapr service invocation for automatic discovery and resiliency.

### 2. Use Pub/Sub for Async Communication
When immediate response is not needed, use pub/sub to decouple services.

### 3. Implement Health Endpoints
All services should expose `/health` endpoint for Kong health checks.

### 4. Handle Timeouts Gracefully
Always handle timeout errors and provide fallback responses.

### 5. Monitor Circuit Breaker State
Alert when circuit breakers open frequently - indicates service issues.

### 6. Process Dead Letter Messages
Regularly check and reprocess messages in dead letter queues.

### 7. Use Correlation IDs
Always propagate correlation IDs for distributed tracing.

### 8. Test Resiliency Policies
Simulate failures to verify retry and circuit breaker behavior.

### 9. Set Appropriate Timeouts
LLM calls need longer timeouts (60s) than database calls (5s).

### 10. Monitor Rate Limits
Alert when users hit rate limits frequently - may need adjustment.

## References

- [Dapr Service Invocation](https://docs.dapr.io/developing-applications/building-blocks/service-invocation/)
- [Dapr Pub/Sub](https://docs.dapr.io/developing-applications/building-blocks/pubsub/)
- [Dapr Resiliency](https://docs.dapr.io/operations/resiliency/)
- [Kong Rate Limiting](https://docs.konghq.com/hub/kong-inc/rate-limiting/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
