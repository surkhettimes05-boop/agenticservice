const form = document.querySelector("#task-form");
const runs = document.querySelector("#runs");
const result = document.querySelector("#result");

async function showRun(id) {
  const response = await fetch(`/api/runs/${id}`);
  const run = await response.json();
  result.textContent = run.output || "No output yet.";
}

async function refreshRuns() {
  const response = await fetch("/api/runs");
  const items = await response.json();
  runs.innerHTML = items.map((run) => `
    <button class="run-row" data-run-id="${run.id}">
      <span>#${run.id}</span>
      <strong>${run.agent_id || "pending"}</strong>
      <em>${run.status}</em>
      <small>${run.prompt}</small>
    </button>
  `).join("");
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const response = await fetch("/api/tasks", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      prompt: data.get("prompt"),
      auto_approve: data.get("auto_approve") === "on",
      dry_run: data.get("dry_run") === "on",
    }),
  });
  const run = await response.json();
  await refreshRuns();
  await showRun(run.id);
  form.reset();
});

runs?.addEventListener("click", (event) => {
  const row = event.target.closest("[data-run-id]");
  if (row) showRun(row.dataset.runId);
});
