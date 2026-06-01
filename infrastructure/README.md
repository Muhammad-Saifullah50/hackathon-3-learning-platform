# LearnPyByAI Infrastructure

## Overview

This directory contains the Kubernetes infrastructure configuration for the LearnPyByAI platform, including Kong API Gateway, Dapr service mesh, and all microservice deployments.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kong API Gateway                          │
│  - JWT Authentication                                        │
│  - Rate Limiting (10 req/min)                               │
│  - CORS Handling                                            │
│  - Request Transformation                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Dapr Service Mesh                           │
│  - Service Discovery                                         │
│  - Service Invocation (with retries & circuit breakers)     │
│  - Pub/Sub Messaging (Redis)                                │
│  - State Management                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend Microservices (11 services)             │
│  - auth-service, user-service, sandbox-service              │
│  - llm-service, teacher-service                             │
│  - 6 AI agents (triage, concepts, code-review, debug,       │
│    exercise, progress)                                       │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Minikube** 1.32+ (Kubernetes 1.28+)
- **kubectl** 1.28+
- **Helm** 3.12+
- **Docker** 24.0+
- **System Resources**: 4 CPUs, 8GB RAM, 20GB disk

## Quick Start

### 1. Deploy Complete Infrastructure

```bash
# Deploy everything (Minikube, Redis, Kong, Dapr, services)
./infrastructure/scripts/deploy-all.sh
```

This will:
1. Start Minikube cluster
2. Deploy Redis (shared infrastructure)
3. Deploy PostgreSQL for Kong
4. Deploy Kong API Gateway
5. Deploy Dapr service mesh
6. Apply Dapr configuration
7. Create JWT public key secret
8. Sync Kong configuration
9. Deploy all microservices
10. Deploy Dapr subscriptions
11. Run verification tests

### 2. Start Minikube Tunnel

In a separate terminal (keep it running):

```bash
minikube tunnel
```

### 3. Verify Deployment

```bash
# Test Kong Gateway
./infrastructure/scripts/test-gateway.sh

# Test Dapr Service Mesh
./infrastructure/scripts/test-service-mesh.sh
```

## Manual Deployment

If you prefer step-by-step deployment:

### Step 1: Setup Minikube

```bash
./infrastructure/scripts/setup-minikube.sh
```

### Step 2: Deploy Redis

```bash
./infrastructure/scripts/deploy-redis.sh
```

### Step 3: Deploy Kong

```bash
./infrastructure/scripts/deploy-kong-postgres.sh
./infrastructure/scripts/deploy-kong.sh
```

### Step 4: Deploy Dapr

```bash
./infrastructure/scripts/deploy-dapr.sh
kubectl apply -f infrastructure/kubernetes/dapr/components.yaml
kubectl apply -f infrastructure/kubernetes/dapr/configuration.yaml
kubectl apply -f infrastructure/kubernetes/dapr/resiliency-full.yaml
```

### Step 5: Configure Kong

```bash
./infrastructure/scripts/create-jwt-secret.sh
./infrastructure/scripts/update-kong-jwt-key.sh
./infrastructure/scripts/sync-kong-config.sh
```

### Step 6: Deploy Services

```bash
./infrastructure/scripts/deploy-services.sh
./infrastructure/scripts/deploy-dapr-subscriptions.sh
```

## Directory Structure

```
infrastructure/
├── kubernetes/           # Kubernetes manifests
│   ├── kong/            # Kong configuration
│   │   ├── values.yaml
│   │   ├── kong-configuration.yaml
│   │   ├── jwt-plugin.yaml
│   │   ├── cors-plugin.yaml
│   │   ├── rate-limit-plugin.yaml
│   │   └── health-checks.yaml
│   ├── dapr/            # Dapr configuration
│   │   ├── components.yaml
│   │   ├── configuration.yaml
│   │   ├── resiliency-full.yaml
│   │   └── subscriptions/
│   ├── redis/           # Redis configuration
│   │   └── values.yaml
│   └── services/        # Service manifests
│       ├── auth-service.yaml
│       ├── user-service.yaml
│       └── ... (11 services total)
├── scripts/             # Deployment scripts
│   ├── deploy-all.sh
│   ├── setup-minikube.sh
│   ├── deploy-redis.sh
│   ├── deploy-kong.sh
│   ├── deploy-dapr.sh
│   ├── deploy-services.sh
│   ├── test-gateway.sh
│   ├── test-service-mesh.sh
│   └── teardown.sh
└── docs/                # Documentation
    ├── kong-setup.md
    ├── dapr-setup.md
    ├── service-mesh-patterns.md
    └── troubleshooting.md
```

## Configuration

### Kong API Gateway

- **Replicas**: 2 (autoscaling 2-5)
- **Database**: PostgreSQL
- **Plugins**: JWT, Rate Limiting, CORS, Request Transformer
- **Rate Limits**: 10 requests/minute per user
- **Health Checks**: Active (5s interval) + Passive

### Dapr Service Mesh

- **Components**: Redis Pub/Sub, Redis State Store, Kubernetes Secrets
- **Resiliency**: Retries (3 attempts), Circuit Breakers (5 failures), Timeouts (5s-60s)
- **Pub/Sub Topics**: struggle-alerts, quiz-completed, code-submitted, mastery-updated
- **Tracing**: Enabled (100% sampling)

### Redis

- **Architecture**: Standalone
- **Persistence**: 1Gi
- **Resources**: 250m CPU / 256Mi RAM (requests), 500m CPU / 512Mi RAM (limits)
- **Usage**: Kong rate limiting, Dapr pub/sub, Dapr state store

## Accessing Services

### Kong Admin API

```bash
kubectl port-forward -n kong svc/kong-kong-admin 8001:8001
curl http://localhost:8001/status
```

### Kong Proxy

```bash
# Get proxy URL
minikube service -n kong kong-kong-proxy --url

# Or port-forward
kubectl port-forward -n kong svc/kong-kong-proxy 8000:8000
```

### Dapr Sidecar

```bash
# From within a pod
curl http://localhost:3500/v1.0/healthz

# Service invocation
curl http://localhost:3500/v1.0/invoke/concepts-agent/method/health

# Pub/sub
curl -X POST http://localhost:3500/v1.0/publish/learnpybyai-pubsub/struggle-alerts \
  -H "Content-Type: application/json" \
  -d '{"student_id": "123", "error": "SyntaxError"}'
```

## Testing

### Test Kong Gateway

```bash
./infrastructure/scripts/test-gateway.sh
```

Tests:
- Kong status and database connectivity
- Services, routes, and plugins configuration
- JWT authentication (401 on protected routes)
- CORS headers
- Rate limiting headers

### Test Dapr Service Mesh

```bash
./infrastructure/scripts/test-service-mesh.sh
```

Tests:
- Dapr system components
- Dapr components and configurations
- Sidecar injection
- Service invocation
- Pub/sub messaging
- State store operations
- Resiliency policies

### Test Service Invocation

```bash
./infrastructure/scripts/test-service-invocation.sh
```

### Test Pub/Sub

```bash
./infrastructure/scripts/test-pubsub.sh
```

### Test Rate Limiting

```bash
./infrastructure/scripts/test-rate-limiting.sh
```

## Monitoring

### View Logs

```bash
# Kong logs
kubectl logs -n kong -l app.kubernetes.io/name=kong --tail=100 -f

# Dapr system logs
kubectl logs -n dapr-system -l app=dapr-operator --tail=100 -f

# Service logs (with Dapr sidecar)
kubectl logs <pod-name> -c <service-name> --tail=100 -f
kubectl logs <pod-name> -c daprd --tail=100 -f

# Redis logs
kubectl logs -l app.kubernetes.io/name=redis --tail=100 -f
```

### Check Health

```bash
# Kong health
./infrastructure/scripts/verify-kong.sh

# Dapr health
./infrastructure/scripts/verify-dapr-health.sh

# Kong health checks
./infrastructure/scripts/verify-health-checks.sh
```

### Resource Usage

```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods --all-namespaces

# Specific namespace
kubectl top pods -n kong
kubectl top pods -n dapr-system
```

## Troubleshooting

See [troubleshooting.md](docs/troubleshooting.md) for detailed troubleshooting guide.

### Common Issues

**Kong pods not starting**:
```bash
kubectl logs -n kong -l app.kubernetes.io/name=kong --tail=50
kubectl exec -n kong deployment/kong-kong -- kong migrations up
```

**Dapr sidecar not injected**:
```bash
kubectl get pod <pod-name> -o yaml | grep dapr.io
kubectl get pods -n dapr-system -l app=dapr-sidecar-injector
```

**Redis connection failed**:
```bash
kubectl get pods -l app.kubernetes.io/name=redis
kubectl run redis-test --rm -it --restart=Never \
  --image=redis:7.2 \
  -- redis-cli -h redis-master.default.svc.cluster.local -a changeme ping
```

## Cleanup

### Delete All Infrastructure

```bash
./infrastructure/scripts/teardown.sh
```

This will delete:
- All microservices
- Dapr service mesh
- Kong API Gateway
- PostgreSQL (Kong database)
- Redis
- Persistent volume claims
- Optionally: Minikube cluster

## Documentation

- [Kong Setup Guide](docs/kong-setup.md)
- [Dapr Setup Guide](docs/dapr-setup.md)
- [Service Mesh Patterns](docs/service-mesh-patterns.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

## References

- [Kong Documentation](https://docs.konghq.com/)
- [Dapr Documentation](https://docs.dapr.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)

## Support

For issues or questions:
- Check logs: `kubectl logs <pod-name>`
- Describe resources: `kubectl describe <resource-type> <resource-name>`
- Check events: `kubectl get events --sort-by='.lastTimestamp'`
- Review troubleshooting guide: [docs/troubleshooting.md](docs/troubleshooting.md)
