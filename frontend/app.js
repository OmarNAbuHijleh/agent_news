const STAGE_META = {
  planning: { label: "Planning", kind: "status" },
  plan: { label: "Research Plan", kind: "content" },
  researching: { label: "Researching", kind: "status" },
  research_result: { label: "Research Findings", kind: "content" },
  fact_checking: { label: "Fact-Checking", kind: "status" },
  fact_check_result: { label: "Fact Check", kind: "content" },
  synthesizing: { label: "Synthesizing", kind: "status" },
  final: { label: "Final Report", kind: "final" },
  cache_hit: { label: "Answer (from cache)", kind: "final" },
};

const transcript = document.getElementById("transcript");
const form = document.getElementById("query-form");
const input = document.getElementById("query-input");
const statusBanner = document.getElementById("status-banner");

function setBusy(isBusy) {
  // While busy, the search bar is replaced entirely by the status banner (not just disabled),
  // so it's unmistakable that no other query can be started until this one finishes.
  form.hidden = isBusy;
  statusBanner.hidden = !isBusy;
}

function appendMessage(kind, label, content) {
  const wrapper = document.createElement("div");
  wrapper.className = `message message-${kind}`;

  const labelEl = document.createElement("div");
  labelEl.className = "message-label";
  labelEl.textContent = label;

  const contentEl = document.createElement("div");
  contentEl.className = "message-content";
  contentEl.textContent = content;

  wrapper.appendChild(labelEl);
  wrapper.appendChild(contentEl);
  transcript.appendChild(wrapper);
  transcript.scrollTop = transcript.scrollHeight;
}

function handleProgressEvent(event) {
  const meta = STAGE_META[event.stage] || { label: event.stage, kind: "content-block" };
  const kind = meta.kind === "content" ? "content-block" : meta.kind;
  appendMessage(kind, meta.label, event.content);
}

function handleRawSseMessage(rawMessage) {
  const dataLine = rawMessage.split("\n").find((line) => line.startsWith("data: "));
  if (!dataLine) return;
  try {
    const event = JSON.parse(dataLine.slice("data: ".length));
    handleProgressEvent(event);
  } catch (err) {
    console.error("Failed to parse progress event", err, rawMessage);
  }
}

async function streamResearch(query) {
  let buffer = "";
  try {
    const response = await fetch("/api/v1/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!response.ok || !response.body) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        handleRawSseMessage(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
        boundary = buffer.indexOf("\n\n");
      }
    }
  } catch (err) {
    appendMessage("error", "Error", `Something went wrong: ${err.message}`);
  } finally {
    setBusy(false);
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) return;

  appendMessage("user", "You", query);
  input.value = "";
  setBusy(true);
  streamResearch(query);
});
