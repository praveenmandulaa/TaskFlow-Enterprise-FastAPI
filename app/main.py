
from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.roles import router as roles_router

from app.api.routes import teams
from app.api.routes import projects, tasks


app = FastAPI(
    title="TaskFlow Enterprise API",
    description="Enterprise Task and Workflow Management System",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to TaskFlow Enterprise API",
        "status": "running",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "taskflow-api",
    }


app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")

app.include_router(projects.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
