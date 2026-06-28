from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, users, admin_institutions, admin_sources, notices, alerts, notifications, admin_match
from app.core.config import settings
from app.core.scheduler import shutdown_crawler_scheduler, start_crawler_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = start_crawler_scheduler()
    app.state.crawler_scheduler = scheduler
    try:
        yield
    finally:
        shutdown_crawler_scheduler(scheduler)


app = FastAPI(
    title="Monitor de Editais API",
    description="API para o MVP da plataforma Monitor de Editais",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Monitor de Editais API is running"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(admin_institutions.router, prefix="/admin/institutions", tags=["admin-institutions"])
app.include_router(admin_sources.router, prefix="/admin/sources", tags=["admin-sources"])
app.include_router(notices.router, prefix="/notices", tags=["notices"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(admin_match.router, prefix="/admin", tags=["admin-match"])