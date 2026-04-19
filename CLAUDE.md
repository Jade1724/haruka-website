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
- **Structure**: `app/api/` routes, `app/services/` business logic, `app/dao/` data access, `app/core/` config
- **Adapters**: `app/core/adapters/` holds thin wrappers around external services (e.g. SMTP, third-party APIs). Each module adapts one external dependency; services import from here rather than calling external SDKs directly
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

## Contents

### Projects

#### Haruka Website

This portfolio website built with Next.js, Tailwind CSS, and FastAPI, hosted on Vercel. Features a project showcase, career timeline, and a dev journal scraped from my private Obsidian repository.

GitHub link: https://github.com/Jade1724/haruka-website 

#### Fruit Maturity Clearance Project 

Maturity clearance system used for real fruit growers, packhouse, and labs users to digitally track fruit quality and maturity. Built with Next.js, .NET, SQL server on Azure. Handled operations, monitoring, and incident resolutions.  

#### B2B Sales Recommendation System

AI Sales recommendation system using RAG to suggest best sales actions based on client's public data and in-house revenue data, and third party data. Built using Next.js, FastAPI, Snowflake database, and Azure OpenAI.  

#### Spectral Detect

Invasive plant detection and location tracker full-stack web app built with Vue.js, Spring Boot, MariaDB, hosted on AWS. University's Master project to help the Department of Conservation automatically detect euphorbia paralias from UAV imagery.

#### Apple Thinning

Agriculture simulation VR game built for training farmers thinning apple fruitlet. Built with Godot game engine to run on Oculus Quest 2. Built as part of University of Canterbury's computor vision lab research.  

GitHub link: https://github.com/uc-vision/apple-thinning


### Experiences

#### Work

##### AI Engineer at Spark New Zealnd
2023 - Current

Developed and maintained applications and systems integrated with AI. Worked on AI-decisioning marketting system and B2B sales recommendation system. 

##### Software Developer Intern at Umajin

2022 - 2023

Worked two projects, one being a React dashboard app for automotive oil company client, another one being an WebXR application using THREE.js with Jest testing. 

#### Education

##### University of Canterbury, Professional Master of Computer Science

Project based master's degree building a full stack web application to automate invasive plants detection. Worked as a research assistant and built apple thinning agricultural VR simmulated training game. 

##### University of Canterbury, Bachelor of Science

Double major in Computer Science and Physics