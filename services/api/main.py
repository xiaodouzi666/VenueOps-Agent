from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import actions, agent, dashboard, demo, health


app = FastAPI(
    title="VenueOps Agent API",
    version="0.1.0",
    description="Operations copilot backend for retail and event venue demos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(actions.router, prefix="/api/actions", tags=["actions"])
app.include_router(demo.router, prefix="/api/demo", tags=["demo"])
