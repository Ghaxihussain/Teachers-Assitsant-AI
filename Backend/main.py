from fastapi import FastAPI
from .routes import teachers, students
from contextlib import asynccontextmanager
from .config.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(teachers.router)
app.include_router(students.router)