from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, assets, summaries, actions, auth

app = FastAPI(
    title="Manufacturing Performance Assistant API",
    description="Backend API for plant performance monitoring and insights",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(summaries.router, prefix="/api/summaries", tags=["Summaries"])
app.include_router(actions.router, prefix="/api/actions", tags=["Actions"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])


@app.get("/")
async def root():
    return {"message": "Manufacturing Performance Assistant API"}
