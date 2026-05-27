import requests

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Task, SubTask

router = APIRouter(prefix="/api/discord", tags=["discord"])


@router.post("/relay/{task_id}")
def relay_task_to_discord(task_id: int, db: Session = Depends(get_db)):
    """Post a rich embed to the project's discord_webhook_url when a task is done."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    project = db.query(Project).filter(Project.id == task.project_id).first()
    if project is None or not project.discord_webhook_url:
        raise HTTPException(
            status_code=400,
            detail="Project has no Discord webhook URL configured",
        )

    subtasks = db.query(SubTask).filter(SubTask.task_id == task_id).all()
    subtask_count = len(subtasks)
    subtask_done = sum(1 for s in subtasks if s.done)

    embed = {
        "title": f"Task Completed: {task.title}",
        "description": f"Project: {project.name}",
        "color": 5763719,  # green
        "fields": [
            {"name": "Deadline", "value": str(task.deadline) if task.deadline else "No deadline", "inline": True},
            {"name": "Subtasks", "value": f"{subtask_done}/{subtask_count}", "inline": True},
        ],
        "footer": {
            "text": "Pelemelo"
        },
    }

    payload = {
        "embeds": [embed],
    }

    try:
        resp = requests.post(
            project.discord_webhook_url,
            json=payload,
            timeout=10,
        )
        if resp.status_code not in (200, 204):
            raise HTTPException(
                status_code=502,
                detail=f"Discord webhook returned {resp.status_code}",
            )
        return {"detail": "Message sent to Discord"}
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Discord webhook error: {str(e)}")
