# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Haruka's portfolio website — project showcase, career timeline, and a dev journal scraped from a private Obsidian repository. Frontend is Next.js; backend is a FastAPI Python service, both deployed to Vercel.

## Commands

### Frontend (`cd frontend`)
```bash
bun install          # install dependencies
bun run dev          # start dev server
bun run build        # production build
bun run lint         # ESLint
```

### Backend (`cd backend`)
```bash
uv sync                                          # install dependencies
uv run uvicorn app.main:app --reload             # start dev server
```

## Architecture

### Frontend (`frontend/`)
- **Framework**: Next.js (App Router) — see warning below
- **Styling**: Tailwind CSS v4 with PostCSS; CSS variables use the `oklch` color space; dark mode via `.dark` class
- **Components**: `components/ui/` holds shadcn/ui components built with CVA (class-variance-authority) and Base UI React for unstyled primitives; Phosphor Icons
- **Data fetching**: TanStack React Query v5 (with Next.js experimental integration)
- **Utilities**: `lib/utils.ts` exports `cn()` — always use it for className merging (combines clsx + tailwind-merge)
- **TypeScript path alias**: `@/` maps to `frontend/` root

### Backend (`backend/`)
- **Framework**: FastAPI + Uvicorn, Python 3.13, managed with `uv`
- **Planned structure**: `app/api/` routes, `app/services/` business logic, `app/dao/` data access, `app/core/` config
- **Key feature**: scrapes markdown from a private Obsidian GitHub repo (requires `GITHUB_TOKEN`) and serves it as a REST API for the dev journal

### Environment Variables
```
# Frontend
NEXT_PUBLIC_API_URL=

# Backend
GITHUB_TOKEN=
DATABASE_URL=
OBSIDIAN_REPO_URL=
```

## Next.js Version Warning

**This project uses Next.js 16**, which has breaking changes from earlier versions. Before writing any Next.js-specific code, read the relevant guide in `frontend/node_modules/next/dist/docs/`. APIs, conventions, and file structure may differ from training data. Heed deprecation notices.
