# Story 1.1: TurboRepo Monorepo Scaffold

Status: ready-for-dev

## Story

As a **development team member**,
I want **a properly scaffolded TurboRepo monorepo with Next.js frontend and Python FastAPI backend**,
so that **I have a standardized, cohesive development environment for building the Manufacturing Performance Assistant**.

## Acceptance Criteria

1. TurboRepo monorepo is initialized at the project root with proper configuration
2. `apps/web` directory contains a scaffolded Next.js 14+ application using App Router
3. `apps/api` directory contains a scaffolded Python FastAPI application
4. `packages/` directory exists for future shared configurations
5. `turbo.json` is configured with build, dev, and lint pipelines
6. Root `package.json` has workspaces configured for the monorepo
7. Next.js app uses Tailwind CSS and Shadcn/UI foundation (installed, not fully configured)
8. FastAPI app has basic project structure with `app/`, `api/`, `core/`, and `services/` directories
9. Both apps can be started independently with their respective dev commands
10. Basic health check endpoint exists in FastAPI (`/health`)
11. Next.js app renders a basic placeholder page confirming setup

## Tasks / Subtasks

- [ ] Task 1: Initialize TurboRepo monorepo (AC: #1, #4, #5, #6)
  - [ ] 1.1 Create project directory structure
  - [ ] 1.2 Initialize root `package.json` with workspaces configuration
  - [ ] 1.3 Create `turbo.json` with build, dev, and lint pipelines
  - [ ] 1.4 Create `packages/` directory placeholder

- [ ] Task 2: Scaffold Next.js frontend in apps/web (AC: #2, #7, #11)
  - [ ] 2.1 Initialize Next.js 14+ with App Router (`npx create-next-app@latest`)
  - [ ] 2.2 Configure for TypeScript
  - [ ] 2.3 Install and configure Tailwind CSS
  - [ ] 2.4 Install Shadcn/UI CLI and initialize
  - [ ] 2.5 Create basic placeholder page at `/` route
  - [ ] 2.6 Update `package.json` name to `@tfn-aihub/web`

- [ ] Task 3: Scaffold Python FastAPI backend in apps/api (AC: #3, #8, #10)
  - [ ] 3.1 Create `apps/api` directory structure
  - [ ] 3.2 Create Python project with `requirements.txt`
  - [ ] 3.3 Create `app/` directory with `__init__.py` and `main.py`
  - [ ] 3.4 Create `app/api/` directory for endpoints
  - [ ] 3.5 Create `app/core/` directory for config and security
  - [ ] 3.6 Create `app/services/` directory for business logic
  - [ ] 3.7 Implement health check endpoint at `/health`
  - [ ] 3.8 Create basic `Dockerfile` for Railway deployment

- [ ] Task 4: Verify local development workflow (AC: #9)
  - [ ] 4.1 Verify `npm run dev` starts Next.js on localhost:3000
  - [ ] 4.2 Verify `uvicorn app.main:app --reload` starts FastAPI on localhost:8000
  - [ ] 4.3 Document local development commands in root README

## Dev Notes

### Technical Stack Requirements

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Monorepo | TurboRepo | Latest | Use `npx create-turbo@latest` or manual setup |
| Frontend | Next.js | 14+ | Must use App Router (`app/` directory) |
| Frontend Language | TypeScript | 5.x | Strict mode enabled |
| Styling | Tailwind CSS | 3.x | With `@tailwindcss/forms` plugin |
| UI Components | Shadcn/UI | Latest | Initialize with CLI, don't install all components |
| Backend | Python | 3.11+ | Required for LangChain compatibility |
| API Framework | FastAPI | 0.109+ | With async support |
| Backend Server | Uvicorn | Latest | For local development |

### Architecture Patterns

- **Modular Monolith**: Frontend and Backend are separate apps but in one repo
- **API-First**: FastAPI provides REST endpoints, Next.js consumes them
- **Component Library**: Shadcn/UI provides accessible, customizable components

### Directory Structure Target

```text
manufacturing-assistant/
├── apps/
│   ├── web/                    # Next.js Frontend
│   │   ├── src/
│   │   │   ├── app/            # App Router pages
│   │   │   ├── components/     # UI components (Shadcn)
│   │   │   └── lib/            # Utilities
│   │   ├── public/
│   │   ├── tailwind.config.ts
│   │   ├── next.config.js
│   │   ├── tsconfig.json
│   │   └── package.json
│   └── api/                    # Python FastAPI Backend
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py         # FastAPI app entry
│       │   ├── api/            # API endpoints
│       │   │   ├── __init__.py
│       │   │   └── health.py
│       │   ├── core/           # Config, Security
│       │   │   ├── __init__.py
│       │   │   └── config.py
│       │   └── services/       # Business Logic
│       │       └── __init__.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── pyproject.toml      # Optional: for modern Python tooling
├── packages/                   # Shared configs (future)
│   └── .gitkeep
├── turbo.json                  # TurboRepo config
├── package.json                # Root workspace config
└── README.md
```

### Key Implementation Details

**TurboRepo Configuration (`turbo.json`):**
```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "lint": {},
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

**Root `package.json` workspaces:**
```json
{
  "name": "tfn-aihub",
  "private": true,
  "workspaces": ["apps/*", "packages/*"],
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "lint": "turbo run lint"
  },
  "devDependencies": {
    "turbo": "latest"
  }
}
```

**FastAPI Main Entry (`app/main.py`):**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Manufacturing Performance Assistant API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "manufacturing-api"}
```

**Requirements.txt (minimal for scaffold):**
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
```

### Commands Reference

```bash
# Root level - run all apps
npm run dev

# Frontend only
cd apps/web && npm run dev

# Backend only
cd apps/api && uvicorn app.main:app --reload --port 8000

# Build all
npm run build
```

### Project Structure Notes

- The `apps/` directory follows TurboRepo conventions for application workspaces
- `packages/` is prepared for shared TypeScript configs or utilities (Story 1.6 may use this)
- Python backend does NOT participate in npm workspaces but lives in the monorepo for code organization
- Dockerfile in `apps/api/` is for Railway deployment (Story 1.1 scope is scaffold only)

### References

- [Source: architecture.md#4-repository-structure] - Directory structure specification
- [Source: architecture.md#3-tech-stack] - Technology versions and rationale
- [Source: prd.md#4-technical-assumptions] - Core technology decisions
- [Source: epic-1.md#story-1.1] - Story requirements

### Anti-Patterns to Avoid

1. **DO NOT** use Pages Router in Next.js - must use App Router (`app/` directory)
2. **DO NOT** install all Shadcn components - only initialize the CLI, components added as needed
3. **DO NOT** configure Supabase in this story - that's Story 1.2
4. **DO NOT** set up database connections - that's Stories 1.3-1.5
5. **DO NOT** create complex UI components - just a basic placeholder confirming setup
6. **DO NOT** use `pip install` globally - use virtual environment for Python

### Testing Verification

After implementation, verify:
1. `npm run dev` from root starts without errors
2. Navigate to `http://localhost:3000` - see Next.js placeholder page
3. Navigate to `http://localhost:8000/health` - see JSON health response
4. Navigate to `http://localhost:8000/docs` - see FastAPI Swagger UI
5. `npm run build` completes without errors for web app

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

