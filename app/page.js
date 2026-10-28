"use client";

import { useEffect, useMemo, useState } from "react";

const starterPrompts = [
  "Give me a short project status update",
  "Summarize my recent AI memory",
  "Plan the next iteration for this assistant",
  "What should I build to make this feel launch-ready?",
];

const starterMessages = [
  {
    role: "assistant",
    content:
      "Hello — I’m Axaliai, your assistant. Ask me to summarize the workspace, plan the next step, or explore the project roadmap.",
  },
];

export default function Home() {
  const [messages, setMessages] = useState(starterMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("Ready");
  const [hubProviders, setHubProviders] = useState([]);
  const [hubNote, setHubNote] = useState("Checking configured providers…");
  const [hubLoading, setHubLoading] = useState(false);

  async function refreshProviders() {
    setHubLoading(true);
    try {
      const response = await fetch("/api/providers", { cache: "no-store" });
      const data = await response.json().catch(() => ({}));
      setHubProviders(Array.isArray(data.providers) ? data.providers : []);
      setHubNote(data.status_note || (response.ok ? "Provider configuration loaded." : "Backend connection needs configuration."));
    } catch {
      setHubProviders([]);
      setHubNote("Provider directory unavailable. Check the backend connection.");
    } finally {
      setHubLoading(false);
    }
  }

  useEffect(() => {
    refreshProviders();
  }, []);

  const quickStats = useMemo(
    () => [
      { label: "Network", value: "XParallel" },
      { label: "Mode", value: "Voice + AI" },
      { label: "Status", value: "Listening" },
    ],
    []
  );

  async function sendPrompt(promptText) {
    const message = promptText ?? input.trim();
    if (!message) return;

    const nextUserMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, nextUserMessage]);
    setInput("");
    setLoading(true);
    setStatus("Thinking...");

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: message,
          workspace_id: "demo-workspace",
          actor: "demo-user",
          messages: [...messages, nextUserMessage],
          use_memory: true,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || "The assistant could not respond.");
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            data.message ||
            data.response ||
            data.summary ||
            "I’m ready to help. Try another prompt or connect the project backend for the live model.",
        },
      ]);
      setStatus("Connected");
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I’m in local demo mode right now. Connect the backend by setting XP_API_URL and XP_TOKEN to use the live XParallel service.",
        },
      ]);
      setStatus(error.message || "Demo fallback");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">A</div>
          <div>
            <p className="eyebrow">AXALIAI</p>
            <h1>Assistant</h1>
          </div>
        </div>

        <nav className="nav-panel">
          <button className="nav-item active">Workspace</button>
          <button className="nav-item">Memory</button>
          <button className="nav-item">Voice</button>
          <button className="nav-item">Deploy</button>
        </nav>

        <div className="stats-block">
          {quickStats.map((stat) => (
            <div key={stat.label} className="stat-card">
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </div>
          ))}
        </div>
      </aside>

      <section className="workspace-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">Unity AI Voice Interface</p>
            <h2>Axaliai control room</h2>
          </div>
          <div className="status-pill">{status}</div>
        </header>

        <section className="hub-panel" aria-labelledby="hub-title">
          <div className="hub-heading">
            <div>
              <p className="eyebrow">HYBRID INTELLIGENCE</p>
              <h3 id="hub-title">Free Access Hub</h3>
            </div>
            <button className="hub-refresh" type="button" onClick={refreshProviders} disabled={hubLoading}>
              {hubLoading ? "Checking…" : "Refresh"}
            </button>
          </div>
          <p className="hub-note">{hubNote}</p>
          {hubProviders.length > 0 ? (
            <div className="hub-provider-list">
              {hubProviders.map((provider) => (
                <div className="hub-provider" key={provider.id}>
                  <div>
                    <strong>{provider.id}</strong>
                    <span>{provider.kind === "local" ? "Local model" : provider.kind === "free_cloud" ? "Free-tier cloud (quota must be verified)" : "Paid provider"}</span>
                  </div>
                  <span className={`hub-status ${provider.status === "available" ? "verified" : "unknown"}`}>
                    {provider.status === "available" ? "Available" : provider.status === "unavailable" ? "Unavailable" : "Unverified"}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="hub-empty">No providers are configured yet. The hub will not assume a free quota or make a paid request.</p>
          )}
        </section>

        <div className="prompt-grid">
          {starterPrompts.map((prompt) => (
            <button key={prompt} className="prompt-chip" onClick={() => sendPrompt(prompt)}>
              {prompt}
            </button>
          ))}
        </div>

        <div className="chat-window">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`message-row ${message.role === "user" ? "user" : "assistant"}`}
            >
              <div className="message-bubble">
                {message.content}
              </div>
            </div>
          ))}

          {loading && <div className="typing-indicator">Thinking…</div>}
        </div>

        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
            sendPrompt();
          }}
        >
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask Axaliai to summarize, plan, or build..."
            aria-label="Ask the assistant"
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? "Working" : "Send"}
          </button>
        </form>
      </section>
    </main>
  );
}
