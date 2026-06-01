# Tasks: API Gateway & Service Mesh Setup

**Input**: Design documents from `/specs/003-api-gateway-service-mesh/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are excluded. Focus is on infrastructure deployment and configuration.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize Minikube cluster and deploy shared infrastructure components (Redis, PostgreSQL)

- [X] T001 Create infrastructure directory structure: infrastructure/kubernetes/{kong,dapr,redis,services}, infrastructure/scripts/, infrastructure/docs/
- [X] T002 Create Minikube setup script in infrastructure/scripts/setup-minikube.sh with 4 CPUs, 8GB RAM, 20GB disk
- [X] T003 [P] Create Redis Helm values file in infrastructure/kubernetes/redis/values.yaml with standalone architecture, auth enabled, 1Gi persistence
- [X] T004 [P] Create Redis deployment script in infrastructure/scripts/deploy-redis.sh using Bitnami Helm chart
- [X] T005 Create Kong PostgreSQL deployment script in infrastructure/scripts/deploy-kong-postgres.sh with auth credentials and 1Gi persistence

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Deploy Kong API Gateway and Dapr service mesh - MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create Kong Helm values file in infrastructure/kubernetes/kong/values.yaml with 2 replicas, PostgreSQL config, admin/proxy listeners, autoscaling
- [X] T007 Create Kong deployment script in infrastructure/scripts/deploy-kong.sh using Kong Helm chart with migrations
- [X] T008 [P] Create Dapr configuration file in infrastructure/kubernetes/dapr/config.yaml with tracing and metrics settings
- [X] T009 [P] Create Dapr resiliency configuration in infrastructure/kubernetes/dapr/resiliency.yaml with retry policies (3 attempts, exponential backoff) and circuit breakers (5 consecutive failures)
- [X] T010 Create Dapr deployment script in infrastructure/scripts/deploy-dapr.sh using Dapr Helm chart in dapr-system namespace
- [X] T011 Copy Dapr components configuration from specs/003-api-gateway-service-mesh/contracts/dapr-components.yaml to infrastructure/kubernetes/dapr/components.yaml
- [X] T012 Copy Dapr configuration from specs/003-api-gateway-service-mesh/contracts/dapr-configuration.yaml to infrastructure/kubernetes/dapr/configuration.yaml
- [X] T013 Copy Dapr resiliency from specs/003-api-gateway-service-mesh/contracts/dapr-resiliency.yaml to infrastructure/kubernetes/dapr/resiliency.yaml
- [X] T014 Create script to generate JWT public key secret in infrastructure/scripts/create-jwt-secret.sh reading from backend/auth-service/keys/jwt_key.pub
- [X] T015 Create master deployment script in infrastructure/scripts/deploy-all.sh that orchestrates setup-minikube.sh, deploy-redis.sh, deploy-kong-postgres.sh, deploy-kong.sh, deploy-dapr.sh, create-jwt-secret.sh

**Checkpoint**: Foundation ready - Kong and Dapr deployed and healthy, user story implementation can now begin

---

## Phase 3: User Story 1 - Secure API Access with JWT Authentication (Priority: P1) 🎯 MVP

**Goal**: Enable authenticated API requests through Kong gateway with JWT validation for all backend services

**Independent Test**: Send authenticated and unauthenticated requests to any backend service through Kong and verify JWT validation works correctly

### Implementation for User Story 1

- [X] T016 [P] [US1] Create Kong JWT plugin configuration in infrastructure/kubernetes/kong/jwt-plugin.yaml with key_claim_name="iss", claims_to_verify=["exp"], header_names=["Authorization"]
- [X] T017 [P] [US1] Create Kong Request Transformer plugin configuration in infrastructure/kubernetes/kong/request-transformer-plugin.yaml to extract JWT claims (X-User-Id, X-User-Email, X-User-Role, X-Session-Id)
- [X] T018 [P] [US1] Create Kong CORS plugin configuration in infrastructure/kubernetes/kong/cors-plugin.yaml with allowed_origins=[localhost:3000, learnpybyai.com], credentials=true
- [X] T019 [US1] Copy Kong declarative configuration from specs/003-api-gateway-service-mesh/contracts/kong-configuration.yaml to infrastructure/kubernetes/kong/kong-configuration.yaml
- [X] T020 [US1] Update kong-configuration.yaml to replace JWT public key placeholder with actual key from Kubernetes secret
- [X] T021 [US1] Create Kong configuration sync script in infrastructure/scripts/sync-kong-config.sh using deck CLI to apply kong-configuration.yaml
- [X] T022 [US1] Create Kong verification script in infrastructure/scripts/verify-kong.sh to test /status endpoint, list services, routes, and plugins
- [X] T023 [US1] Update deploy-all.sh to include sync-kong-config.sh and verify-kong.sh steps

**Checkpoint**: Kong gateway validates JWT tokens and routes authenticated requests to backend services

---

## Phase 4: User Story 2 - Service-to-Service Communication via Dapr (Priority: P1)

**Goal**: Enable microservices to communicate through Dapr with automatic service discovery, retries, and observability

**Independent Test**: Deploy two services with Dapr sidecars and verify they can invoke each other using Dapr service invocation

### Implementation for User Story 2

- [X] T024 [P] [US2] Create base service manifest template in infrastructure/kubernetes/services/service-template.yaml with Dapr annotations (dapr.io/enabled, dapr.io/app-id, dapr.io/app-port, dapr.io/app-protocol, dapr.io/config)
- [X] T025 [P] [US2] Create auth-service manifest in infrastructure/kubernetes/services/auth-service.yaml with app-id="auth-service", app-port="8000", Dapr enabled
- [X] T026 [P] [US2] Create user-service manifest in infrastructure/kubernetes/services/user-service.yaml with app-id="user-service", app-port="8000", Dapr enabled
- [X] T027 [P] [US2] Create sandbox-service manifest in infrastructure/kubernetes/services/sandbox-service.yaml with app-id="sandbox-service", app-port="8000", Dapr enabled
- [X] T028 [P] [US2] Create llm-service manifest in infrastructure/kubernetes/services/llm-service.yaml with app-id="llm-service", app-port="8000", Dapr enabled
- [X] T029 [P] [US2] Create triage-agent manifest in infrastructure/kubernetes/services/triage-agent.yaml with app-id="triage-agent", app-port="8000", Dapr enabled
- [X] T030 [P] [US2] Create concepts-agent manifest in infrastructure/kubernetes/services/concepts-agent.yaml with app-id="concepts-agent", app-port="8000", Dapr enabled
- [X] T031 [P] [US2] Create code-review-agent manifest in infrastructure/kubernetes/services/code-review-agent.yaml with app-id="code-review-agent", app-port="8000", Dapr enabled
- [X] T032 [P] [US2] Create debug-agent manifest in infrastructure/kubernetes/services/debug-agent.yaml with app-id="debug-agent", app-port="8000", Dapr enabled
- [X] T033 [P] [US2] Create exercise-agent manifest in infrastructure/kubernetes/services/exercise-agent.yaml with app-id="exercise-agent", app-port="8000", Dapr enabled
- [X] T034 [P] [US2] Create progress-agent manifest in infrastructure/kubernetes/services/progress-agent.yaml with app-id="progress-agent", app-port="8000", Dapr enabled
- [X] T035 [P] [US2] Create teacher-service manifest in infrastructure/kubernetes/services/teacher-service.yaml with app-id="teacher-service", app-port="8000", Dapr enabled
- [X] T036 [US2] Create services deployment script in infrastructure/scripts/deploy-services.sh to apply all service manifests
- [X] T037 [US2] Create Dapr service invocation test script in infrastructure/scripts/test-service-invocation.sh to verify triage-agent can call concepts-agent
- [X] T038 [US2] Update deploy-all.sh to include deploy-services.sh and test-service-invocation.sh steps

**Checkpoint**: All microservices deployed with Dapr sidecars and can invoke each other via Dapr

---

## Phase 5: User Story 5 - Pub/Sub Event Distribution (Priority: P1)

**Goal**: Enable asynchronous event distribution between services using Dapr pub/sub with Redis

**Independent Test**: Publish events to Dapr topics and verify subscribers receive them within 2 seconds

### Implementation for User Story 5

- [X] T039 [P] [US5] Copy Dapr subscriptions from specs/003-api-gateway-service-mesh/contracts/dapr-subscriptions.yaml to infrastructure/kubernetes/dapr/subscriptions.yaml
- [X] T040 [P] [US5] Create struggle-alerts subscription manifest in infrastructure/kubernetes/dapr/subscriptions/struggle-alerts.yaml for teacher-service with route=/webhooks/struggle-alert, deadLetterTopic=struggle-alerts-deadletter
- [X] T041 [P] [US5] Create quiz-completed subscription manifest in infrastructure/kubernetes/dapr/subscriptions/quiz-completed.yaml for progress-agent with route=/webhooks/quiz-completed, deadLetterTopic=quiz-completed-deadletter
- [X] T042 [P] [US5] Create code-submitted subscription manifest in infrastructure/kubernetes/dapr/subscriptions/code-submitted.yaml for code-review-agent and progress-agent with routes=/webhooks/code-submitted, deadLetterTopic=code-submitted-deadletter
- [X] T043 [P] [US5] Create mastery-updated subscription manifest in infrastructure/kubernetes/dapr/subscriptions/mastery-updated.yaml for user-service with route=/webhooks/mastery-updated, deadLetterTopic=mastery-updated-deadletter
- [X] T044 [US5] Create Dapr subscriptions deployment script in infrastructure/scripts/deploy-dapr-subscriptions.sh to apply all subscription manifests
- [X] T045 [US5] Create pub/sub test script in infrastructure/scripts/test-pubsub.sh to publish test message to struggle-alerts topic and verify delivery
- [X] T046 [US5] Update deploy-all.sh to include deploy-dapr-subscriptions.sh and test-pubsub.sh steps

**Checkpoint**: Pub/sub topics configured and services can publish/subscribe to events asynchronously

---

## Phase 6: User Story 3 - Rate Limiting for API Protection (Priority: P2)

**Goal**: Enforce rate limiting to prevent API abuse and ensure fair resource usage

**Independent Test**: Send multiple rapid requests from a single user and verify rate limits are enforced with 429 responses

### Implementation for User Story 3

- [X] T047 [US3] Create Kong rate limiting plugin configuration in infrastructure/kubernetes/kong/rate-limit-plugin.yaml with minute=10, policy=redis, redis_host=redis-master.default.svc.cluster.local, identifier=consumer
- [X] T048 [US3] Update kong-configuration.yaml to apply rate-limiting plugin to all protected routes
- [X] T049 [US3] Create rate limiting test script in infrastructure/scripts/test-rate-limiting.sh to send 11 requests in 1 minute and verify 11th request returns 429
- [X] T050 [US3] Update sync-kong-config.sh to apply updated kong-configuration.yaml with rate limiting
- [X] T051 [US3] Update deploy-all.sh to include test-rate-limiting.sh step

**Checkpoint**: Rate limiting enforced at 10 requests per minute per authenticated user

---

## Phase 7: User Story 4 - Health Monitoring and Service Discovery (Priority: P2)

**Goal**: Enable health checks for all services to detect failures and ensure system reliability

**Independent Test**: Deploy services with health endpoints and verify Kong/Dapr can detect unhealthy services

### Implementation for User Story 4

- [X] T052 [P] [US4] Create Kong health check configuration in infrastructure/kubernetes/kong/health-checks.yaml with active checks (5s interval, 3 successes, 3 failures) and passive checks, http_path=/health
- [X] T053 [US4] Update kong-configuration.yaml to add health check configuration to all service upstreams
- [X] T054 [US4] Create health check verification script in infrastructure/scripts/verify-health-checks.sh to query Kong health status for all services
- [X] T055 [US4] Create Dapr health check script in infrastructure/scripts/verify-dapr-health.sh to query Dapr sidecar health endpoints for all services
- [X] T056 [US4] Update deploy-all.sh to include verify-health-checks.sh and verify-dapr-health.sh steps

**Checkpoint**: Health checks configured and Kong stops routing to unhealthy service instances

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, testing, and operational improvements

- [X] T057 [P] Create Kong setup documentation in infrastructure/docs/kong-setup.md with deployment steps, configuration details, troubleshooting
- [X] T058 [P] Create Dapr setup documentation in infrastructure/docs/dapr-setup.md with deployment steps, component configuration, troubleshooting
- [X] T059 [P] Create service mesh patterns documentation in infrastructure/docs/service-mesh-patterns.md with service invocation examples, pub/sub patterns, resiliency configuration
- [X] T060 [P] Create troubleshooting guide in infrastructure/docs/troubleshooting.md with common issues (Kong not starting, Dapr sidecar not injected, Redis connection failed, rate limiting not working)
- [X] T061 Create comprehensive test script in infrastructure/scripts/test-gateway.sh to test Kong routing, JWT validation, rate limiting, CORS
- [X] T062 Create comprehensive test script in infrastructure/scripts/test-service-mesh.sh to test Dapr service invocation, pub/sub, health checks
- [X] T063 Create teardown script in infrastructure/scripts/teardown.sh to delete all resources (services, Dapr config, Kong, Redis, Minikube)
- [X] T064 Validate quickstart.md by following all steps from specs/003-api-gateway-service-mesh/quickstart.md and verify successful deployment
- [X] T065 Update CLAUDE.md to add Kong 3.x, Dapr 1.13+, Kubernetes 1.28+, Helm 3.x, Redis 7.x to Active Technologies section
- [X] T066 Create README.md in infrastructure/ directory with overview, prerequisites, quick start, architecture diagram, troubleshooting links

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - JWT authentication and routing
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) - Service-to-service communication
- **User Story 5 (Phase 5)**: Depends on Foundational (Phase 2) and User Story 2 (Phase 4) - Pub/sub requires services deployed
- **User Story 3 (Phase 6)**: Depends on User Story 1 (Phase 3) - Rate limiting requires Kong routing configured
- **User Story 4 (Phase 7)**: Depends on User Story 1 (Phase 3) and User Story 2 (Phase 4) - Health checks require services and routing configured
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P1)**: Depends on User Story 2 (services must be deployed first)
- **User Story 3 (P2)**: Depends on User Story 1 (routing must be configured first)
- **User Story 4 (P2)**: Depends on User Story 1 and User Story 2 (routing and services must be deployed first)

### Within Each User Story

- **User Story 1**: Plugin configs [P] → Kong config → Sync script → Verification
- **User Story 2**: Service manifests [P] → Deployment script → Test script
- **User Story 5**: Subscription manifests [P] → Deployment script → Test script
- **User Story 3**: Rate limit config → Update Kong config → Test script
- **User Story 4**: Health check configs [P] → Update Kong config → Verification scripts

### Parallel Opportunities

- **Phase 1**: T003 (Redis values) and T004 (Redis script) can run in parallel
- **Phase 2**: T008 (Dapr config) and T009 (Dapr resiliency) can run in parallel
- **User Story 1**: T016 (JWT plugin), T017 (Request Transformer), T018 (CORS plugin) can run in parallel
- **User Story 2**: T025-T035 (all service manifests) can run in parallel
- **User Story 5**: T040-T043 (all subscription manifests) can run in parallel
- **Phase 8**: T057-T060 (all documentation) can run in parallel

---

## Parallel Example: User Story 2 (Service Manifests)

```bash
# Launch all service manifest creation tasks together:
Task: "Create auth-service manifest in infrastructure/kubernetes/services/auth-service.yaml"
Task: "Create user-service manifest in infrastructure/kubernetes/services/user-service.yaml"
Task: "Create sandbox-service manifest in infrastructure/kubernetes/services/sandbox-service.yaml"
Task: "Create llm-service manifest in infrastructure/kubernetes/services/llm-service.yaml"
Task: "Create triage-agent manifest in infrastructure/kubernetes/services/triage-agent.yaml"
Task: "Create concepts-agent manifest in infrastructure/kubernetes/services/concepts-agent.yaml"
Task: "Create code-review-agent manifest in infrastructure/kubernetes/services/code-review-agent.yaml"
Task: "Create debug-agent manifest in infrastructure/kubernetes/services/debug-agent.yaml"
Task: "Create exercise-agent manifest in infrastructure/kubernetes/services/exercise-agent.yaml"
Task: "Create progress-agent manifest in infrastructure/kubernetes/services/progress-agent.yaml"
Task: "Create teacher-service manifest in infrastructure/kubernetes/services/teacher-service.yaml"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (Minikube + Redis + PostgreSQL)
2. Complete Phase 2: Foundational (Kong + Dapr deployment)
3. Complete Phase 3: User Story 1 (JWT authentication and routing)
4. Complete Phase 4: User Story 2 (Service-to-service communication)
5. **STOP and VALIDATE**: Test authenticated API requests and service invocation
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Infrastructure ready
2. Add User Story 1 → Test JWT auth independently → Deploy/Demo (Secure gateway!)
3. Add User Story 2 → Test service invocation independently → Deploy/Demo (Service mesh!)
4. Add User Story 5 → Test pub/sub independently → Deploy/Demo (Event-driven!)
5. Add User Story 3 → Test rate limiting independently → Deploy/Demo (API protection!)
6. Add User Story 4 → Test health checks independently → Deploy/Demo (Monitoring!)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (JWT authentication)
   - Developer B: User Story 2 (Service manifests)
3. After User Stories 1 & 2:
   - Developer A: User Story 3 (Rate limiting)
   - Developer B: User Story 5 (Pub/sub)
   - Developer C: User Story 4 (Health checks)
4. Stories complete and integrate independently

---

## Summary

**Total Tasks**: 66 tasks across 8 phases

**Task Count by User Story**:
- Setup (Phase 1): 5 tasks
- Foundational (Phase 2): 10 tasks (CRITICAL - blocks all stories)
- User Story 1 (P1): 8 tasks - JWT authentication and routing
- User Story 2 (P1): 15 tasks - Service-to-service communication
- User Story 5 (P1): 8 tasks - Pub/sub event distribution
- User Story 3 (P2): 5 tasks - Rate limiting
- User Story 4 (P2): 5 tasks - Health monitoring
- Polish (Phase 8): 10 tasks - Documentation and testing

**Parallel Opportunities Identified**:
- 3 tasks in Phase 1 can run in parallel
- 2 tasks in Phase 2 can run in parallel
- 3 tasks in User Story 1 can run in parallel
- 11 tasks in User Story 2 can run in parallel (service manifests)
- 4 tasks in User Story 5 can run in parallel (subscription manifests)
- 4 tasks in Phase 8 can run in parallel (documentation)

**Independent Test Criteria**:
- User Story 1: Send authenticated/unauthenticated requests and verify JWT validation
- User Story 2: Deploy two services and verify Dapr service invocation works
- User Story 5: Publish events and verify subscribers receive them within 2 seconds
- User Story 3: Send 11 rapid requests and verify 11th returns 429
- User Story 4: Query health endpoints and verify Kong detects unhealthy services

**Suggested MVP Scope**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (User Story 1) + Phase 4 (User Story 2)

**Format Validation**: ✅ All tasks follow the checklist format with checkbox, ID, optional [P] marker, [Story] label (for user story phases), and file paths

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are NOT included as they were not explicitly requested in the specification
- Focus is on infrastructure deployment, configuration, and operational scripts
