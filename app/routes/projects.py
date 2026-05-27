from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Task
from app.schemas import ProjectCreate, ProjectUpdate, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


@router.post("", response_model=ProjectOut)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**project_in.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, project_in: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"detail": "Project deleted"}


@router.get("/{project_id}/tasks")
def list_tasks_for_project(project_id: int, db: Session = Depends(get_db)):
    """List all tasks for a project — returns tasks with subtasks."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.schemas import TaskDetail, SubTaskOut
    from app.models import SubTask

    tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.position).all()
    result = []
    for task in tasks:
        subtasks = db.query(SubTask).filter(SubTask.task_id == task.id).all()
        detail = TaskDetail.model_validate(task).model_dump()
        detail["subtasks"] = [SubTaskOut.model_validate(s).model_dump() for s in subtasks]
        result.append(detail)
    return result
