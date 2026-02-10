# Story 1.1: TurboRepo Monorepo Scaffold

Status: Done

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

- [x] Task 1: Initialize TurboRepo monorepo (AC: #1, #4, #5, #6)
  - [x] 1.1 Create project directory structure
  - [x] 1.2 Initialize root `package.json` with workspaces configuration
  - [x] 1.3 Create `turbo.json` with build, dev, and lint pipelines
  - [x] 1.4 Create `packages/` directory placeholder

- [x] Task 2: Scaffold Next.js frontend in apps/web (AC: #2, #7, #11)
  - [x] 2.1 Initialize Next.js 14+ with App Router (`npx create-next-app@latest`)
  - [x] 2.2 Configure for TypeScript
  - [x] 2.3 Install and configure Tailwind CSS
  - [x] 2.4 Install Shadcn/UI CLI and initialize
  - [x] 2.5 Create basic placeholder page at `/` route
  - [x] 2.6 Update `package.json` name to `@tfn-aihub/web`

- [x] Task 3: Scaffold Python FastAPI backend in apps/api (AC: #3, #8, #10)
  - [x] 3.1 Create `apps/api` directory structure
  - [x] 3.2 Create Python project with `requirements.txt`
  - [x] 3.3 Create `app/` directory with `__init__.py` and `main.py`
  - [x] 3.4 Create `app/api/` directory for endpoints
  - [x] 3.5 Create `app/core/` directory for config and security
  - [x] 3.6 Create `app/services/` directory for business logic
  - [x] 3.7 Implement health check endpoint at `/health`
  - [x] 3.8 Create basic `Dockerfile` for Railway deployment

- [x] Task 4: Verify local development workflow (AC: #9)
  - [x] 4.1 Verify `npm run dev` starts Next.js on localhost:3000
  - [x] 4.2 Verify `uvicorn app.main:app --reload` starts FastAPI on localhost:8000
  - [x] 4.3 Document local development commands in root README

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

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Implementation Summary

Successfully implemented the TurboRepo monorepo scaffold with Next.js 14 frontend and Python FastAPI backend. The project structure follows the specified architecture with proper workspaces configuration, Tailwind CSS with Shadcn/UI foundation, and a fully functional FastAPI backend with health endpoint.

### Files Created/Modified

**Created:**
- `README.md` - Root documentation with development commands
- `apps/web/src/lib/utils.ts` - Shadcn/UI utility function (cn helper)
- `apps/web/components.json` - Shadcn/UI CLI configuration
- `apps/web/.eslintrc.json` - ESLint configuration for Next.js
- `apps/web/src/components/ui/` - Directory for Shadcn/UI components (empty, ready for use)

**Modified:**
- `package.json` - Updated name to `tfn-aihub`, verified workspaces configuration
- `apps/web/package.json` - Updated name to `@tfn-aihub/web`, added Shadcn/UI deps, @tailwindcss/forms, tailwindcss-animate, ESLint
- `apps/web/tailwind.config.ts` - Added Shadcn/UI color variables, forms plugin, animate plugin, darkMode config
- `apps/web/src/app/globals.css` - Added Shadcn/UI CSS variables for theming
- `apps/web/src/app/page.tsx` - Enhanced placeholder page confirming setup
- `apps/api/app/api/health.py` - Updated health response to include service name

### Key Decisions

1. **Shadcn/UI Initialization**: Manually configured rather than using CLI to avoid interactive prompts and ensure deterministic setup
2. **CSS Variables**: Used HSL-based CSS variables for theming compatibility with Shadcn/UI
3. **Tailwind Plugins**: Added both `@tailwindcss/forms` and `tailwindcss-animate` as these are commonly needed with Shadcn/UI
4. **ESLint**: Added ESLint with `next/core-web-vitals` configuration for strict linting

### Test Results

| Test | Result |
|------|--------|
| `npm run build` | PASS - Compiled successfully, static pages generated |
| `npm run lint` | PASS - No ESLint warnings or errors |
| FastAPI health endpoint | PASS - Returns `{"status":"healthy","service":"manufacturing-api"}` |
| Python dependencies install | PASS - All requirements installed in venv |

### Notes for Reviewer

1. The existing project structure already had the basic TurboRepo setup; implementation focused on completing missing pieces
2. FastAPI requirements.txt includes additional dependencies beyond the minimal scaffold (for later stories)
3. Virtual environment for Python is not tracked in git (apps/api/venv/)
4. Build outputs verified: Next.js generates optimized static pages

### Acceptance Criteria Status

| AC | Status | Evidence |
|----|--------|----------|
| #1 TurboRepo initialized | PASS | `turbo.json` at root with proper configuration |
| #2 Next.js 14+ with App Router | PASS | `apps/web/src/app/` directory structure |
| #3 FastAPI application | PASS | `apps/api/app/main.py` with routers |
| #4 packages/ directory exists | PASS | `packages/.gitkeep` present |
| #5 turbo.json with pipelines | PASS | build, dev, lint, test tasks configured |
| #6 Root package.json workspaces | PASS | `"workspaces": ["apps/*", "packages/*"]` |
| #7 Tailwind CSS + Shadcn/UI | PASS | `tailwind.config.ts` + `components.json` + CSS variables |
| #8 FastAPI structure | PASS | `app/`, `api/`, `core/`, `services/` directories |
| #9 Both apps start independently | PASS | Verified both dev commands work |
| #10 Health check endpoint | PASS | `/health` returns `{"status":"healthy","service":"manufacturing-api"}` |
| #11 Placeholder page | PASS | `page.tsx` renders setup confirmation |

### File List

```
package.json
turbo.json
README.md
packages/.gitkeep
apps/web/package.json
apps/web/next.config.js
apps/web/tailwind.config.ts
apps/web/tsconfig.json
apps/web/postcss.config.js
apps/web/components.json
apps/web/.eslintrc.json
apps/web/src/app/layout.tsx
apps/web/src/app/page.tsx
apps/web/src/app/globals.css
apps/web/src/lib/utils.ts
apps/web/src/components/ui/
apps/api/requirements.txt
apps/api/Dockerfile
apps/api/app/__init__.py
apps/api/app/main.py
apps/api/app/api/__init__.py
apps/api/app/api/health.py
apps/api/app/core/__init__.py
apps/api/app/core/config.py
apps/api/app/services/__init__.py
```

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-01-06

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | CORS `allow_origins=["*"]` is overly permissive - should be `["http://localhost:3000"]` per spec | HIGH | Fixed |
| 2 | turbo.json uses `"tasks"` instead of `"pipeline"` (new TurboRepo v2 syntax, works correctly) | LOW | Documented |
| 3 | requirements.txt includes dependencies beyond minimal scaffold (for later stories) | LOW | Documented |

**Totals**: 1 HIGH, 0 MEDIUM, 2 LOW

### Fixes Applied

1. **CORS Security Fix** (`apps/api/app/main.py:15`): Changed `allow_origins=["*"]` to `allow_origins=["http://localhost:3000"]` to restrict CORS to the Next.js dev server as specified in the story requirements.

### Remaining Issues

- **turbo.json syntax**: Uses newer `"tasks"` key instead of `"pipeline"` - this is the correct modern TurboRepo v2 syntax and works properly. No action needed.
- **requirements.txt scope**: Includes dependencies for future stories (langchain, mem0ai, supabase, etc.) beyond the minimal scaffold. Not harmful as these are needed for later stories.

### Acceptance Criteria Verification

| AC | Status | Evidence |
|----|--------|----------|
| #1 TurboRepo initialized | ✅ PASS | `turbo.json` at root with proper configuration |
| #2 Next.js 14+ with App Router | ✅ PASS | `apps/web/src/app/` directory structure |
| #3 FastAPI application | ✅ PASS | `apps/api/app/main.py` present |
| #4 packages/ directory | ✅ PASS | `packages/.gitkeep` present |
| #5 turbo.json pipelines | ✅ PASS | build, dev, lint, test configured |
| #6 Root package.json workspaces | ✅ PASS | `"workspaces": ["apps/*", "packages/*"]` |
| #7 Tailwind CSS + Shadcn/UI | ✅ PASS | Config, CSS variables, components.json all present |
| #8 FastAPI structure | ✅ PASS | `app/`, `api/`, `core/`, `services/` directories exist |
| #9 Both apps start | ✅ PASS | Build verified, dev commands documented |
| #10 Health check endpoint | ✅ PASS | `/health` returns `{"status":"healthy","service":"manufacturing-api"}` |
| #11 Placeholder page | ✅ PASS | Enhanced placeholder page renders correctly |

### Build & Lint Verification

```
npm run build: ✅ PASS - Compiled successfully
npm run lint: ✅ PASS - No ESLint warnings or errors
```

### Final Status

**Approved with fixes** - All acceptance criteria met. One HIGH severity security issue (CORS wildcard) was identified and fixed.

