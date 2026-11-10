"use client";

import { useMemo, useState } from "react";

const starterPrompts = [
  "Explain how the Axaliai infrastructure fits together",
  "What is the role of XParallel?",
  "Describe the Omni orchestration architecture",
  "How should AI memory be verified?",
];

const starterMessages = [
  {
    role: "assistant",
    content:
      "Welcome to the ƎllE preview. The workspace interface is available for review; live chat will be enabled after sign-in and workspace authorization are connected.",
  },
];

export default function AssistantPreview() {
  const [messages, setMessages] = useState(starterMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("Preview");

  const quickStats = useMemo(
    () => [
      { label: "Network", value: "Not connected" },
      { label: "Mode", value: "Text preview" },
      { label: "Status", value: "Preview only" },
    ],
    []
  );

  async function sendPrompt(promptText) {
    const message = promptText ?? input.trim();
    if (!message || loading) return;

    const nextUserMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, nextUserMessage]);
    setInput("");
    setLoading(true);
    setStatus("Checking access…");

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: message }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.message || data?.error || "Live assistant access is not available."
        );
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.message || data.response || data.answer || "No response was returned.",
        },
      ]);
      setStatus("Connected");
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: error.message || "Live assistant access is currently unavailable.",
        },
      ]);
      setStatus("Unavailable");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">Ǝ</div>
          <div>
            <p className="eyebrow">AXALIAI</p>
            <h1>ƎllE</h1>
          </div>
        </div>

        <nav className="nav-panel" aria-label="Preview navigation">
          <span className="nav-item active" aria-current="page">Workspace preview</span>
          <span className="nav-item">Memory — not connected</span>
          <span className="nav-item">Voice — not connected</span>
          <span className="nav-item">Deployment — not available</span>
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
            <p className="eyebrow">AXALIAI INTELLIGENCE</p>
            <h2>ƎllE workspace preview</h2>
          </div>
          <div className="status-pill" role="status">{status}</div>
        </header>

        <div className="prompt-grid">
          {starterPrompts.map((prompt) => (
            <button key={prompt} className="prompt-chip" onClick={() => sendPrompt(prompt)} disabled={loading}>
              {prompt}
            </button>
          ))}
        </div>

        <div className="chat-window" aria-live="polite">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`message-row ${message.role === "user" ? "user" : "assistant"}`}
            >
              <div className="message-bubble">{message.content}</div>
            </div>
          ))}
          {loading && <div className="typing-indicator">Checking access…</div>}
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
            placeholder="Preview the ƎllE workspace…"
            aria-label="Preview prompt"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? "Checking" : "Send"}
          </button>
        </form>
        <p className="eyebrow">Live chat, personal memory and voice remain disabled until secure sign-in and workspace authorization are verified.</p>
      </section>
    </main>
  );
}
