# Personal Task Manager — Plan

## Goal
A web-based, Trello-like personal task manager running on this machine. Supports projects → tasks → sub-tasks with optional deadlines, Discord channel linking, and speech-to-text dictation.

---

## 1. Architecture

**Stack:** Python (FastAPI backend) + vanilla HTML/JS/CSS frontend  
**Storage:** SQLite via SQLAlchemy (local file, auto-migrates)  
**STT:** whisper.cpp CLI (`whisper-cli`) — already available at `~/whisper.cpp`  
**Discord:** Discord webhook — posting task completions to a dedicated channel on the bot_boat server  
**Hosting:** Uvicorn on `0.0.0.0:3000`, started via systemd service  

**Project structure:**
```
~/projects/pelemello/
├── app/
│   ├── main.py           # FastAPI app entry
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic DTOs
│   ├── database.py       # DB session
│   ├── routes/
│   │   ├── projects.py
│   │   ├── tasks.py
│   │   └── discord.py
│   └── services/
│       ├── stt.py        # whisper-cli wrapper
│       └── discord.py    # Discord webhook/relay
├── static/
│   ├── index.html       # SPA (kanban board)
│   ├── style.css
│   └── app.js
├── templates/
│   └── discord_embed.html
├── config.yaml           # Discord webhook URLs, whisper path
└── tests/
    ├── test_models.py
    ├── test_api.py
    └── test_stt.py
```

---

## 2. Data Model

```
Project
  id, name, description, discord_webhook_url (optional), created_at

Task
  id, project_id (FK), title, done (bool), deadline (datetime, optional),
  created_at, position (int, for ordering)

SubTask
  id, task_id (FK), title, done (bool), created_at
```

---

## 3. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create project |
| PUT | `/api/projects/:id` | Update project (incl. webhook URL) |
| DELETE | `/api/projects/:id` | Delete project |
| GET | `/api/projects/:id/tasks` | List tasks for project |
| POST | `/api/tasks` | Create task |
| PUT | `/api/tasks/:id` | Update task (done, deadline, position) |
| DELETE | `/api/tasks/:id` | Delete task |
| POST | `/api/tasks/:id/subtasks` | Create sub-task |
| PUT | `/api/subtasks/:id` | Toggle sub-task done |
| DELETE | `/api/subtasks/:id` | Delete sub-task |
| POST | `/api/stt` | Upload audio → whisper-cli → text |
| POST | `/api/discord/relay/:task_id` | Post task update to Discord channel |

---

## 4. Frontend (Kanban Board)

**Layout:** Sidebar (project list) + main area (Kanban columns: Todo / Doing / Done for each project)  
- Tasks are drag-and-drop between columns  
- Click to expand tasks (with sub-tasks inline)  
- Mic button on each task input → triggers STT, fills title field  
- Optional deadline picker (date + time input)  
- Discord link icon on project header → set webhook URL  
- Tasks with deadline show countdown; overdue in red  

**STT flow:**
1. Click mic → browser `MediaRecorder` (webm/opus)  
2. Send audio blob to `/api/stt`  
3. Backend runs `whisper-cli` with appropriate model  
4. Return transcribed text → fill focused input field  

---

## 5. Discord Integration

**Mode:** Webhook only — POST to Discord when a task is marked done  
**What to post:** Rich embed with task name, project, deadline, subtask completion count  
- Color: green if on time, orange if past deadline  
- The webhook URL is stored per-project in the DB  
- Projects can be linked to a dedicated channel on the bot_boat Discord server

---

## 6. Implementation Phases

### Phase 1: Foundation (TDD)
1. Write model tests (`test_models.py`) — entities, relationships, defaults  
2. Write API tests (`test_api.py`) — all endpoints, happy + error paths  
3. Implement models + database setup  
4. Implement all CRUD API routes  
5. Verify: `pytest tests/test_api.py` passes  

### Phase 2: Frontend
6. Write basic HTML layout (sidebar + kanban columns)  
7. JS: fetch + render project list  
8. JS: task CRUD (create, toggle done, reorder)  
9. JS: sub-task CRUD  
10. CSS: trello-style dark theme  
11. Verify: manual browser test at `localhost:3000`  

### Phase 3: STT
12. Write STT service tests (`test_stt.py`)  
13. Implement `/api/stt` endpoint  
14. JS: MediaRecorder flow, mic button in task form  
15. Verify: speak "Buy groceries", text appears in input  

### Phase 4: Discord
16. Implement `/api/discord/relay/:task_id`  
17. Render Discord link UI in project sidebar  
18. Verify: mark task done → Discord message appears  

### Phase 5: Deployment
19. Write `config.yaml` template  
20. Create systemd service (`pelemello.service`)  
21. Start service, verify at `0.0.0.0:3000`  

---

## 7. Key Files

| File | Changes |
|------|---------|
| `app/main.py` | FastAPI app, CORS, routes |
| `app/models.py` | SQLAlchemy Project/Task/SubTask |
| `app/schemas.py` | Pydantic in/out DTOs |
| `app/database.py` | engine, session, Base |
| `app/routes/projects.py` | Project CRUD |
| `app/routes/tasks.py` | Task + SubTask CRUD |
| `app/routes/discord.py` | relay endpoint |
| `app/services/stt.py` | whisper-cli subprocess |
| `app/services/discord.py` | webhook POST |
| `static/index.html` | SPA shell |
| `static/app.js` | frontend logic |
| `static/style.css` | kanban styling |
| `config.yaml` | settings |
| `~/.config/systemd/user/pelemello.service` | systemd unit |

---

## 8. Notes

- Whisper model: check existing models at `~/whisper.cpp/models/` — use one of them if available, otherwise document the download step in `config.yaml`
- Discord webhook: user will provide the webhook URL for their bot_boat server channel
- No auth needed (personal, same machine)
- TDD: tests first, then implementation
