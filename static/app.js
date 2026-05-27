// ===== Pelemelo Frontend =====
const API = "/api";
let currentProjectId = null;
let currentProjectWebhook = null;
let allTasks = {};
let draggedTaskId = null;

// ===== API helpers =====
async function api(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();
  return data;
}

// ===== Project list =====
async function loadProjects() {
  const projects = await api("GET", "/projects");
  const list = document.getElementById("project-list");
  list.innerHTML = "";
  for (const p of projects) {
    const li = document.createElement("li");
    li.textContent = p.name;
    li.dataset.id = p.id;
    li.dataset.webhook = p.discord_webhook_url || "";
    if (p.id === currentProjectId) li.classList.add("active");
    li.addEventListener("click", () => selectProject(p.id, p.name));
    li.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      openEditProject(p.id);
    });
    list.appendChild(li);
  }
}

async function selectProject(id, name) {
  currentProjectId = id;
  const activeLi = document.querySelector(`#project-list li[data-id="${id}"]`);
  currentProjectWebhook = activeLi ? activeLi.dataset.webhook || null : null;
  document.querySelectorAll("#project-list li").forEach(li => {
    li.classList.toggle("active", parseInt(li.dataset.id) === id);
  });
  document.getElementById("project-title").textContent = name;
  document.getElementById("btn-add-task").style.display = "";
  document.getElementById("kanban-columns").style.display = "";
  await loadTasks();
}

async function addProject() {
  const name = document.getElementById("project-name").value.trim();
  if (!name) return;
  const body = {
    name,
    discord_webhook_url: document.getElementById("project-webhook").value.trim() || null,
  };
  await api("POST", "/projects", body);
  closeModal("modal-add-project");
  document.getElementById("project-name").value = "";
  document.getElementById("project-webhook").value = "";
  await loadProjects();
}

// ===== Tasks =====
async function loadTasks() {
  if (!currentProjectId) return;
  const tasks = await api("GET", `/projects/${currentProjectId}/tasks`);
  allTasks = {};
  for (const t of tasks) {
    allTasks[t.id] = t;
  }
  renderBoard();
}

function renderBoard() {
  const colTodo = document.getElementById("col-todo");
  const colDoing = document.getElementById("col-doing");
  const colDone = document.getElementById("col-done");
  colTodo.innerHTML = "";
  colDoing.innerHTML = "";
  colDone.innerHTML = "";

  for (const t of Object.values(allTasks)) {
    const card = createTaskCard(t);
    if (t.done) colDone.appendChild(card);
    else if (t.position > 0) colDoing.appendChild(card);
    else colTodo.appendChild(card);
  }
}

function createTaskCard(task) {
  const div = document.createElement("div");
  div.className = "task-card";
  div.dataset.id = task.id;
  div.dataset.done = task.done;
  div.draggable = true;

  const title = document.createElement("div");
  title.className = "task-title";
  title.textContent = task.title;
  div.appendChild(title);

  // Optional description
  if (task.description) {
    const desc = document.createElement("div");
    desc.className = "task-desc";
    desc.textContent = task.description;
    div.appendChild(desc);
  }

  const meta = document.createElement("div");
  meta.className = "task-meta";
  const deadlineSpan = document.createElement("span");
  if (task.deadline) {
    deadlineSpan.className = "task-deadline";
    deadlineSpan.textContent = new Date(task.deadline).toLocaleDateString();
  }
  meta.appendChild(deadlineSpan);

  const posSpan = document.createElement("span");
  posSpan.textContent = `pos:${task.position}`;
  meta.appendChild(posSpan);
  div.appendChild(meta);

  // Subtask bar
  if (task.subtasks && task.subtasks.length > 0) {
    const bar = document.createElement("div");
    bar.className = "subtask-bar";
    const done = task.subtasks.filter(s => s.done).length;
    bar.textContent = `${done}/${task.subtasks.length} subtasks ▾`;
    bar.addEventListener("click", (e) => {
      e.stopPropagation();
      const list = div.querySelector(".subtask-list");
      list.classList.toggle("expanded");
    });
    div.appendChild(bar);

    const list = document.createElement("div");
    list.className = "subtask-list";
    for (const s of task.subtasks) {
      const item = document.createElement("div");
      item.className = "subtask-item" + (s.done ? " done" : "");
      item.innerHTML = `<input type="checkbox" ${s.done ? "checked" : ""}><label>${s.title}</label>`;
      item.querySelector("input").addEventListener("change", async () => {
        await api("PUT", `/subtasks/${s.id}`, { done: item.querySelector("input").checked });
        await loadTasks();
      });
      list.appendChild(item);
    }
    div.appendChild(list);
  }

  // Double-click to edit
  div.addEventListener("dblclick", () => openEditTask(task));

  // Drag events
  div.addEventListener("dragstart", (e) => {
    draggedTaskId = task.id;
    div.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
  });
  div.addEventListener("dragend", () => {
    div.classList.remove("dragging");
    draggedTaskId = null;
  });

  return div;
}

// ===== Drag & Drop =====
document.querySelectorAll(".column-body").forEach(col => {
  col.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    col.classList.add("drag-over");
  });
  col.addEventListener("dragleave", () => col.classList.remove("drag-over"));
  col.addEventListener("drop", async (e) => {
    e.preventDefault();
    col.classList.remove("drag-over");
    if (!draggedTaskId) return;
    const status = col.parentElement.dataset.status;
    const updates = {};
    if (status === "done") updates.done = true;
    else if (status === "doing") { updates.done = false; updates.position = 1; }
    else { updates.done = false; updates.position = 0; }

    try {
      await api("PUT", `/tasks/${draggedTaskId}`, updates);
      // Auto-relay to Discord when task is marked done
      if (status === "done") relayToDiscord(draggedTaskId);
      await loadTasks();
    } catch (err) {
      console.error("Drop error:", err);
    }
  });
});

// ===== Trash Zone =====
const trashZone = document.getElementById("trash-zone");
trashZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  trashZone.classList.add("drag-over");
});
trashZone.addEventListener("dragleave", () => trashZone.classList.remove("drag-over"));
trashZone.addEventListener("drop", async (e) => {
  e.preventDefault();
  trashZone.classList.remove("drag-over");
  if (!draggedTaskId) return;
  const taskId = draggedTaskId;
  draggedTaskId = null;
  try {
    const result = await api("DELETE", `/tasks/${taskId}`);
    if (result.project_deleted) {
      // Reload projects list and reset to unselected state
      currentProjectId = null;
      document.getElementById("project-title").textContent = "Select a project";
      document.getElementById("btn-add-task").style.display = "none";
      document.getElementById("kanban-columns").style.display = "none";
      await loadProjects();
    } else {
      await loadTasks();
    }
  } catch (err) {
    console.error("Trash drop error:", err);
  }
});

// ===== Task CRUD =====
async function addTask() {
  const title = document.getElementById("task-title").value.trim();
  if (!title) return;
  const body = {
    title,
    project_id: currentProjectId,
    description: document.getElementById("task-desc").value.trim() || null,
    deadline: document.getElementById("task-deadline").value || null,
  };
  await api("POST", "/tasks", body);
  closeModal("modal-add-task");
  document.getElementById("task-title").value = "";
  document.getElementById("task-desc").value = "";
  document.getElementById("task-deadline").value = "";
  await loadTasks();
}

let editingTaskId = null;
async function openEditTask(task) {
  editingTaskId = task.id;
  document.getElementById("edit-task-title").value = task.title;
  document.getElementById("edit-task-desc").value = task.description || "";
  document.getElementById("edit-task-deadline").value = task.deadline ? task.deadline.slice(0, 10) : "";
  document.getElementById("modal-edit-task").style.display = "flex";
}

async function saveEditTask() {
  const title = document.getElementById("edit-task-title").value.trim();
  if (!title || !editingTaskId) return;
  const body = {
    title,
    description: document.getElementById("edit-task-desc").value.trim() || null,
    deadline: document.getElementById("edit-task-deadline").value || null,
  };
  await api("PUT", `/tasks/${editingTaskId}`, body);
  closeModal("modal-edit-task");
  await loadTasks();
}

// ===== Project Edit =====
let editingProjectId = null;
async function openEditProject(id) {
  editingProjectId = id;
  const li = document.querySelector(`#project-list li[data-id="${id}"]`);
  document.getElementById("edit-project-name").value = li ? li.textContent : "";
  document.getElementById("edit-project-webhook").value = li ? li.dataset.webhook || "" : "";
  document.getElementById("modal-edit-project").style.display = "flex";
}

async function saveEditProject() {
  const name = document.getElementById("edit-project-name").value.trim();
  if (!name || !editingProjectId) return;
  const body = {
    name,
    discord_webhook_url: document.getElementById("edit-project-webhook").value.trim() || null,
  };
  await api("PUT", `/projects/${editingProjectId}`, body);
  // Update local state
  currentProjectWebhook = body.discord_webhook_url;
  if (editingProjectId === currentProjectId) {
    document.getElementById("project-title").textContent = name;
  }
  closeModal("modal-edit-project");
  await loadProjects();
}

// ===== Discord relay =====
async function relayToDiscord(taskId) {
  try {
    await api("POST", `/discord/relay/${taskId}`);
  } catch (err) {
    console.error("Discord relay error:", err);
  }
}

// ===== STT (Speech-to-Text) =====
let recognition = null;
const micBtn = document.getElementById("btn-mic");

function initSTT() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onresult = (e) => {
    const text = e.results[0][0].transcript;
    document.getElementById("task-title").value = text;
    micBtn.classList.remove("listening");
    micBtn.style.display = "none";
  };

  recognition.onerror = () => {
    micBtn.classList.remove("listening");
    micBtn.style.display = "none";
  };

  recognition.onend = () => {
    micBtn.classList.remove("listening");
    micBtn.style.display = "none";
  };
}

// ===== Modals =====
function closeModal(id) {
  document.getElementById(id).style.display = "none";
}

// ===== Event bindings =====
document.getElementById("btn-add-project").addEventListener("click", () => {
  document.getElementById("modal-add-project").style.display = "flex";
});

document.getElementById("btn-add-task").addEventListener("click", () => {
  document.getElementById("modal-add-task").style.display = "flex";
  // Show mic button when task modal is open
  micBtn.style.display = "block";
});

if (micBtn) {
  micBtn.addEventListener("click", () => {
    if (!recognition) return;
    if (micBtn.classList.contains("listening")) {
      recognition.stop();
    } else {
      recognition.start();
      micBtn.classList.add("listening");
    }
  });
}

// Close modals on overlay click
document.querySelectorAll(".modal-overlay").forEach(overlay => {
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeModal(overlay.id);
  });
});

// ===== Init =====
initSTT();
loadProjects();
