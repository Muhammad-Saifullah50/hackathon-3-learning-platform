# Troubleshooting Guide for LearnPyByAI Infrastructure

## Overview

This guide provides solutions to common issues with Kong API Gateway, Dapr service mesh, and related infrastructure components.

## Quick Diagnostics

### Check Overall System Health

```bash
# Check all pods
kubectl get pods --all-namespaces

# Check Kong
kubectl get pods -n kong
kubectl logs -n kong -l app.kubernetes.io/name=kong --tail=20

# Check Dapr
kubectl get pods -n dapr-system
kubectl logs -n dapr-system -l app=dapr-operator --tail=20

# Check Redis
kubectl get pods -l app.kubernetes.io/name=redis
kubectl logs -l app.kubernetes.io/name=redis --tail=20

# Check services
kubectl get pods -n default
```

### Check Resource Usage

```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods --all-namespaces
```

## Kong Issues

### Issue: Kong pods not starting

**Symptoms**:
- Pods stuck in `Pending`, `CrashLoopBackOff`, or `Error` state
- Kong Admin API not accessible

**Diagnosis**:
```bash
# Check pod status
kubectl get pods -n kong

# Check pod events
kubectl describe pod -n kong <pod-name>

# Check logs
kubectl logs -n kong <pod-name> --tail=50
```

**Common Causes & Solutions**:

1. **PostgreSQL not ready**
   ```bash
   # Check PostgreSQL
   kubectl get pods -n kong -l app.kubernetes.io/name=postgresql

   # If not running, redeploy
   ./infrastructure/scripts/deploy-kong-postgres.sh
   ```

2. **Database migrations not run**
   ```bash
   # Run migrations
   kubectl exec -n kong deployment/kong-kong -- kong migrations bootstrap
   kubectl exec -n kong deployment/kong-kong -- kong migrations up
   ```

3. **Insufficient resources**
   ```bash
   # Check resource limits
   kubectl describe pod -n kong <pod-name> | grep -A 5 "Limits"

   # Increase Minikube resources
   minikube stop
   minikube start --cpus=4 --memory=8192
   ```

### Issue: Kong Admin API returns 404

**Symptoms**:
- `curl http://localhost:8001/status` returns 404
- Cannot sync Kong configuration

**Diagnosis**:
```bash
# Check Kong service
kubectl get svc -n kong kong-kong-admin

# Check port-forward
kubectl port-forward -n kong svc/kong-kong-admin 8001:8001
```

**Solutions**:
1. Verify Admin API is enabled in values.yaml
2. Check if port-forward is active
3. Restart Kong pods

### Issue: JWT validation failing

**Symptoms**:
- 401 Unauthorized on protected routes
- "No credentials found" error

**Diagnosis**:
```bash
# Check JWT secret
kubectl get secret kong-jwt-public-key -n kong

# Check JWT consumer
curl http://localhost:8001/consumers/learnpybyai-auth/jwt | jq
```

**Solutions**:

1. **JWT secret not created**
   ```bash
   ./infrastructure/scripts/create-jwt-secret.sh
   ```

2. **JWT public key not in Kong config**
   ```bash
   ./infrastructure/scripts/update-kong-jwt-key.sh
   ./infrastructure/scripts/sync-kong-config.sh
   ```

3. **Invalid token format**
   - Verify token has `Bearer ` prefix
   - Check token expiration
   - Verify token signature with public key

### Issue: Rate limiting not working

**Symptoms**:
- No 429 responses after exceeding limits
- Rate limit headers not present

**Diagnosis**:
```bash
# Check rate limiting plugin
curl http://localhost:8001/plugins | jq '.data[] | select(.name=="rate-limiting")'

# Test Redis connectivity
kubectl exec -n kong deployment/kong-kong -- \
  redis-cli -h redis-master.default.svc.cluster.local -a changeme ping
```

**Solutions**:

1. **Redis not accessible**
   ```bash
   # Check Redis
   kubectl get pods -l app.kubernetes.io/name=redis

   # Test connectivity
   kubectl run redis-test --rm -it --restart=Never \
     --image=redis:7.2 \
     -- redis-cli -h redis-master.default.svc.cluster.local -a changeme ping
   ```

2. **Plugin not applied**
   ```bash
   # Verify plugin in Kong config
   grep -A 10 "rate-limiting" infrastructure/kubernetes/kong/kong-configuration.yaml

   # Re-sync configuration
   ./infrastructure/scripts/sync-kong-config.sh
   ```

## Dapr Issues

### Issue: Dapr sidecar not injected

**Symptoms**:
- Pod shows 1/1 containers instead of 2/2
- Service invocation fails with "app not found"

**Diagnosis**:
```bash
# Check pod containers
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[*].name}'

# Check annotations
kubectl get pod <pod-name> -o yaml | grep dapr.io
```

**Solutions**:

1. **Missing annotations**
   - Add Dapr annotations to pod spec
   - Redeploy service

2. **Dapr sidecar injector not running**
   ```bash
   # Check injector
   kubectl get pods -n dapr-system -l app=dapr-sidecar-injector

   # Restart if needed
   kubectl rollout restart deployment -n dapr-system dapr-sidecar-injector
   ```

3. **Namespace not labeled**
   ```bash
   # Label namespace (if using namespace-scoped injection)
   kubectl label namespace default dapr.io/enabled=true
   ```

### Issue: Service invocation failing

**Symptoms**:
- 500 errors when calling services
- "app not found" errors
- Timeout errors

**Diagnosis**:
```bash
# Check target service
kubectl get pods -l app=<target-service>

# Check Dapr sidecar logs
kubectl logs <pod-name> -c daprd --tail=50

# Test Dapr health
kubectl exec <pod-name> -c daprd -- curl http://localhost:3500/v1.0/healthz
```

**Solutions**:

1. **Target service not running**
   ```bash
   # Deploy services
   ./infrastructure/scripts/deploy-services.sh
   ```

2. **Circuit breaker open**
   ```bash
   # Check logs for circuit breaker messages
   kubectl logs <pod-name> -c daprd | grep "circuit breaker"

   # Wait for circuit breaker to close (30s)
   # Or restart pod to reset state
   kubectl delete pod <pod-name>
   ```

3. **Network policy blocking traffic**
   ```bash
   # Check network policies
   kubectl get networkpolicies

   # Temporarily disable to test
   kubectl delete networkpolicy <policy-name>
   ```

### Issue: Pub/sub messages not delivered

**Symptoms**:
- Messages published but not received
- Subscriber webhook not called

**Diagnosis**:
```bash
# Check subscriptions
kubectl get subscriptions -n default

# Check Redis streams
kubectl exec -n default redis-master-0 -- \
  redis-cli -a changeme KEYS "learnpybyai-pubsub-*"

# Check subscriber logs
kubectl logs <subscriber-pod> -c daprd --tail=50 | grep "pubsub"
```

**Solutions**:

1. **Subscription not created**
   ```bash
   # Deploy subscriptions
   ./infrastructure/scripts/deploy-dapr-subscriptions.sh
   ```

2. **Webhook endpoint not implemented**
   - Verify subscriber has webhook endpoint
   - Check endpoint returns 200 OK

3. **Messages in dead letter queue**
   ```bash
   # Check dead letter queue
   kubectl exec -n default redis-master-0 -- \
     redis-cli -a changeme XLEN "learnpybyai-pubsub-<topic>-deadletter"

   # Read dead letter messages
   kubectl exec -n default redis-master-0 -- \
     redis-cli -a changeme XREAD COUNT 10 STREAMS "learnpybyai-pubsub-<topic>-deadletter" 0
   ```

### Issue: Dapr components not loading

**Symptoms**:
- "component not found" errors
- Pub/sub or state store not working

**Diagnosis**:
```bash
# Check components
kubectl get components -n default

# Check component details
kubectl describe component learnpybyai-pubsub
```

**Solutions**:

1. **Components not applied**
   ```bash
   kubectl apply -f infrastructure/kubernetes/dapr/components.yaml
   ```

2. **Redis not accessible**
   ```bash
   # Test Redis
   kubectl exec <pod-name> -c daprd -- \
     redis-cli -h redis-master.default.svc.cluster.local -a changeme ping
   ```

3. **Secret not found**
   ```bash
   # Check Redis secret
   kubectl get secret redis-secret -n default

   # Recreate if missing
   kubectl create secret generic redis-secret \
     --from-literal=password=changeme -n default
   ```

## Redis Issues

### Issue: Redis not starting

**Symptoms**:
- Redis pod in `CrashLoopBackOff`
- Connection refused errors

**Diagnosis**:
```bash
# Check Redis pod
kubectl get pods -l app.kubernetes.io/name=redis

# Check logs
kubectl logs -l app.kubernetes.io/name=redis --tail=50

# Check events
kubectl describe pod redis-master-0
```

**Solutions**:

1. **Insufficient resources**
   ```bash
   # Check resource usage
   kubectl top pod redis-master-0

   # Increase resources in values.yaml
   ```

2. **Persistent volume issues**
   ```bash
   # Check PVC
   kubectl get pvc

   # Delete and recreate if needed
   kubectl delete pvc data-redis-master-0
   helm uninstall redis
   ./infrastructure/scripts/deploy-redis.sh
   ```

### Issue: Redis connection timeout

**Symptoms**:
- "connection timeout" errors from Kong or Dapr
- Slow response times

**Diagnosis**:
```bash
# Test Redis connectivity
kubectl run redis-test --rm -it --restart=Never \
  --image=redis:7.2 \
  -- redis-cli -h redis-master.default.svc.cluster.local -a changeme ping

# Check Redis performance
kubectl exec redis-master-0 -- redis-cli -a changeme INFO stats
```

**Solutions**:

1. **Redis overloaded**
   ```bash
   # Check memory usage
   kubectl exec redis-master-0 -- redis-cli -a changeme INFO memory

   # Increase Redis resources
   # Edit infrastructure/kubernetes/redis/values.yaml
   helm upgrade redis bitnami/redis -f infrastructure/kubernetes/redis/values.yaml
   ```

2. **Network latency**
   ```bash
   # Check network policies
   kubectl get networkpolicies

   # Test latency
   kubectl exec <pod-name> -- ping redis-master.default.svc.cluster.local
   ```

## Minikube Issues

### Issue: Minikube not starting

**Symptoms**:
- `minikube start` fails
- "insufficient resources" error

**Solutions**:

1. **Insufficient system resources**
   ```bash
   # Check available resources
   free -h
   df -h

   # Reduce Minikube resources
   minikube start --cpus=2 --memory=4096
   ```

2. **Docker not running**
   ```bash
   # Start Docker
   sudo systemctl start docker

   # Verify Docker
   docker ps
   ```

3. **Existing cluster conflicts**
   ```bash
   # Delete existing cluster
   minikube delete

   # Start fresh
   ./infrastructure/scripts/setup-minikube.sh
   ```

### Issue: LoadBalancer services pending

**Symptoms**:
- Kong proxy service stuck in `Pending`
- External IP shows `<pending>`

**Diagnosis**:
```bash
# Check services
kubectl get svc -n kong
```

**Solutions**:

1. **Minikube tunnel not running**
   ```bash
   # Start tunnel in separate terminal
   minikube tunnel
   ```

2. **Use NodePort instead**
   ```bash
   # Get service URL
   minikube service -n kong kong-kong-proxy --url
   ```

## General Debugging Tips

### 1. Check Logs

Always start with logs:
```bash
# Pod logs
kubectl logs <pod-name> --tail=100

# Previous pod logs (if crashed)
kubectl logs <pod-name> --previous

# Specific container logs
kubectl logs <pod-name> -c <container-name>

# Follow logs
kubectl logs <pod-name> -f
```

### 2. Describe Resources

Get detailed information:
```bash
# Pod details
kubectl describe pod <pod-name>

# Service details
kubectl describe svc <service-name>

# Events
kubectl get events --sort-by='.lastTimestamp'
```

### 3. Execute Commands in Pods

Debug from inside pods:
```bash
# Shell access
kubectl exec -it <pod-name> -- /bin/sh

# Run specific command
kubectl exec <pod-name> -- curl http://localhost:8000/health

# Access Dapr sidecar
kubectl exec <pod-name> -c daprd -- curl http://localhost:3500/v1.0/healthz
```

### 4. Port Forwarding

Access services locally:
```bash
# Forward service port
kubectl port-forward svc/<service-name> <local-port>:<service-port>

# Forward pod port
kubectl port-forward pod/<pod-name> <local-port>:<pod-port>
```

### 5. Check Resource Quotas

Verify resource limits:
```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods

# Resource quotas
kubectl describe resourcequota
```

## Getting Help

### Collect Diagnostic Information

```bash
# Create diagnostic bundle
mkdir -p diagnostics

# Collect pod info
kubectl get pods --all-namespaces -o yaml > diagnostics/pods.yaml

# Collect logs
kubectl logs -n kong -l app.kubernetes.io/name=kong --tail=500 > diagnostics/kong.log
kubectl logs -n dapr-system -l app=dapr-operator --tail=500 > diagnostics/dapr.log

# Collect events
kubectl get events --all-namespaces --sort-by='.lastTimestamp' > diagnostics/events.txt

# Collect configurations
kubectl get configmaps --all-namespaces -o yaml > diagnostics/configmaps.yaml
kubectl get secrets --all-namespaces -o yaml > diagnostics/secrets.yaml

# Create archive
tar -czf diagnostics.tar.gz diagnostics/
```

### Useful Commands Reference

```bash
# Restart deployment
kubectl rollout restart deployment <deployment-name>

# Scale deployment
kubectl scale deployment <deployment-name> --replicas=3

# Delete pod (will be recreated)
kubectl delete pod <pod-name>

# Force delete stuck pod
kubectl delete pod <pod-name> --force --grace-period=0

# Get pod YAML
kubectl get pod <pod-name> -o yaml

# Edit resource
kubectl edit deployment <deployment-name>

# Apply configuration
kubectl apply -f <file.yaml>

# Delete resource
kubectl delete -f <file.yaml>
```

## References

- [Kubernetes Debugging](https://kubernetes.io/docs/tasks/debug/)
- [Kong Troubleshooting](https://docs.konghq.com/gateway/latest/troubleshoot/)
- [Dapr Troubleshooting](https://docs.dapr.io/operations/troubleshooting/)
- [Minikube Troubleshooting](https://minikube.sigs.k8s.io/docs/handbook/troubleshooting/)
