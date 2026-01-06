# TFN AI Hub - Manufacturing Performance Assistant

A monorepo containing the Manufacturing Performance Assistant application - a plant performance monitoring and insights dashboard.

## Project Structure

```
tfn-aihub/
├── apps/
│   ├── web/           # Next.js 14 Frontend (App Router)
│   └── api/           # Python FastAPI Backend
├── packages/          # Shared configurations (future)
├── turbo.json         # TurboRepo configuration
└── package.json       # Root workspace configuration
```

## Tech Stack

- **Frontend**: Next.js 14+ with App Router, TypeScript, Tailwind CSS, Shadcn/UI
- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Monorepo**: TurboRepo

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- npm 10+

### Installation

1. Install frontend dependencies:
```bash
npm install
```

2. Set up Python virtual environment for the API:
```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Development

#### Run All Apps (Frontend)

```bash
npm run dev
```

This starts the Next.js frontend on http://localhost:3000

#### Run Frontend Only

```bash
cd apps/web
npm run dev
```

#### Run Backend Only

```bash
cd apps/api
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API Root: http://localhost:8000
- Health Check: http://localhost:8000/health
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Build

```bash
npm run build
```

### Lint

```bash
npm run lint
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API root message |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI documentation |

## License

Private - All rights reserved.
