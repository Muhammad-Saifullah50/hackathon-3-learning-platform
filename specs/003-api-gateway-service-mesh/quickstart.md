# Quickstart: API Gateway & Service Mesh Setup

**Feature**: 003-api-gateway-service-mesh
**Date**: 2026-03-15
**Status**: Complete

## Overview

This guide walks you through deploying Kong API Gateway and Dapr service mesh on Kubernetes (Minikube) for the LearnPyByAI platform.

**Estimated Time**: 30-45 minutes

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| Minikube | 1.32+ | `curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && sudo install minikube-linux-amd64 /usr/local/bin/minikube` |
| kubectl | 1.28+ | `curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && sudo install kubectl /usr/local/bin/kubectl` |
| Helm | 3.12+ | `curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \| bash` |
| Docker | 24.0+ | `sudo apt-get install docker.io` (or Docker Desktop) |

### Verify Installation

```bash
minikube version
kubectl version --client
helm version
docker --version
```

---

## Step 1: Start Minikube Cluster

### 1.1 Start Minikube

```bash
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=20g \
  --driver=docker \
  --kubernetes-version=v1.28.0
```

**Expected Output:**
```
😄  minikube v1.32.0 on Ubuntu 22.04
✨  Using the docker driver based on user configuration
👍  Starting control plane node minikube in cluster minikube
🚜  Pulling base image ...
🔥  Creating docker container (CPUs=4, Memory=8192MB) ...
🐳  Preparing Kubernetes v1.28.0 on Docker 24.0.7 ...
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
🌟  Enabled addons: storage-provisioner, default-storageclass
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

### 1.2 Enable Minikube Addons

```bash
minikube addons enable ingress
minikube addons enable metrics-server
```

### 1.3 Start Minikube Tunnel (Separate Terminal)

```bash
# Run this in a separate terminal and keep it running
minikube tunnel
```

**Note**: This enables LoadBalancer services to work locally.

### 1.4 Verify Cluster

```bash
kubectl cluster-info
kubectl get nodes
```

---

## Step 2: Deploy Redis (Shared Infrastructure)

### 2.1 Add Bitnami Helm Repository

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 2.2 Create Redis Values File

```bash
cat > redis-values.yaml <<EOF
architecture: standalone
auth:
  enabled: true
  password: "changeme"
master:
  persistence:
    enabled: true
    size: 1Gi
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi
metrics:
  enabled: true
  serviceMonitor:
    enabled: false
EOF
```

### 2.3 Deploy Redis

```bash
helm install redis bitnami/redis \
  -f redis-values.yaml \
  -n default \
  --create-namespace
```

### 2.4 Create Redis Secret

```bash
kubectl create secret generic redis-secret \
  --from-literal=password=changeme \
  -n default
```

### 2.5 Verify Redis Deployment

```bash
kubectl get pods -l app.kubernetes.io/name=redis
kubectl logs -l app.kubernetes.io/name=redis --tail=20

# Test Redis connection
kubectl run redis-client --rm -it --restart=Never \
  --image=redis:7.2 \
  -- redis-cli -h redis-master.default.svc.cluster.local -a changeme ping
```

**Expected Output**: `PONG`

---

## Step 3: Deploy Kong API Gateway

### 3.1 Add Kong Helm Repository

```bash
helm repo add kong https://charts.konghq.com
helm repo update
```

### 3.2 Create Kong Namespace

```bash
kubectl create namespace kong
```

### 3.3 Deploy PostgreSQL for Kong

```bash
helm install kong-postgresql bitnami/postgresql \
  --set auth.username=kong \
  --set auth.password=kong \
  --set auth.database=kong \
  --set primary.persistence.size=1Gi \
  -n kong
```

### 3.4 Create Kong Values File

```bash
cat > kong-values.yaml <<EOF
replicaCount: 2

image:
  repository: kong
  tag: "3.4"

env:
  database: postgres
  pg_host: kong-postgresql.kong.svc.cluster.local
  pg_port: 5432
  pg_user: kong
  pg_password: kong
  pg_database: kong
  admin_listen: "0.0.0.0:8001"
  proxy_listen: "0.0.0.0:8000"
  log_level: info

ingressController:
  enabled: true
  installCRDs: true

proxy:
  type: LoadBalancer
  http:
    enabled: true
    servicePort: 80
    containerPort: 8000
  tls:
    enabled: false

admin:
  enabled: true
  type: ClusterIP
  http:
    enabled: true
    servicePort: 8001
    containerPort: 8001

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70
EOF
```

### 3.5 Deploy Kong

```bash
helm install kong kong/kong \
  -f kong-values.yaml \
  -n kong \
  --wait
```

### 3.6 Run Kong Migrations

```bash
kubectl exec -it -n kong deployment/kong-kong -- kong migrations bootstrap
kubectl exec -it -n kong deployment/kong-kong -- kong migrations up
```

### 3.7 Verify Kong Deployment

```bash
kubectl get pods -n kong
kubectl get svc -n kong

# Test Kong Admin API
export KONG_ADMIN_URL=$(kubectl get svc -n kong kong-kong-admin -o jsonpath='{.spec.clusterIP}')
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -- curl http://$KONG_ADMIN_URL:8001/status
```

**Expected Output**: JSON with Kong status information

---

## Step 4: Deploy Dapr Service Mesh

### 4.1 Add Dapr Helm Repository

```bash
helm repo add dapr https://dapr.github.io/helm-charts/
helm repo update
```

### 4.2 Create Dapr Namespace

```bash
kubectl create namespace dapr-system
```

### 4.3 Deploy Dapr

```bash
helm install dapr dapr/dapr \
  --namespace dapr-system \
  --set global.logAsJson=true \
  --set global.ha.enabled=false \
  --wait
```

### 4.4 Verify Dapr Deployment

```bash
kubectl get pods -n dapr-system

# Expected pods:
# - dapr-operator
# - dapr-placement-server
# - dapr-sentry
# - dapr-sidecar-injector
```

### 4.5 Install Dapr CLI (Optional)

```bash
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
dapr --version
```

---

## Step 5: Apply Dapr Configuration

### 5.1 Apply Dapr Components

```bash
kubectl apply -f specs/003-api-gateway-service-mesh/contracts/dapr-components.yaml
kubectl apply -f specs/003-api-gateway-service-mesh/contracts/dapr-configuration.yaml
kubectl apply -f specs/003-api-gateway-service-mesh/contracts/dapr-resiliency.yaml
```

### 5.2 Apply Dapr Subscriptions

```bash
kubectl apply -f specs/003-api-gateway-service-mesh/contracts/dapr-subscriptions.yaml
```

### 5.3 Verify Dapr Components

```bash
kubectl get components -n default
kubectl get subscriptions -n default
kubectl get configurations -n default
```

---

## Step 6: Create JWT Public Key Secret

### 6.1 Generate RSA Key Pair (If Not Exists)

```bash
# This should already exist from F01 (auth-service)
# If not, generate it:
mkdir -p backend/auth-service/keys
ssh-keygen -t rsa -b 2048 -m PEM -f backend/auth-service/keys/jwt_key -N ""
openssl rsa -in backend/auth-service/keys/jwt_key -pubout -outform PEM -out backend/auth-service/keys/jwt_key.pub
```

### 6.2 Create Kubernetes Secret

```bash
kubectl create secret generic kong-jwt-public-key \
  --from-file=public_key.pem=backend/auth-service/keys/jwt_key.pub \
  -n kong
```

### 6.3 Verify Secret

```bash
kubectl get secret kong-jwt-public-key -n kong
kubectl describe secret kong-jwt-public-key -n kong
```

---

## Step 7: Apply Kong Configuration

### 7.1 Update Kong Configuration with Actual Public Key

```bash
# Extract public key
PUBLIC_KEY=$(cat backend/auth-service/keys/jwt_key.pub)

# Update kong-configuration.yaml with actual public key
# (Manual step: replace placeholder in contracts/kong-configuration.yaml)
```

### 7.2 Apply Kong Configuration Using deck

```bash
# Install deck CLI
curl -sL https://github.com/kong/deck/releases/download/v1.28.0/deck_1.28.0_linux_amd64.tar.gz -o deck.tar.gz
tar -xf deck.tar.gz -C /tmp
sudo cp /tmp/deck /usr/local/bin/

# Sync configuration
deck sync \
  --kong-addr http://$(kubectl get svc -n kong kong-kong-admin -o jsonpath='{.spec.clusterIP}'):8001 \
  --state specs/003-api-gateway-service-mesh/contracts/kong-configuration.yaml
```

### 7.3 Verify Kong Routes

```bash
# Port-forward Kong Admin API
kubectl port-forward -n kong svc/kong-kong-admin 8001:8001 &

# List services
curl http://localhost:8001/services | jq '.data[] | {name, url}'

# List routes
curl http://localhost:8001/routes | jq '.data[] | {name, paths}'

# List plugins
curl http://localhost:8001/plugins | jq '.data[] | {name, enabled}'
```

---

## Step 8: Deploy Sample Service for Testing

### 8.1 Create Test Service

```bash
cat > test-service.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-service
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-service
  template:
    metadata:
      labels:
        app: test-service
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "test-service"
        dapr.io/app-port: "8000"
        dapr.io/app-protocol: "http"
        dapr.io/config: "learnpybyai-config"
        dapr.io/log-level: "info"
    spec:
      containers:
      - name: test-service
        image: hashicorp/http-echo:latest
        args:
        - "-text=Hello from test-service"
        - "-listen=:8000"
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: test-service
  namespace: default
spec:
  selector:
    app: test-service
  ports:
  - port: 8000
    targetPort: 8000
EOF
```

### 8.2 Deploy Test Service

```bash
kubectl apply -f test-service.yaml
kubectl wait --for=condition=ready pod -l app=test-service --timeout=60s
```

### 8.3 Verify Dapr Sidecar Injection

```bash
kubectl get pods -l app=test-service
# Should show 2/2 containers (app + dapr sidecar)

kubectl logs -l app=test-service -c daprd --tail=20
```

---

## Step 9: Test the Setup

### 9.1 Test Kong Gateway (Without JWT)

```bash
# Get Kong proxy URL
export KONG_PROXY_URL=$(minikube service -n kong kong-kong-proxy --url | head -1)

# Test public endpoint (should work)
curl $KONG_PROXY_URL/api/auth/login
```

**Expected**: 404 (route exists but backend not deployed yet)

### 9.2 Test JWT Authentication

```bash
# Try accessing protected endpoint without token (should fail)
curl -i $KONG_PROXY_URL/api/users/me

# Expected: 401 Unauthorized
```

### 9.3 Test Dapr Service Invocation

```bash
# Port-forward to test-service Dapr sidecar
kubectl port-forward -l app=test-service 3500:3500 &

# Invoke test-service via Dapr
curl http://localhost:3500/v1.0/invoke/test-service/method/

# Expected: "Hello from test-service"
```

### 9.4 Test Dapr Pub/Sub

```bash
# Publish a test message
curl -X POST http://localhost:3500/v1.0/publish/learnpybyai-pubsub/struggle-alerts \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test-123",
    "error_type": "SyntaxError",
    "message": "Test struggle alert"
  }'

# Expected: 204 No Content (message published)

# Check Redis for the message
kubectl exec -it redis-master-0 -- redis-cli -a changeme XLEN "learnpybyai-pubsub-struggle-alerts"
```

### 9.5 Test Health Checks

```bash
# Check Kong health
curl http://localhost:8001/status

# Check Dapr health
kubectl port-forward -n dapr-system svc/dapr-api 3501:80 &
curl http://localhost:3501/v1.0/healthz
```

---

## Step 10: Monitoring and Troubleshooting

### 10.1 View Logs

```bash
# Kong logs
kubectl logs -n kong -l app.kubernetes.io/name=kong --tail=50

# Dapr logs
kubectl logs -n dapr-system -l app=dapr-operator --tail=50

# Service logs with Dapr sidecar
kubectl logs -l app=test-service -c test-service --tail=20
kubectl logs -l app=test-service -c daprd --tail=20
```

### 10.2 Check Resource Usage

```bash
kubectl top nodes
kubectl top pods -n kong
kubectl top pods -n dapr-system
kubectl top pods -n default
```

### 10.3 Common Issues

**Issue**: Kong pods not starting
```bash
# Check PostgreSQL connection
kubectl logs -n kong -l app.kubernetes.io/name=kong | grep postgres

# Verify PostgreSQL is running
kubectl get pods -n kong -l app.kubernetes.io/name=postgresql
```

**Issue**: Dapr sidecar not injected
```bash
# Verify Dapr sidecar injector is running
kubectl get pods -n dapr-system -l app=dapr-sidecar-injector

# Check pod annotations
kubectl get pod <pod-name> -o yaml | grep dapr.io
```

**Issue**: Redis connection failed
```bash
# Test Redis connectivity
kubectl run redis-test --rm -it --restart=Never \
  --image=redis:7.2 \
  -- redis-cli -h redis-master.default.svc.cluster.local -a changeme ping
```

**Issue**: Rate limiting not working
```bash
# Verify Redis is accessible from Kong
kubectl exec -n kong -it deployment/kong-kong -- \
  redis-cli -h redis-master.default.svc.cluster.local -a changeme ping
```

---

## Step 11: Cleanup (Optional)

### 11.1 Delete All Resources

```bash
# Delete test service
kubectl delete -f test-service.yaml

# Delete Dapr configuration
kubectl delete -f specs/003-api-gateway-service-mesh/contracts/dapr-subscriptions.yaml
kubectl delete -f specs/003-api-gateway-service-mesh/contracts/dapr-resiliency.yaml
kubectl delete -f specs/003-api-gateway-service-mesh/contracts/dapr-configuration.yaml
kubectl delete -f specs/003-api-gateway-service-mesh/contracts/dapr-components.yaml

# Uninstall Helm releases
helm uninstall dapr -n dapr-system
helm uninstall kong -n kong
helm uninstall kong-postgresql -n kong
helm uninstall redis -n default

# Delete namespaces
kubectl delete namespace kong
kubectl delete namespace dapr-system

# Stop Minikube
minikube stop
minikube delete
```

---

## Next Steps

1. **Deploy Backend Services**: Deploy the 11 LearnPyByAI microservices with Dapr sidecars
2. **Configure Authentication**: Integrate with auth-service JWT tokens
3. **Test End-to-End Flows**: Verify API requests through Kong → Dapr → Services
4. **Set Up Monitoring**: Deploy Prometheus and Grafana for observability
5. **Load Testing**: Test rate limiting and circuit breakers under load

---

## Reference

- [Kong Documentation](https://docs.konghq.com/)
- [Dapr Documentation](https://docs.dapr.io/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

---

## Support

For issues or questions:
- Check logs: `kubectl logs <pod-name> -c <container-name>`
- Describe resources: `kubectl describe <resource-type> <resource-name>`
- Check events: `kubectl get events --sort-by='.lastTimestamp'`
