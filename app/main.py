from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.routes import projects, tasks
from app.services import stt, discord

Base.metadata.create_all(bind=engine)

# Migrate existing DB: add description column to tasks table if missing
with engine.connect() as conn:
    import sqlalchemy
    try:
        conn.execute(sqlalchemy.text("ALTER TABLE tasks ADD COLUMN description TEXT"))
        conn.commit()
    except Exception:
        pass  # column already exists

app = FastAPI(title="Pelemello")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_files = StaticFiles(directory="static")

# Serve static files under /static
app.mount("/static", static_files, name="static")

# Root redirects to /static/index.html
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

# Routers
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(tasks.subtask_router)
app.include_router(stt.router)
app.include_router(discord.router)
