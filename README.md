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
- Frontend deployed on Vercel
- Backend API deployed on Vercel (serverless functions)
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

### Vercel Configuration
- Frontend: Automatic deployment from `frontend/` directory
- Backend: Serverless functions in `backend/` directory
- Environment variables for API keys and database connections

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
