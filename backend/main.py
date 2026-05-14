from fastapi import FastAPI
from app.api.routers import auth, users, admin_institutions, admin_sources, notices, alerts, notifications, admin_match

app = FastAPI(
    title="Monitor de Editais API",
    description="API para o MVP da plataforma Monitor de Editais",
    version="1.0.0"
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

