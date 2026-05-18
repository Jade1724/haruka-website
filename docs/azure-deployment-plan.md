# Azure Deployment Plan

## Context

Currently deployed to Vercel (serverless). Goal is to migrate to personal Azure infrastructure for hands-on experience with Docker, Kubernetes, Terraform, and Azure services — without overengineering. Custom domain is a future enhancement; for now a static Azure public IP is used so `NEXT_PUBLIC_API_URL` is known before the first build. CI/CD via GitHub Actions on push to `main`.

---

## Architecture

```
GitHub Push → GitHub Actions
  ├── Build frontend image  (NEXT_PUBLIC_API_URL baked in as build arg)
  ├── Build backend image
  ├── Push both → Azure Container Registry (ACR)
  └── kubectl apply → AKS

AKS Cluster (1 node, Standard_B2s)
  └── nginx ingress  (static public IP, provisioned by Terraform)
        ├── /journals → backend pod (FastAPI, port 8000)
        ├── /contact  → backend pod
        └── /         → frontend pod (Next.js, port 3000)
```

Secrets (GitHub token, SMTP creds) live in a Kubernetes Secret, injected as env vars into the backend pod.

---

## Files to Create / Modify

### Modifications to existing files

| File | Change |
|---|---|
| `frontend/next.config.ts` | Add `output: 'standalone'` for smaller Docker image |
| `backend/app/main.py` | Include health router |
| `backend/app/api/health.py` | New: `GET /health` endpoint for liveness/readiness probes |

### New files

```
frontend/
  Dockerfile              ← multi-stage Node build
  .dockerignore
backend/
  Dockerfile              ← Python 3.13 + uvicorn
  .dockerignore
docker-compose.yml        ← local testing of both containers
infra/                    ← Terraform
  providers.tf
  main.tf                 ← resource group, ACR, AKS, static public IP
  variables.tf
  outputs.tf              ← ingress IP, ACR login server, kube config
k8s/
  namespace.yaml
  backend-secret.yaml     ← K8s Secret (GITHUB_TOKEN, SMTP_*, ALLOWED_ORIGINS)
  backend-deployment.yaml
  backend-service.yaml    ← ClusterIP, port 8000
  frontend-deployment.yaml
  frontend-service.yaml   ← ClusterIP, port 3000
  ingress.yaml            ← nginx path-based routing, static IP annotation
.github/
  workflows/
    deploy.yml            ← CI/CD: build → push to ACR → kubectl apply
```

---

## Phase 1 — Code Changes

### `frontend/next.config.ts`
Add `output: 'standalone'` so Next.js emits a self-contained build for Docker.

### `backend/app/api/health.py`
Simple health check endpoint used by K8s liveness and readiness probes.

### `backend/app/main.py`
Include the health router alongside existing journal and contact routers.

---

## Phase 2 — Dockerise

### `frontend/Dockerfile` (multi-stage)

- **Stage 1 (builder):** `node:20-alpine` — install deps, set `NEXT_PUBLIC_API_URL` build arg, run `next build`
- **Stage 2 (runner):** `node:20-alpine` — copy `.next/standalone`, `.next/static`, `public/` from builder; expose port 3000; `CMD ["node", "server.js"]`

### `backend/Dockerfile`

- Base: `python:3.13-slim`
- Install `uv`, then `uv pip install --system -r requirements.txt`
- Copy `app/`; expose port 8000; `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`

### `docker-compose.yml`

Local integration test for both services before touching Azure.

---

## Phase 3 — Terraform (`infra/`)

| Resource | SKU | Purpose |
|---|---|---|
| `azurerm_resource_group` | — | Container for all resources |
| `azurerm_container_registry` | Basic | Store Docker images |
| `azurerm_kubernetes_cluster` | 1× Standard_B2s | Run pods |
| `azurerm_public_ip` | Static | Fixed IP for nginx ingress |

One-time setup:
```bash
az login
terraform -chdir=infra init
terraform -chdir=infra apply    # note the ingress_ip output
```

---

## Phase 4 — nginx Ingress (Helm, one-time)

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --set controller.service.loadBalancerIP=<ingress-ip>
```

---

## Phase 5 — Kubernetes Manifests (`k8s/`)

### `backend-secret.yaml`
K8s Secret holding all sensitive backend env vars. Values are base64-encoded. Do not commit real values — apply manually or use sealed-secrets.

Variables: `GITHUB_TOKEN`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_HOST`, `SMTP_PORT`, `CONTACT_RECIPIENT`, `ALLOWED_ORIGINS` (set to `http://<ingress-ip>`)

### Deployments
- **backend:** 1 replica, env from Secret, liveness/readiness probe `GET /health`
- **frontend:** 1 replica, `NEXT_PUBLIC_API_URL` baked into image at build time

### `ingress.yaml`
Path-based routing:
- `/journals` → `backend-service:8000`
- `/contact` → `backend-service:8000`
- `/` → `frontend-service:3000`

---

## Phase 6 — GitHub Actions (`.github/workflows/deploy.yml`)

Trigger: push to `main`

**Required GitHub Actions secrets:**

| Secret | Value |
|---|---|
| `AZURE_CREDENTIALS` | Service principal JSON (`az ad sp create-for-rbac`) |
| `ACR_LOGIN_SERVER` | e.g. `harukaacr.azurecr.io` |
| `NEXT_PUBLIC_API_URL` | `http://<ingress-ip>` |
| `GH_TOKEN` | GitHub token for Obsidian repo |
| `SMTP_USER` | Gmail address |
| `SMTP_PASSWORD` | Gmail app password |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `CONTACT_RECIPIENT` | Destination email |

**Jobs:**
1. `build-push` — `docker build` + `docker push` for both images to ACR
2. `deploy` — `az aks get-credentials` → `kubectl apply -f k8s/`

---

## Implementation Order

1. Code changes (`next.config.ts`, health endpoint)
2. Dockerfiles + `.dockerignore` files
3. `docker-compose.yml` — test locally
4. Terraform — provision infrastructure, note static IP
5. Helm — install nginx ingress controller
6. K8s manifests
7. GitHub Actions workflow

---

## Verification

```bash
# Local
docker-compose up
curl http://localhost:8000/health    # backend health
curl http://localhost:3000           # frontend loads

# Azure (after deploy)
curl http://<ingress-ip>/health      # backend health via ingress
curl http://<ingress-ip>/journals    # journals API
curl http://<ingress-ip>             # Next.js frontend
kubectl get pods -n haruka           # all pods Running
kubectl logs deploy/frontend -n haruka
kubectl logs deploy/backend -n haruka
```
