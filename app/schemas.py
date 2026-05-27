from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


# --- Project ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    discord_webhook_url: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    discord_webhook_url: Optional[str] = None


class ProjectOut(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Task ---
class TaskBase(BaseModel):
    title: str
    project_id: int
    done: bool = False
    deadline: Optional[datetime] = None
    position: int = 0


class TaskCreate(TaskBase):
    done: bool = False
    position: int = 0


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None
    deadline: Optional[datetime] = None
    position: Optional[int] = None


class TaskOut(TaskBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- SubTask ---
class SubTaskBase(BaseModel):
    title: str
    done: bool = False


class SubTaskCreate(SubTaskBase):
    pass


class SubTaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


class SubTaskOut(SubTaskBase):
    id: int
    task_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Task with SubTasks ---
class TaskDetail(TaskOut):
    subtasks: List[SubTaskOut] = []
