from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, SubTask
from app.schemas import (
    TaskCreate, TaskUpdate, TaskDetail, SubTaskCreate, SubTaskUpdate, SubTaskOut,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskDetail)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    subtasks = db.query(SubTask).filter(SubTask.task_id == task.id).all()
    detail = TaskDetail.model_validate(task).model_dump()
    detail["subtasks"] = [SubTaskOut.model_validate(s).model_dump() for s in subtasks]
    return detail


@router.get("/{task_id}", response_model=TaskDetail)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    subtasks = db.query(SubTask).filter(SubTask.task_id == task_id).all()
    detail = TaskDetail.model_validate(task).model_dump()
    detail["subtasks"] = [SubTaskOut.model_validate(s).model_dump() for s in subtasks]
    return detail


@router.put("/{task_id}", response_model=TaskDetail)
def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task_in.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    subtasks = db.query(SubTask).filter(SubTask.task_id == task_id).all()
    detail = TaskDetail.model_validate(task).model_dump()
    detail["subtasks"] = [SubTaskOut.model_validate(s).model_dump() for s in subtasks]
    return detail


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    project_id = task.project_id
    db.delete(task)
    db.commit()

    # Auto-delete project when its last task is removed
    remaining = db.query(Task).filter(Task.project_id == project_id).count()
    if remaining == 0:
        from app.models import Project
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            db.delete(project)
            db.commit()
            return {"detail": "Task deleted", "project_deleted": True, "project_id": project_id}

    return {"detail": "Task deleted", "project_deleted": False}


@router.post("/{task_id}/subtasks", response_model=SubTaskOut)
def create_subtask(task_id: int, subtask_in: SubTaskCreate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    subtask = SubTask(task_id=task_id, **subtask_in.model_dump())
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


# SubTask routes — separate router to keep prefix clean
subtask_router = APIRouter(prefix="/api/subtasks", tags=["subtasks"])


@subtask_router.get("/{subtask_id}", response_model=SubTaskOut)
def get_subtask(subtask_id: int, db: Session = Depends(get_db)):
    subtask = db.query(SubTask).filter(SubTask.id == subtask_id).first()
    if subtask is None:
        raise HTTPException(status_code=404, detail="SubTask not found")
    return subtask


@subtask_router.put("/{subtask_id}", response_model=SubTaskOut)
def update_subtask(subtask_id: int, subtask_in: SubTaskUpdate, db: Session = Depends(get_db)):
    subtask = db.query(SubTask).filter(SubTask.id == subtask_id).first()
    if subtask is None:
        raise HTTPException(status_code=404, detail="SubTask not found")
    for key, value in subtask_in.model_dump(exclude_unset=True).items():
        setattr(subtask, key, value)
    db.commit()
    db.refresh(subtask)
    return subtask


@subtask_router.delete("/{subtask_id}")
def delete_subtask(subtask_id: int, db: Session = Depends(get_db)):
    subtask = db.query(SubTask).filter(SubTask.id == subtask_id).first()
    if subtask is None:
        raise HTTPException(status_code=404, detail="SubTask not found")
    db.delete(subtask)
    db.commit()
    return {"detail": "SubTask deleted"}
