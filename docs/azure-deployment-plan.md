# Azure Deployment Plan

## Context

Currently deployed to Vercel (serverless). Goal is to migrate to personal Azure infrastructure for hands-on experience with Docker, Kubernetes, Terraform, and Azure services — without overengineering. Custom domain is a future enhancement; for now a static Azure public IP is used so `NEXT_PUBLIC_API_URL` is known before the first build. CI/CD via GitHub Actions on push to `main`.

**Ingress (revised Jun 2026):** the original plan used the community ingress-nginx controller, which was **retired in March 2026** — repositories are read-only with no further security fixes, following the CVSS 9.8 "IngressNightmare" RCE (CVE-2025-1974). It is replaced with **self-managed Istio (Helm) in ambient mode**, fronted by the **Gateway API** (`Gateway` + `HTTPRoute`). Chosen to learn Istio fundamentals and good practices hands-on, while staying light enough to run on a single small node.

**Future (not built yet):** TLS via cert-manager + Let's Encrypt and a custom domain when going public; separate `dev`/`prod` environments (parameterized Terraform, per-environment namespaces, then separate clusters/state).

---

## Architecture

```
GitHub Push → GitHub Actions
  ├── Build frontend image  (NEXT_PUBLIC_API_URL baked in as build arg)
  ├── Build backend image
  ├── Push both → Azure Container Registry (ACR)
  └── kubectl apply → AKS

AKS Cluster (1 node, Standard_B2as_v2)
  └── Istio ingress gateway — Envoy  (static public IP, provisioned by Terraform)
        │   (Gateway API: Gateway + HTTPRoute, gatewayClassName: istio)
        ├── /journals → backend pod (FastAPI, port 8000)
        ├── /contact  → backend pod
        └── /         → frontend pod (Next.js, port 3000)
        ↳ east-west traffic secured by Istio ambient mesh (per-node ztunnel, mTLS) — no sidecars

Secret resolution (runtime, no env var injection):
  backend pod (workload identity ServiceAccount)
    → Secrets Store CSI Driver
      → Azure Key Vault  (GITHUB_TOKEN, SMTP_*, CONTACT_RECIPIENT, ALLOWED_ORIGINS)
        ← User-Assigned Managed Identity (UAMI)
          ← Federated credential bound to the K8s ServiceAccount via AKS OIDC issuer
```

Secrets live in Azure Key Vault. The backend pod authenticates via workload identity (OIDC federation → UAMI → Key Vault RBAC). The CSI driver mounts secrets as a volume; the deployment reads them from there. No K8s Secret object, no secret values in GitHub Actions.

### Secrets Management — two tiers

**Tier 1 — Application runtime secrets** (consumed by running pods):
`GITHUB_TOKEN`, `SMTP_*`, `CONTACT_RECIPIENT`, `ALLOWED_ORIGINS`.
Strict handling only: Azure Key Vault → Secrets Store CSI Driver → workload
identity. No env var injection, no K8s Secret objects, never stored in CI/CD.

**Tier 2 — Operator & tooling credentials** (used to provision/deploy, never
by the app itself):
- Local Terraform → Azure: interactive `az login` session (no stored secret).
- CI/CD → Azure: service principal (`AZURE_CREDENTIALS`), later upgradable to
  GitHub OIDC federation.
- Terraform state backend access: via the operator's Azure RBAC.

These authenticate the *operator or pipeline*, not the workload, so they are
managed flexibly (az session, env vars, CI secrets). They deliberately do **not**
live in Key Vault — they are needed to *create* Key Vault in the first place
(bootstrapping), so storing them there would be circular.

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
  main.tf                 ← resource group, ACR, AKS, static public IP,
                             Key Vault, UAMI, federated credential, RBAC
  variables.tf
  outputs.tf              ← ingress IP, ACR login server, kube config,
                             Key Vault URI, UAMI client ID
k8s/
  namespace.yaml               ← haruka ns, labelled istio.io/dataplane-mode=ambient
  backend-serviceaccount.yaml  ← ServiceAccount annotated with UAMI client ID
  secret-provider-class.yaml   ← SecretProviderClass (Key Vault → CSI mount)
  backend-deployment.yaml      ← CSI volume mount; reads secrets from /mnt/secrets/
  backend-service.yaml         ← ClusterIP, port 8000
  frontend-deployment.yaml
  frontend-service.yaml        ← ClusterIP, port 3000
  gateway.yaml                 ← Gateway API Gateway (gatewayClassName: istio); static IP via azure-pip-name
  httproute.yaml               ← HTTPRoute(s): path-based routing to backend/frontend
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

| Resource | SKU / Config | Purpose |
|---|---|---|
| `azurerm_resource_group` | — | Container for all resources |
| `azurerm_container_registry` | Basic | Store Docker images |
| `azurerm_kubernetes_cluster` | 1× Standard_B2as_v2 | Run pods; `oidc_issuer_enabled = true`, `workload_identity_enabled = true`, `key_vault_secrets_provider` add-on enabled |
| `azurerm_public_ip` | Static | Fixed IP for nginx ingress |
| `azurerm_key_vault` | Standard | Store all backend secrets |
| `azurerm_user_assigned_identity` | — | UAMI for the backend pod |
| `azurerm_federated_identity_credential` | — | Binds the K8s ServiceAccount (`haruka/backend`) to the UAMI via AKS OIDC issuer |
| `azurerm_role_assignment` | `Key Vault Secrets User` | Grants UAMI read access to Key Vault secrets |

Key Vault secrets to populate manually after `terraform apply` (one-time):

```bash
az keyvault secret set --vault-name <kv-name> --name GITHUB-TOKEN     --value "..."
az keyvault secret set --vault-name <kv-name> --name SMTP-USER         --value "..."
az keyvault secret set --vault-name <kv-name> --name SMTP-PASSWORD     --value "..."
az keyvault secret set --vault-name <kv-name> --name SMTP-HOST         --value "smtp.gmail.com"
az keyvault secret set --vault-name <kv-name> --name SMTP-PORT         --value "587"
az keyvault secret set --vault-name <kv-name> --name CONTACT-RECIPIENT --value "..."
az keyvault secret set --vault-name <kv-name> --name ALLOWED-ORIGINS   --value "http://<ingress-ip>"
```

One-time Terraform setup:
```bash
az login
terraform -chdir=infra init
terraform -chdir=infra apply    # note ingress_ip, key_vault_uri, uami_client_id outputs
```

---

## Phase 4 — Istio ambient via Helm (one-time)

Self-managed Istio in **ambient mode** (sidecar-less). The ingress gateway is created later
via the Gateway API (Phase 5), which makes istiod auto-deploy the Envoy gateway.

```bash
# 1. Gateway API CRDs (AKS does not ship them)
kubectl get crd gateways.gateway.networking.k8s.io >/dev/null 2>&1 || \
  kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml

# 2. Istio Helm repo
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

# 3. Ambient components (control-plane requests tuned down for the single small node)
helm install istio-base istio/base -n istio-system --create-namespace
helm install istiod istio/istiod -n istio-system --set profile=ambient \
  --set pilot.resources.requests.cpu=100m --set pilot.resources.requests.memory=256Mi --wait
helm install istio-cni istio/cni -n istio-system --set profile=ambient
helm install ztunnel istio/ztunnel -n istio-system
```

Verify: `kubectl get pods -n istio-system` → `istiod`, `istio-cni` (DaemonSet), `ztunnel`
(DaemonSet) all Running. Install `istioctl` locally for inspection.

> **Caveat:** ambient traffic redirection runs over AKS's Azure CNI. If ztunnel does not capture
> workload traffic, check `istio-cni` logs — Azure CNI is supported but is the most likely snag.
> Confirm enrollment with `istioctl ztunnel-config workloads`.

---

## Phase 5 — Kubernetes Manifests (`k8s/`)

### `namespace.yaml`
The `haruka` namespace, labelled to enroll its pods into the Istio **ambient** mesh — no sidecar
injection, enrollment is purely a namespace label:
```yaml
metadata:
  labels:
    istio.io/dataplane-mode: ambient
```

### `backend-serviceaccount.yaml`
A dedicated `ServiceAccount` in the `haruka` namespace annotated with the UAMI client ID:
```yaml
annotations:
  azure.workload.identity/client-id: "<uami-client-id>"
```
The pod will carry the `azure.workload.identity/use: "true"` label so the mutating webhook injects the OIDC token projection automatically.

### `secret-provider-class.yaml`
A `SecretProviderClass` (kind: `SecretProviderClass`, provider: `azure`) that maps each Key Vault secret to a file under `/mnt/secrets/` inside the pod. Specifies the Key Vault name, tenant ID, and the list of secret objects (e.g. `GITHUB-TOKEN` → file `github-token`).

### Deployments
- **backend:** 1 replica; uses the `backend` ServiceAccount; mounts the CSI volume at `/mnt/secrets/`; app reads secret values from those files at startup (e.g. `open("/mnt/secrets/github-token").read()`); liveness/readiness probe `GET /health`. No `env` block for secrets.
- **frontend:** 1 replica, `NEXT_PUBLIC_API_URL` baked into image at build time.

### `gateway.yaml`
A Gateway API `Gateway` with `gatewayClassName: istio`; istiod auto-deploys an Envoy gateway
Deployment + a `LoadBalancer` Service for it. One HTTP listener on port 80 (TLS is a future phase).
Bind the pre-provisioned static IP to the generated Service via `spec.infrastructure.annotations`:
```yaml
annotations:
  service.beta.kubernetes.io/azure-pip-name: pip-haruka-ingress
```
References the existing public IP **by name** (the `loadBalancerIP` Service field is deprecated in
k8s ≥1.24). No `azure-load-balancer-resource-group` annotation needed — the IP already lives in the
node resource group.

### `httproute.yaml`
`HTTPRoute`(s) attached to the Gateway, replacing the old path-based Ingress rules:
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

Backend secrets (`GITHUB_TOKEN`, `SMTP_*`, `CONTACT_RECIPIENT`, `ALLOWED_ORIGINS`) are **not** stored in GitHub Actions. They live exclusively in Azure Key Vault and are fetched at pod startup via the CSI driver.

**Jobs:**
1. `build-push` — `docker build` + `docker push` for both images to ACR
2. `deploy` — `az aks get-credentials` → `kubectl apply -f k8s/`

---

## Implementation Order

1. Code changes (`next.config.ts`, health endpoint)
2. Dockerfiles + `.dockerignore` files
3. `docker-compose.yml` — test locally
4. Terraform — provision infrastructure (AKS with OIDC + workload identity + CSI add-on, Key Vault, UAMI, federated credential, RBAC); note `ingress_ip`, `key_vault_uri`, `uami_client_id` outputs
5. Helm — install Gateway API CRDs + Istio ambient (base, istiod, cni, ztunnel)
6. Populate Key Vault secrets manually via `az keyvault secret set` (one-time)
7. K8s manifests (`namespace.yaml` w/ ambient label, `backend-serviceaccount.yaml`, `secret-provider-class.yaml`, deployments, services, `gateway.yaml`, `httproute.yaml`)
8. GitHub Actions workflow

---

## Verification

```bash
# Local
docker-compose up
curl http://localhost:8000/health    # backend health
curl http://localhost:3000           # frontend loads

# Azure — Istio (after deploy)
kubectl get pods -n istio-system     # istiod, istio-cni, ztunnel Running
istioctl ztunnel-config workloads    # app pods enrolled in the ambient mesh
kubectl get gateway -n haruka        # PROGRAMMED=True
kubectl get svc -n haruka            # gateway Service EXTERNAL-IP == static IP (4.196.65.234)

# Azure — app via the Istio gateway
curl http://<ingress-ip>/health      # backend health via gateway
curl http://<ingress-ip>/journals    # journals API
curl http://<ingress-ip>             # Next.js frontend
kubectl get pods -n haruka           # all pods Running
kubectl logs deploy/frontend -n haruka
kubectl logs deploy/backend -n haruka
```
