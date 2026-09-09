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

const FRESH_QUERY_PLACEHOLDER = "e.g. Nvidia stock price";
const FOLLOW_UP_PLACEHOLDER = "Ask a follow-up about this investigation...";
const FRESH_QUERY_SUBTITLE = "Ask about a topic. You'll see the plan, research, and fact-checking as they happen, not just the final answer.";
const FOLLOW_UP_SUBTITLE = "Ask a follow-up about this investigation, or click New Investigation to research something else.";

const transcript = document.getElementById("transcript");
const form = document.getElementById("query-form");
const input = document.getElementById("query-input");
const statusBanner = document.getElementById("status-banner");
const newInvestigationButton = document.getElementById("new-investigation-button");
const subtitle = document.getElementById("subtitle");

// Accumulates every piece of real evidence (not transient status lines) from the current
// investigation, so a follow-up question can be grounded in the full evidence, not just the
// final summary - closer to the README's "RAG over the investigation's evidence" description.
let investigationContext = "";
let hasCompletedInvestigation = false;

function setBusy(isBusy) {
  // While busy, the search bar is replaced entirely by the status banner (not just disabled),
  // so it's unmistakable that no other query can be started until this one finishes.
  form.hidden = isBusy;
  statusBanner.hidden = !isBusy;
}

function enterFollowUpMode() {
  hasCompletedInvestigation = true;
  newInvestigationButton.hidden = false;
  input.placeholder = FOLLOW_UP_PLACEHOLDER;
  subtitle.textContent = FOLLOW_UP_SUBTITLE;
}

function resetToFreshQueryMode() {
  investigationContext = "";
  hasCompletedInvestigation = false;
  newInvestigationButton.hidden = true;
  input.placeholder = FRESH_QUERY_PLACEHOLDER;
  subtitle.textContent = FRESH_QUERY_SUBTITLE;
  transcript.replaceChildren();
  input.value = "";
  input.focus();
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

  if (kind !== "status") {
    investigationContext += `### ${meta.label}\n${event.content}\n\n`;
  }
  if (event.done) {
    enterFollowUpMode();
  }
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

async function askInvestigation(question) {
  try {
    const response = await fetch("/api/v1/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ context: investigationContext, question }),
    });
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const { answer } = await response.json();
    appendMessage("final", "Answer", answer);
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

  if (hasCompletedInvestigation) {
    askInvestigation(query);
  } else {
    streamResearch(query);
  }
});

newInvestigationButton.addEventListener("click", () => {
  resetToFreshQueryMode();
});
