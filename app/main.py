from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.routes import projects, tasks
from app.services import stt, discord

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pelemelo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(tasks.subtask_router)
app.include_router(stt.router)
app.include_router(discord.router)
