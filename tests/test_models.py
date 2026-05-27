"""Tests for SQLAlchemy models — entities, relationships, defaults."""
import pytest
from datetime import datetime
from app.models import Project, Task, SubTask


class TestProjectModel:
    def test_create_project(self, db):
        project = Project(name="Test Project", description="A test project")
        db.add(project)
        db.commit()
        db.refresh(project)

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.created_at is not None
        assert project.discord_webhook_url is None

    def test_create_project_minimal(self, db):
        project = Project(name="Minimal")
        db.add(project)
        db.commit()

        assert project.id is not None
        assert project.name == "Minimal"

    def test_create_project_with_webhook(self, db):
        project = Project(
            name="With Webhook",
            discord_webhook_url="https://discord.com/api/webhooks/123/abc",
        )
        db.add(project)
        db.commit()

        assert project.discord_webhook_url == "https://discord.com/api/webhooks/123/abc"


class TestTaskModel:
    def test_create_task(self, db):
        project = Project(name="My Project")
        db.add(project)
        db.commit()

        task = Task(title="Buy milk", project_id=project.id)
        db.add(task)
        db.commit()
        db.refresh(task)

        assert task.id is not None
        assert task.title == "Buy milk"
        assert task.done is False
        assert task.position == 0
        assert task.deadline is None
        assert task.created_at is not None

    def test_create_task_with_deadline(self, db):
        project = Project(name="My Project")
        db.add(project)
        db.commit()

        deadline = datetime(2026, 6, 1, 12, 0, 0)
        task = Task(title="Finish report", project_id=project.id, deadline=deadline)
        db.add(task)
        db.commit()

        assert task.deadline == deadline

    def test_task_belongs_to_project(self, db):
        project = Project(name="My Project")
        db.add(project)
        db.commit()

        task = Task(title="Task 1", project_id=project.id)
        db.add(task)
        db.commit()
        db.refresh(project)

        assert len(project.tasks) == 1
        assert project.tasks[0].title == "Task 1"

    def test_project_cascade_delete_tasks(self, db):
        project = Project(name="My Project")
        db.add(project)
        db.commit()

        task = Task(title="Task 1", project_id=project.id)
        db.add(task)
        db.commit()

        db.delete(project)
        db.commit()

        assert db.query(Task).filter_by(id=task.id).first() is None

    def test_task_position(self, db):
        project = Project(name="My Project")
        db.add(project)
        db.commit()

        task = Task(title="Task 1", project_id=project.id, position=5)
        db.add(task)
        db.commit()

        assert task.position == 5


class TestSubTaskModel:
    def test_create_subtask(self, db):
        project = Project(name="My Project")
        db.add(project)
        db.commit()

        task = Task(title="Task 1", project_id=project.id)
        db.add(task)
        db.commit()

        subtask = SubTask(title="Step 1", task_id=task.id)
        db.add(subtask)
        db.commit()
        db.refresh(subtask)

        assert subtask.id is not None
        assert subtask.title == "Step 1"
        assert subtask.done is False
        assert subtask.task_id == task.id
        assert subtask.created_at is not None

    def test_subtask_belongs_to_task(self, db):
        project = Project(name="My Project")
        db.add(project)
        db.commit()

        task = Task(title="Task 1", project_id=project.id)
        db.add(task)
        db.commit()

        subtask = SubTask(title="Step 1", task_id=task.id)
        db.add(subtask)
        db.commit()
        db.refresh(task)

        assert len(task.subtasks) == 1
        assert task.subtasks[0].title == "Step 1"

    def test_task_cascade_delete_subtasks(self, db):
        project = Project(name="My Project")
        db.add(project)
        db.commit()

        task = Task(title="Task 1", project_id=project.id)
        db.add(task)
        db.commit()

        subtask = SubTask(title="Step 1", task_id=task.id)
        db.add(subtask)
        db.commit()

        db.delete(task)
        db.commit()

        assert db.query(SubTask).filter_by(id=subtask.id).first() is None

    def test_subtask_done_toggle(self, db):
        project = Project(name="My Project")
        db.add(project)
        db.commit()

        task = Task(title="Task 1", project_id=project.id)
        db.add(task)
        db.commit()

        subtask = SubTask(title="Step 1", task_id=task.id)
        db.add(subtask)
        db.commit()

        subtask.done = True
        db.commit()

        assert subtask.done is True
