# Development Guide

## Prerequisites

- **Node.js** 18+
- **Python** 3.11+
- **npm** 10+
- **Git**

## Quick Start

### 1. Clone and Install

```bash
# Clone repository
git clone <repository-url>
cd tfn-aihub

# Install frontend dependencies (from root)
npm install

# Set up Python virtual environment for API
cd apps/api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup

#### Frontend (apps/web/.env)
```bash
cp apps/web/.env.example apps/web/.env
# Edit with your values:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

#### Backend (apps/api/.env)
```bash
cp apps/api/.env.example apps/api/.env
# Edit with your values:
# SUPABASE_URL=your-supabase-url
# SUPABASE_KEY=your-service-role-key
# OPENAI_API_KEY=your-openai-key
# ANTHROPIC_API_KEY=your-anthropic-key (optional)
# MSSQL_SERVER=your-mssql-server (optional)
# MSSQL_DATABASE=your-database
# MSSQL_USER=your-user
# MSSQL_PASSWORD=your-password
```

### 3. Start Development Servers

#### Option A: Run Everything (Turbo)
```bash
# From root directory
npm run dev
```

#### Option B: Run Separately

**Frontend:**
```bash
cd apps/web
npm run dev
# Starts on http://localhost:3000
```

**Backend:**
```bash
cd apps/api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Starts on http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

## Project Structure

```
tfn-aihub/
├── apps/
│   ├── web/           # Next.js frontend
│   └── api/           # Python FastAPI backend
├── packages/          # Shared packages (future)
├── supabase/          # Database migrations
├── _bmad-output/      # BMAD workflow outputs
├── turbo.json         # Turborepo config
└── package.json       # Root workspace
```

## Development Workflow

### Frontend Development

```bash
cd apps/web

# Start dev server
npm run dev

# Run tests
npm run test

# Run tests once
npm run test:run

# Lint
npm run lint

# Build
npm run build
```

**Key directories:**
- `src/app/` - Next.js App Router pages
- `src/components/` - React components
- `src/lib/` - Utility functions

### Backend Development

```bash
cd apps/api
source venv/bin/activate

# Start dev server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific tests
pytest tests/services/agent/
```

**Key directories:**
- `app/api/` - FastAPI route handlers
- `app/services/` - Business logic
- `app/services/agent/tools/` - AI agent tools
- `app/models/` - Pydantic models
- `tests/` - Pytest tests

### Adding a New AI Tool

1. Create tool file in `apps/api/app/services/agent/tools/`:

```python
# apps/api/app/services/agent/tools/my_new_tool.py
from pydantic import BaseModel, Field
from app.services.agent.base import ManufacturingTool, ToolResult, Citation

class MyToolInput(BaseModel):
    """Input schema for MyNewTool."""
    param: str = Field(..., description="Description of param")

class MyNewTool(ManufacturingTool):
    name = "my_new_tool"
    description = "Description of what this tool does"
    args_schema = MyToolInput
    citations_required = True

    async def _arun(self, param: str) -> ToolResult:
        # Implement tool logic
        data = {"result": f"Processed {param}"}

        citation = self._create_citation(
            source="my_source",
            query=f"Query for {param}"
        )

        return self._create_success_result(
            data=data,
            citations=[citation]
        )
```

2. Register in `apps/api/app/services/agent/tools/__init__.py`:

```python
from .my_new_tool import MyNewTool

__all__ = [
    # ... existing tools
    "MyNewTool",
]
```

3. Write tests in `apps/api/tests/services/agent/tools/test_my_new_tool.py`

### Adding a New Frontend Component

1. Create component in appropriate directory:

```typescript
// apps/web/src/components/my-feature/MyComponent.tsx
'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'

interface MyComponentProps {
  data: MyData
}

export function MyComponent({ data }: MyComponentProps) {
  return (
    <Card>
      {/* Component content */}
    </Card>
  )
}
```

2. Create barrel export:

```typescript
// apps/web/src/components/my-feature/index.ts
export { MyComponent } from './MyComponent'
```

3. Write tests:

```typescript
// apps/web/src/components/my-feature/__tests__/MyComponent.test.tsx
import { render, screen } from '@testing-library/react'
import { MyComponent } from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent data={mockData} />)
    expect(screen.getByText('expected text')).toBeInTheDocument()
  })
})
```

## Database Operations

### Run Migrations

```bash
# Using Supabase CLI
cd supabase
supabase db push

# Or apply manually via Supabase dashboard
```

### Create New Migration

```bash
# Create migration file
touch supabase/migrations/$(date +%Y%m%d%H%M%S)_description.sql
```

## Testing

### Frontend Tests
```bash
cd apps/web
npm run test        # Watch mode
npm run test:run    # Single run
```

### Backend Tests
```bash
cd apps/api
source venv/bin/activate

pytest                           # All tests
pytest tests/services/           # Service tests
pytest tests/api/                # API tests
pytest -k "test_oee"             # Tests matching pattern
pytest --cov=app --cov-report=html  # Coverage report
```

## Linting & Formatting

### Frontend
```bash
cd apps/web
npm run lint        # ESLint
```

### Backend
```bash
cd apps/api
# Add ruff or black to requirements.txt for formatting
ruff check .
ruff format .
```

## Build for Production

### Frontend
```bash
cd apps/web
npm run build
npm run start
```

### Backend
```bash
cd apps/api
# Using Docker
docker build -t tfn-aihub-api .
docker run -p 8000:8000 tfn-aihub-api
```

## Common Issues

### MSSQL Connection Failed
- MSSQL is optional; the app runs without it
- Check `.env` for correct credentials
- Ensure read-only user permissions

### Supabase Connection Issues
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Check RLS policies allow your queries

### OpenAI API Errors
- Verify `OPENAI_API_KEY` is set
- Check API usage limits

## Useful Commands

```bash
# Root level
npm run dev         # Start all apps
npm run build       # Build all apps
npm run lint        # Lint all apps
npm run test        # Test all apps

# Turbo cache
turbo clean         # Clear turbo cache
```

---
*Generated by BMAD Document Project Workflow on 2026-01-10*
