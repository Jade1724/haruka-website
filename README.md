# Haruka's Portfolio Website

A modern portfolio website showcasing my projects, professional experience, education, and development journey through scraped dev journal entries.

## Features

### Project Showcase
- Display of personal projects with screenshots and detailed descriptions
- Interactive project galleries
- Links to live demos and source code repositories

### Professional Experience
- Job history and career timeline
- Education background and certifications
- Skills and technologies overview

### Dev Journal
- Automated scraping of development notes from a private Obsidian repository
- Chronological display of development insights and learnings
- Integration with personal knowledge management system

### Deployment
- **Currently hosted on Vercel** — frontend and backend API (serverless functions)
- Azure/AKS deployment configuration is also present in the repo (Terraform, Kubernetes manifests, Dockerfiles, GitHub Actions) but is not the active host
- Automated CI/CD pipelines

## Tech Stack

### Frontend
- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with shadcn/ui
- **Deployment**: Vercel

### Backend
- **Framework**: FastAPI (Python)
- **Database**: TBD (likely PostgreSQL or similar)
- **Scraping**: Custom scripts for Obsidian repository data extraction
- **Deployment**: Vercel serverless functions

## Project Structure

```
haruka-website/
├── frontend/          # Next.js application
│   ├── app/          # Next.js app directory
│   ├── components/   # Reusable UI components
│   ├── lib/          # Utility functions
│   └── public/       # Static assets
├── backend/          # FastAPI application
│   ├── app/          # FastAPI application code
│   │   ├── api/      # API routes
│   │   ├── core/     # Core functionality
│   │   ├── dao/      # Data access objects
│   │   └── services/ # Business logic services
│   └── pyproject.toml # Python dependencies
└── README.md         # This file
```

## Docker

The easiest way to run the full stack locally is **Docker Compose**, which starts the
backend and frontend together with hot reload. You can also build and run each image on its own.

### Docker Compose (local development)

Runs both services with the source bind-mounted for hot reload — edits under `backend/app/`
or `frontend/` are picked up automatically, no rebuild required.

**Prerequisites**
- Docker Desktop (includes Docker Compose v2)
- A `backend/.env` file with the backend secrets (see [Environment Variables](#environment-variables)).
  Values must be **unquoted** — `docker compose` does not strip surrounding quotes, so a quoted
  token would be sent with the quotes included.

```bash
# Start both services (builds images on first run)
docker compose up --build

# Subsequent runs (no rebuild)
docker compose up

# Stop and remove the containers
docker compose down

# ...and also remove the anonymous volumes (node_modules, .next cache)
docker compose down -v
```

Once it's up:

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Backend health check | http://localhost:8000/health |

### Individual images

#### Frontend

`NEXT_PUBLIC_API_URL` is baked in at **build time**, so set it via `--build-arg` (rebuild to change it):

```bash
# Build
docker build --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 -t frontend ./frontend

# Run
docker run -p 3000:3000 frontend
```

#### Backend

Secrets are provided at **runtime** via `--env-file`:

```bash
# Build
docker build -t backend ./backend

# Run
docker run -p 8000:8000 --env-file backend/.env backend
```

## Development Setup

### Prerequisites
- Node.js 22
- Python 3.13
- Git

### Frontend Setup
```bash
cd frontend
bun install
bun run dev
```

### Backend Setup
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

## Dev Journal Scraping

The dev journal feature scrapes content from a private Obsidian repository:

1. **Source**: Private GitHub repository containing Obsidian vault
2. **Scraping Process**: Custom Python scripts extract markdown files
3. **Data Processing**: Parse frontmatter and content for display
4. **API Integration**: RESTful endpoints serve journal data to frontend

### Scraping Requirements
- Access to private Obsidian repository
- Authentication tokens for GitHub API
- Scheduled updates or manual triggers

## Deployment

This repository keeps **two deployment setups side by side**. Vercel is the **active host**;
the Azure/AKS setup is fully configured and committed but currently dormant, kept as a
migration target and reference. The two are independent — Vercel ignores the Azure files, and
the Azure pipeline ignores the Vercel files.

| Target | Status | Key files |
|---|---|---|
| **Vercel** | **Active (live host)** | `frontend/vercel.json`, `backend/vercel.json`, `backend/api/index.py`, `backend/requirements.txt` |
| **Azure / AKS** | Configured, dormant | `infra/` (Terraform), `k8s/` (manifests), `frontend/Dockerfile`, `backend/Dockerfile`, `.github/workflows/deploy.yml` |

### Vercel Configuration (active)
- Frontend: Automatic deployment from `frontend/` directory
- Backend: Serverless functions in `backend/` directory
- Environment variables for API keys and database connections

#### Manual Production Deploy

Frontend and backend are separate Vercel projects (each has its own `.vercel/project.json`), so
deploy each from its own directory:

```bash
# Frontend
cd frontend
vercel --prod

# Backend
cd backend
vercel --prod
```

Requires the [Vercel CLI](https://vercel.com/docs/cli) installed and logged in (`vercel login`).

### Azure / AKS Configuration (dormant)
- Infrastructure provisioned via Terraform in `infra/`
- Workloads defined as Kubernetes manifests in `k8s/`
- Container images built from `frontend/Dockerfile` and `backend/Dockerfile`
- The `.github/workflows/deploy.yml` workflow builds images to ACR and rolls them out to AKS.
  It is **triggered only on the `azure-migration` branch**, so pushes to `main` do not deploy to Azure.
  To make Azure the active host, point that workflow's trigger at `main` and connect DNS to the
  AKS ingress.

### Environment Variables
```
# Frontend
NEXT_PUBLIC_API_URL=...

# Backend
GITHUB_TOKEN=...
DATABASE_URL=...
OBSIDIAN_REPO_URL=...
```

## Future Plans

- [ ] Implement project showcase with screenshots and descriptions including links
- [ ] Add a timeline for career progression
- [ ] Enhance dev journal with search and filtering
- [ ] Add analytics and visitor tracking
- [ ] Optimize for SEO and performance
