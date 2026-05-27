"""Tests for API endpoints — all CRUD operations, happy + error paths."""
import pytest
from datetime import datetime


# ====== Project CRUD ======

class TestProjectAPI:
    def test_create_project(self, client):
        response = client.post("/api/projects", json={
            "name": "Test Project",
            "description": "For testing",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "For testing"
        assert data["id"] is not None

    def test_create_project_minimal(self, client):
        response = client.post("/api/projects", json={"name": "Minimal"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal"
        assert data["description"] is None

    def test_list_projects_empty(self, client):
        response = client.get("/api/projects")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_projects(self, client):
        client.post("/api/projects", json={"name": "Project A"})
        client.post("/api/projects", json={"name": "Project B"})
        response = client.get("/api/projects")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_update_project(self, client):
        created = client.post("/api/projects", json={"name": "Old Name"}).json()
        project_id = created["id"]

        response = client.put(f"/api/projects/{project_id}", json={
            "name": "New Name",
            "description": "Updated",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Updated"

    def test_update_project_partial(self, client):
        created = client.post("/api/projects", json={
            "name": "Project",
            "description": "Old desc",
        }).json()
        project_id = created["id"]

        response = client.put(f"/api/projects/{project_id}", json={"description": "New desc"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Project"
        assert data["description"] == "New desc"

    def test_delete_project(self, client):
        created = client.post("/api/projects", json={"name": "To Delete"}).json()
        project_id = created["id"]

        response = client.delete(f"/api/projects/{project_id}")
        assert response.status_code == 200

        response = client.get(f"/api/projects/{project_id}/tasks")
        assert response.status_code == 404

    def test_delete_nonexistent_project(self, client):
        response = client.delete("/api/projects/9999")
        assert response.status_code == 404

    def test_update_nonexistent_project(self, client):
        response = client.put("/api/projects/9999", json={"name": "Ghost"})
        assert response.status_code == 404

    def test_create_project_cascades_delete_tasks(self, client):
        project = client.post("/api/projects", json={"name": "Cascading"}).json()
        project_id = project["id"]

        task = client.post("/api/tasks", json={
            "title": "Task 1",
            "project_id": project_id,
        }).json()

        client.delete(f"/api/projects/{project_id}")

        # Task should be gone
        response = client.get(f"/api/tasks/{task['id']}")
        assert response.status_code == 404


# ====== Task CRUD ======

class TestTaskAPI:
    def test_create_task(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        project_id = project["id"]

        response = client.post("/api/tasks", json={
            "title": "Buy groceries",
            "project_id": project_id,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert data["done"] is False
        assert data["position"] == 0

    def test_create_task_with_deadline(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        project_id = project["id"]

        deadline = "2026-06-01T12:00:00"
        response = client.post("/api/tasks", json={
            "title": "Finish report",
            "project_id": project_id,
            "deadline": deadline,
        })
        assert response.status_code == 200
        assert response.json()["deadline"] is not None

    def test_list_tasks_for_project(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        project_id = project["id"]

        client.post("/api/tasks", json={"title": "Task A", "project_id": project_id})
        client.post("/api/tasks", json={"title": "Task B", "project_id": project_id})

        response = client.get(f"/api/projects/{project_id}/tasks")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_tasks_empty_project(self, client):
        project = client.post("/api/projects", json={"name": "Empty"}).json()
        response = client.get(f"/api/projects/{project['id']}/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_update_task_toggle_done(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        task = client.post("/api/tasks", json={
            "title": "Task",
            "project_id": project["id"],
        }).json()

        response = client.put(f"/api/tasks/{task['id']}", json={"done": True})
        assert response.status_code == 200
        assert response.json()["done"] is True

    def test_update_task_position(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        task = client.post("/api/tasks", json={
            "title": "Task",
            "project_id": project["id"],
        }).json()

        response = client.put(f"/api/tasks/{task['id']}", json={"position": 10})
        assert response.status_code == 200
        assert response.json()["position"] == 10

    def test_delete_task(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        task = client.post("/api/tasks", json={
            "title": "Task",
            "project_id": project["id"],
        }).json()

        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 200

        response = client.get(f"/api/tasks/{task['id']}")
        assert response.status_code == 404

    def test_delete_nonexistent_task(self, client):
        response = client.delete("/api/tasks/9999")
        assert response.status_code == 404

    def test_task_cascade_deletes_subtasks(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        task = client.post("/api/tasks", json={
            "title": "Task",
            "project_id": project["id"],
        }).json()

        subtask = client.post(f"/api/tasks/{task['id']}/subtasks", json={
            "title": "Step 1",
        }).json()

        client.delete(f"/api/tasks/{task['id']}")

        # Subtask should be gone
        response = client.get(f"/api/subtasks/{subtask['id']}")
        assert response.status_code == 404

    def test_get_task_with_subtasks(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        task = client.post("/api/tasks", json={
            "title": "Task",
            "project_id": project["id"],
        }).json()

        client.post(f"/api/tasks/{task['id']}/subtasks", json={"title": "Step 1"})
        client.post(f"/api/tasks/{task['id']}/subtasks", json={"title": "Step 2"})

        response = client.get(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["subtasks"]) == 2

    def test_get_nonexistent_task(self, client):
        response = client.get("/api/tasks/9999")
        assert response.status_code == 404

    def test_update_nonexistent_task(self, client):
        response = client.put("/api/tasks/9999", json={"done": True})
        assert response.status_code == 404

    def test_list_tasks_nonexistent_project(self, client):
        response = client.get("/api/projects/9999/tasks")
        assert response.status_code == 404


# ====== SubTask CRUD ======

class TestSubTaskAPI:
    def test_create_subtask(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        task = client.post("/api/tasks", json={
            "title": "Task",
            "project_id": project["id"],
        }).json()

        response = client.post(f"/api/tasks/{task['id']}/subtasks", json={
            "title": "Step 1",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Step 1"
        assert data["done"] is False

    def test_update_subtask_toggle_done(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        task = client.post("/api/tasks", json={
            "title": "Task",
            "project_id": project["id"],
        }).json()
        subtask = client.post(f"/api/tasks/{task['id']}/subtasks", json={
            "title": "Step 1",
        }).json()

        response = client.put(f"/api/subtasks/{subtask['id']}", json={"done": True})
        assert response.status_code == 200
        assert response.json()["done"] is True

    def test_delete_subtask(self, client):
        project = client.post("/api/projects", json={"name": "Project"}).json()
        task = client.post("/api/tasks", json={
            "title": "Task",
            "project_id": project["id"],
        }).json()
        subtask = client.post(f"/api/tasks/{task['id']}/subtasks", json={
            "title": "Step 1",
        }).json()

        response = client.delete(f"/api/subtasks/{subtask['id']}")
        assert response.status_code == 200

        response = client.get(f"/api/subtasks/{subtask['id']}")
        assert response.status_code == 404

    def test_delete_nonexistent_subtask(self, client):
        response = client.delete("/api/subtasks/9999")
        assert response.status_code == 404

    def test_update_nonexistent_subtask(self, client):
        response = client.put("/api/subtasks/9999", json={"done": True})
        assert response.status_code == 404

    def test_create_subtask_nonexistent_task(self, client):
        response = client.post("/api/tasks/9999/subtasks", json={"title": "Ghost"})
        assert response.status_code == 404
