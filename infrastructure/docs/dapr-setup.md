# Dapr Setup Documentation

## Overview

This document describes the Dapr service mesh setup for the LearnPyByAI platform, including deployment, configuration, and troubleshooting.

## Architecture

Dapr provides service mesh capabilities for LearnPyByAI microservices:
- Service-to-service invocation with automatic retries
- Pub/sub messaging with Redis
- State management
- Resiliency policies (circuit breakers, timeouts)
- Distributed tracing
- Service discovery

## Deployment

### Prerequisites

- Minikube cluster running
- Helm 3.x installed
- kubectl configured
- Redis deployed (shared with Kong)

### Installation Steps

1. **Deploy Dapr**:
   ```bash
   ./infrastructure/scripts/deploy-dapr.sh
   ```

2. **Apply Dapr components**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/dapr/components.yaml
   ```

3. **Apply Dapr configuration**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/dapr/configuration.yaml
   ```

4. **Apply Dapr resiliency policies**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/dapr/resiliency-full.yaml
   ```

5. **Verify Dapr deployment**:
   ```bash
   kubectl get pods -n dapr-system
   kubectl get components -n default
   kubectl get configurations -n default
   ```

## Configuration

### Dapr Components

Location: `infrastructure/kubernetes/dapr/components.yaml`

#### Redis Pub/Sub Component
- **Name**: `learnpybyai-pubsub`
- **Type**: `pubsub.redis`
- **Host**: `redis-master.default.svc.cluster.local:6379`
- **Features**:
  - Consumer ID: `{podName}` (unique per pod)
  - Processing timeout: 60s
  - Redelivery interval: 30s
  - Queue depth: 100
  - Concurrency: 10

#### Redis State Store Component
- **Name**: `learnpybyai-statestore`
- **Type**: `state.redis`
- **Host**: `redis-master.default.svc.cluster.local:6379`
- **Features**:
  - Actor state store: enabled
  - TTL: 3600s (1 hour)

#### Kubernetes Secret Store
- **Name**: `kubernetes`
- **Type**: `secretstores.kubernetes`
- **Purpose**: Access Kubernetes secrets from Dapr

### Dapr Configuration

Location: `infrastructure/kubernetes/dapr/configuration.yaml`

#### Tracing
- **Sampling rate**: 100% (all requests traced)
- **Backend**: Zipkin (optional)
- **Endpoint**: `http://zipkin.default.svc.cluster.local:9411/api/v2/spans`

#### Metrics
- **Enabled**: Yes
- **Increased cardinality**: Yes
- **Path matching**: `/api/*`

#### Access Control
- **Default action**: Allow
- **Trust domain**: public
- **Policies**:
  - Only `triage-agent` can call other agents
  - `llm-service` can only be called by agents

#### Features
- Service Invocation: Enabled
- Pub/Sub: Enabled
- State Store: Enabled
- Secrets: Enabled
- Bindings: Disabled
- Actors: Disabled

### Resiliency Policies

Location: `infrastructure/kubernetes/dapr/resiliency-full.yaml`

#### Timeout Policies
- **general**: 5s
- **fast**: 2s
- **slow**: 30s
- **llm**: 60s

#### Retry Policies
- **general**: 3 retries, constant 100ms delay
- **exponential**: 5 retries, exponential backoff (100ms-5s)
- **llm-retry**: 3 retries, exponential backoff (500ms-10s)

#### Circuit Breaker Policies
- **general**: 5 consecutive failures, 30s interval
- **strict**: 3 consecutive failures, 60s interval
- **llm-breaker**: 3 consecutive failures, 60s interval

#### Service-Specific Policies
- **auth-service**: general timeout, general retry, general circuit breaker
- **user-service**: general timeout, general retry, general circuit breaker
- **sandbox-service**: slow timeout, exponential retry, strict circuit breaker
- **llm-service**: llm timeout, llm-retry, llm-breaker
- **triage-agent**: fast timeout, general retry, general circuit breaker
- **All other agents**: general timeout, general retry, general circuit breaker

### Subscriptions

Location: `infrastructure/kubernetes/dapr/subscriptions.yaml`

#### Struggle Alerts
- **Topic**: `struggle-alerts`
- **Subscriber**: `teacher-service`
- **Route**: `/webhooks/struggle-alert`
- **Dead letter topic**: `struggle-alerts-deadletter`

#### Quiz Completed
- **Topic**: `quiz-completed`
- **Subscriber**: `progress-agent`
- **Route**: `/webhooks/quiz-completed`
- **Dead letter topic**: `quiz-completed-deadletter`

#### Code Submitted
- **Topic**: `code-submitted`
- **Subscribers**: `code-review-agent`, `progress-agent`
- **Route**: `/webhooks/code-submitted`
- **Dead letter topic**: `code-submitted-deadletter`

#### Mastery Updated
- **Topic**: `mastery-updated`
- **Subscriber**: `user-service`
- **Route**: `/webhooks/mastery-updated`
- **Dead letter topic**: `mastery-updated-deadletter`

## Sidecar Injection

### Pod Annotations

To enable Dapr sidecar for a service, add these annotations:

```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "service-name"
  dapr.io/app-port: "8000"
  dapr.io/app-protocol: "http"
  dapr.io/config: "learnpybyai-config"
  dapr.io/log-level: "info"
  dapr.io/enable-metrics: "true"
  dapr.io/metrics-port: "9090"
```

### Sidecar Ports

- **3500**: Dapr HTTP API
- **50001**: Dapr gRPC API
- **9090**: Metrics endpoint

## Service Invocation

### Invoking a Service

From within a pod with Dapr sidecar:

```bash
# HTTP invocation
curl http://localhost:3500/v1.0/invoke/concepts-agent/method/explain \
  -H "Content-Type: application/json" \
  -d '{"topic": "variables", "level": "beginner"}'

# With Dapr Python SDK
from dapr.clients import DaprClient

with DaprClient() as client:
    response = client.invoke_method(
        app_id="concepts-agent",
        method_name="explain",
        data={"topic": "variables", "level": "beginner"}
    )
```

### Service Discovery

Dapr automatically discovers services by `app-id`. No need for hardcoded IPs or DNS names.

## Pub/Sub Messaging

### Publishing a Message

```bash
# HTTP publish
curl -X POST http://localhost:3500/v1.0/publish/learnpybyai-pubsub/struggle-alerts \
  -H "Content-Type: application/json" \
  -d '{"student_id": "123", "error_type": "SyntaxError"}'

# With Dapr Python SDK
from dapr.clients import DaprClient

with DaprClient() as client:
    client.publish_event(
        pubsub_name="learnpybyai-pubsub",
        topic_name="struggle-alerts",
        data={"student_id": "123", "error_type": "SyntaxError"}
    )
```

### Subscribing to Messages

Implement a webhook endpoint in your service:

```python
@app.post("/webhooks/struggle-alert")
async def handle_struggle_alert(event: dict):
    # Process the event
    return {"status": "ok"}
```

Dapr will automatically deliver messages to this endpoint based on the subscription configuration.

## Troubleshooting

### Dapr sidecar not injected

**Symptom**: Pod shows 1/1 containers instead of 2/2

**Possible causes**:
1. Missing Dapr annotations
2. Dapr sidecar injector not running
3. Namespace not labeled

**Solutions**:
```bash
# Check Dapr sidecar injector
kubectl get pods -n dapr-system -l app=dapr-sidecar-injector

# Verify pod annotations
kubectl get pod <pod-name> -o yaml | grep dapr.io

# Check Dapr operator logs
kubectl logs -n dapr-system -l app=dapr-operator --tail=50
```

### Service invocation failing

**Symptom**: 500 errors when invoking services

**Possible causes**:
1. Target service not running
2. Target service doesn't have Dapr sidecar
3. Network policy blocking traffic
4. Circuit breaker open

**Solutions**:
```bash
# Check target service
kubectl get pods -l app=<target-service>

# Check Dapr sidecar logs
kubectl logs <pod-name> -c daprd --tail=50

# Test Dapr health
kubectl exec <pod-name> -c daprd -- curl http://localhost:3500/v1.0/healthz

# Check Dapr metadata
kubectl exec <pod-name> -c daprd -- curl http://localhost:3500/v1.0/metadata
```

### Pub/sub messages not delivered

**Symptom**: Messages published but not received by subscribers

**Possible causes**:
1. Subscription not created
2. Redis not accessible
3. Webhook endpoint not implemented
4. Message in dead letter queue

**Solutions**:
```bash
# Check subscriptions
kubectl get subscriptions -n default

# Test Redis connectivity
kubectl exec <pod-name> -c daprd -- redis-cli -h redis-master.default.svc.cluster.local -a changeme ping

# Check Redis streams
kubectl exec -n default redis-master-0 -- redis-cli -a changeme KEYS "learnpybyai-pubsub-*"

# Check dead letter topics
kubectl exec -n default redis-master-0 -- redis-cli -a changeme XLEN "learnpybyai-pubsub-struggle-alerts-deadletter"

# Check Dapr logs for delivery errors
kubectl logs <subscriber-pod> -c daprd --tail=50 | grep "struggle-alerts"
```

### Circuit breaker open

**Symptom**: Service invocation returns 500 with "circuit breaker is open"

**Possible causes**:
1. Target service failing repeatedly
2. Circuit breaker threshold reached (5 consecutive failures)

**Solutions**:
```bash
# Check target service health
kubectl logs <target-pod> --tail=50

# Wait for circuit breaker to close (30s interval)
# Or restart the calling pod to reset circuit breaker state

# Adjust circuit breaker settings in resiliency.yaml if needed
```

### Redis connection failed

**Symptom**: Dapr logs show "failed to connect to Redis"

**Possible causes**:
1. Redis not running
2. Wrong Redis host/port
3. Wrong Redis password
4. Network policy blocking traffic

**Solutions**:
```bash
# Check Redis
kubectl get pods -l app.kubernetes.io/name=redis

# Test Redis from Dapr pod
kubectl exec <pod-name> -c daprd -- redis-cli -h redis-master.default.svc.cluster.local -a changeme ping

# Verify Redis secret
kubectl get secret redis-secret -n default

# Check Dapr component configuration
kubectl get component learnpybyai-pubsub -o yaml
```

## Monitoring

### Key Metrics

Monitor these Dapr metrics (exposed on port 9090):
- Service invocation latency
- Service invocation errors
- Pub/sub message delivery rate
- Pub/sub message delivery errors
- Circuit breaker state

### Logs

View Dapr sidecar logs:
```bash
kubectl logs <pod-name> -c daprd --tail=100 -f
```

View Dapr system logs:
```bash
kubectl logs -n dapr-system -l app=dapr-operator --tail=100 -f
```

### Health Status

Check Dapr health:
```bash
kubectl exec <pod-name> -c daprd -- curl http://localhost:3500/v1.0/healthz
```

## References

- [Dapr Documentation](https://docs.dapr.io/)
- [Dapr on Kubernetes](https://docs.dapr.io/operations/hosting/kubernetes/)
- [Dapr Service Invocation](https://docs.dapr.io/developing-applications/building-blocks/service-invocation/)
- [Dapr Pub/Sub](https://docs.dapr.io/developing-applications/building-blocks/pubsub/)
- [Dapr Resiliency](https://docs.dapr.io/operations/resiliency/)
