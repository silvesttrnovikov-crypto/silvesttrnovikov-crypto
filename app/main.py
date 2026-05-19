from fastapi import FastAPI
from app import models
from app.database import engine
from app.routers import auth_router, project_router, task_router
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Load-Balanced Task Manager",
    description="REST API с автоматическим балансировщиком задач на основе квалификации сотрудников",
    version="1.0.0"
)

app.include_router(auth_router.router)
app.include_router(project_router.router)
app.include_router(task_router.router)

@app.get("/")
def read_root():
    return {"status": "API запущен. Перейдите на /docs для просмотра документации Swagger."}