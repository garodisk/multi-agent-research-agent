"use client";
import { useState, useRef, useEffect, FormEvent } from "react";

// ── Types ──────────────────────────────────────────────────────────────────
interface AgentStep {
  agent: string;
  confidence?: number;
  result?: string;
  attempts?: number;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "clarification";
  content: string;
  trace?: AgentStep[];
  agentsRun?: { agent: string }[];
}

// ── Agent pill config ──────────────────────────────────────────────────────
const AGENT_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  clarity:   { color: "#93c5fd", bg: "rgba(59,130,246,0.15)",  label: "Clarity"   },
  research:  { color: "#86efac", bg: "rgba(34,197,94,0.15)",   label: "Research"  },
  validator: { color: "#fca5a5", bg: "rgba(239,68,68,0.15)",   label: "Validator" },
  synthesis: { color: "#c4b5fd", bg: "rgba(168,85,247,0.15)",  label: "Synthesis" },
};

// ── AgentTrace component ───────────────────────────────────────────────────
function AgentTrace({ steps }: { steps: AgentStep[] }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap", marginTop: "12px" }}>
      {steps.map((step, i) => {
        const cfg = AGENT_CONFIG[step.agent] ?? { color: "#94a3b8", bg: "rgba(148,163,184,0.15)", label: step.agent };
        let extra = "";
        if (step.agent === "research" && step.confidence !== undefined)
          extra = ` ★${step.confidence}`;
        if (step.agent === "validator" && step.result)
          extra = ` ${step.result === "sufficient" ? "✓" : "✗"}`;
        return (
          <span key={i} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            {i > 0 && <span style={{ color: "#475569", fontSize: "11px" }}>→</span>}
            <span style={{
              background: cfg.bg,
              color: cfg.color,
              border: `1px solid ${cfg.color}33`,
              borderRadius: "6px",
              padding: "2px 8px",
              fontSize: "11px",
              fontWeight: 500,
              fontFamily: "monospace",
            }}>
              {cfg.label}{extra}
            </span>
          </span>
        );
      })}
    </div>
  );
}

// ── TypingIndicator ────────────────────────────────────────────────────────
function TypingIndicator({ agents }: { agents: string[] }) {
  return (
    <div style={{ display: "flex", gap: "12px", alignItems: "flex-start", marginBottom: "20px" }}>
      <div style={{
        width: "32px", height: "32px", borderRadius: "10px", flexShrink: 0, marginTop: "4px",
        background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
        display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px",
      }}>🧠</div>
      <div style={{
        background: "#1a1f2e", border: "1px solid #2d3748", borderRadius: "14px",
        padding: "14px 18px", display: "flex", flexDirection: "column", gap: "8px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span style={{ marginLeft: "6px", fontSize: "12px", color: "#64748b" }}>
            {agents.length > 0 ? `Running ${agents[agents.length - 1]} agent…` : "Thinking…"}
          </span>
        </div>
        {agents.length > 0 && (
          <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
            {agents.map((a, i) => {
              const cfg = AGENT_CONFIG[a] ?? { color: "#94a3b8", bg: "rgba(148,163,184,0.1)", label: a };
              return (
                <span key={i} style={{
                  background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}33`,
                  borderRadius: "5px", padding: "1px 7px", fontSize: "10px", fontFamily: "monospace",
                }}>
                  {cfg.label} ✓
                </span>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ── MessageBubble ──────────────────────────────────────────────────────────
function MessageBubble({ msg, onClarify }: { msg: ChatMessage; onClarify?: (text: string) => void }) {
  const [clarifyInput, setClarifyInput] = useState("");

  if (msg.role === "user") {
    return (
      <div className="message-enter" style={{ display: "flex", justifyContent: "flex-end", marginBottom: "16px" }}>
        <div style={{
          background: "linear-gradient(135deg,#4f46e5,#7c3aed)",
          color: "#fff", borderRadius: "16px 16px 4px 16px",
          padding: "12px 16px", maxWidth: "70%", fontSize: "14px", lineHeight: "1.6",
        }}>
          {msg.content}
        </div>
      </div>
    );
  }

  if (msg.role === "clarification") {
    return (
      <div className="message-enter" style={{ display: "flex", gap: "12px", alignItems: "flex-start", marginBottom: "20px" }}>
        <div style={{
          width: "32px", height: "32px", borderRadius: "10px", flexShrink: 0, marginTop: "4px",
          background: "rgba(245,158,11,0.2)", border: "1px solid rgba(245,158,11,0.4)",
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px",
        }}>⚡</div>
        <div style={{
          background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.3)",
          borderRadius: "14px", padding: "16px 18px", maxWidth: "75%",
        }}>
          <p style={{ fontSize: "12px", color: "#fbbf24", fontWeight: 600, marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Clarification Needed
          </p>
          <p style={{ fontSize: "14px", color: "#e2e8f0", lineHeight: "1.6", marginBottom: "12px" }}>
            {msg.content}
          </p>
          <form
            onSubmit={(e: FormEvent) => { e.preventDefault(); if (clarifyInput.trim() && onClarify) { onClarify(clarifyInput); setClarifyInput(""); }}}
            style={{ display: "flex", gap: "8px" }}
          >
            <input
              autoFocus
              value={clarifyInput}
              onChange={e => setClarifyInput(e.target.value)}
              placeholder="Type your answer…"
              style={{
                flex: 1, background: "rgba(0,0,0,0.3)", border: "1px solid rgba(245,158,11,0.4)",
                borderRadius: "8px", padding: "8px 12px", color: "#e2e8f0", fontSize: "13px", outline: "none",
              }}
            />
            <button type="submit" style={{
              background: "rgba(245,158,11,0.2)", border: "1px solid rgba(245,158,11,0.5)",
              color: "#fbbf24", borderRadius: "8px", padding: "8px 14px", fontSize: "13px",
              cursor: "pointer", fontWeight: 600,
            }}>
              Send
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="message-enter" style={{ display: "flex", gap: "12px", alignItems: "flex-start", marginBottom: "20px" }}>
      <div style={{
        width: "32px", height: "32px", borderRadius: "10px", flexShrink: 0, marginTop: "4px",
        background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
        display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px",
      }}>🧠</div>
      <div style={{
        background: "#1a1f2e", border: "1px solid #2d3748", borderRadius: "4px 16px 16px 16px",
        padding: "16px 18px", maxWidth: "75%",
      }}>
        <p style={{ fontSize: "14px", lineHeight: "1.75", color: "#e2e8f0", whiteSpace: "pre-wrap" }}>
          {msg.content}
        </p>
        {msg.trace && msg.trace.length > 0 && <AgentTrace steps={msg.trace} />}
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────
export default function Page() {
  const [messages, setMessages] = useState<ChatMessage[]>([{
    id: "welcome",
    role: "assistant",
    content: "Hello! I am a multi-agent research assistant. Ask me about any company — try Apple, Tesla, or anything else. I will search the web and synthesize findings for you.",
  }]);
  const [threadId] = useState(() => crypto.randomUUID());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [liveAgents, setLiveAgents] = useState<string[]>([]);
  const [awaitingClarification, setAwaitingClarification] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleResponse = (data: { type: string; content?: string; trace?: AgentStep[]; prompt?: string; agents_run?: { agent: string }[] }) => {
    setLoading(false);
    setLiveAgents([]);
    if (data.type === "clarification_needed") {
      setAwaitingClarification(true);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: "clarification",
        content: data.prompt ?? "Could you clarify your query?",
      }]);
    } else {
      setAwaitingClarification(false);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: "assistant",
        content: data.content ?? "",
        trace: data.trace ?? [],
      }]);
    }
  };

  const send = async (text: string, isClarification = false) => {
    if (!text.trim() || loading) return;
    setMessages(prev => [...prev, { id: Date.now().toString(), role: "user", content: text }]);
    setInput("");
    setLoading(true);
    setLiveAgents([]);

    const endpoint = isClarification ? "/api/clarify" : "/api/chat";
    const body = isClarification
      ? { clarification: text, thread_id: threadId }
      : { message: text, thread_id: threadId };

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();

      // Reconstruct live agent steps from trace for animation
      if (data.trace) {
        const steps: string[] = data.trace.map((s: AgentStep) => s.agent);
        let i = 0;
        const tick = () => {
          if (i < steps.length) { setLiveAgents(steps.slice(0, i + 1)); i++; setTimeout(tick, 300); }
          else handleResponse(data);
        };
        tick();
      } else {
        handleResponse(data);
      }
    } catch {
      setLoading(false);
      setLiveAgents([]);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: "assistant",
        content: "Error connecting to backend. Make sure the Python server is running on port 8000.",
      }]);
    }
  };

  const newChat = () => {
    setMessages([{
      id: "welcome",
      role: "assistant",
      content: "Hello! I am a multi-agent research assistant. Ask me about any company — try Apple, Tesla, or anything else.",
    }]);
    setAwaitingClarification(false);
    setLiveAgents([]);
    inputRef.current?.focus();
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0f1117" }}>
      {/* Header */}
      <header style={{
        background: "#1a1f2e", borderBottom: "1px solid #2d3748",
        padding: "0 24px", height: "60px",
        display: "flex", alignItems: "center", gap: "12px", flexShrink: 0,
      }}>
        <div style={{
          width: "32px", height: "32px", borderRadius: "9px",
          background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: "16px",
        }}>🧠</div>
        <span style={{ fontWeight: 700, fontSize: "15px", color: "#f1f5f9" }}>Research Assistant</span>
        <span style={{
          background: "rgba(99,102,241,0.15)", color: "#818cf8",
          border: "1px solid rgba(99,102,241,0.3)", borderRadius: "6px",
          fontSize: "11px", padding: "2px 8px", fontFamily: "monospace",
        }}>turing-interview</span>
        <div style={{ flex: 1 }} />
        <a
          href="https://smith.langchain.com"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: "rgba(16,185,129,0.12)", color: "#34d399",
            border: "1px solid rgba(16,185,129,0.3)", borderRadius: "6px",
            fontSize: "11px", padding: "4px 10px", textDecoration: "none",
            fontWeight: 500, display: "flex", alignItems: "center", gap: "4px",
          }}
        >
          <span>●</span> LangSmith
        </a>
        <button
          onClick={newChat}
          style={{
            background: "#252d3d", border: "1px solid #374151", color: "#94a3b8",
            borderRadius: "8px", padding: "6px 14px", cursor: "pointer", fontSize: "12px", fontWeight: 500,
          }}
        >
          + New Chat
        </button>
      </header>

      {/* Messages */}
      <main style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
        <div style={{ maxWidth: "780px", margin: "0 auto" }}>
          {messages.map(msg => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              onClarify={text => send(text, true)}
            />
          ))}
          {loading && <TypingIndicator agents={liveAgents} />}
          <div ref={bottomRef} />
        </div>
      </main>

      {/* Suggested prompts */}
      {messages.length === 1 && !loading && (
        <div style={{ padding: "0 24px 16px", maxWidth: "780px", margin: "0 auto", width: "100%" }}>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "center" }}>
            {["What's happening with Apple?", "Tell me about Tesla", "How is Microsoft doing?", "Tell me about a tech company"].map(p => (
              <button
                key={p}
                onClick={() => send(p)}
                style={{
                  background: "#1a1f2e", border: "1px solid #2d3748", color: "#94a3b8",
                  borderRadius: "20px", padding: "7px 14px", cursor: "pointer", fontSize: "12px",
                  transition: "all 0.15s",
                }}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input bar */}
      <footer style={{
        background: "#1a1f2e", borderTop: "1px solid #2d3748",
        padding: "16px 24px", flexShrink: 0,
      }}>
        <div style={{ maxWidth: "780px", margin: "0 auto" }}>
          <form
            onSubmit={(e: FormEvent) => { e.preventDefault(); if (!awaitingClarification) send(input); }}
            style={{ display: "flex", gap: "10px" }}
          >
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={awaitingClarification ? "Clarification is shown above — use that form" : "Ask about any company…"}
              disabled={loading || awaitingClarification}
              style={{
                flex: 1, background: "#0f1117", border: "1px solid #374151",
                borderRadius: "10px", padding: "12px 16px", color: "#e2e8f0",
                fontSize: "14px", outline: "none",
                opacity: awaitingClarification ? 0.4 : 1,
              }}
            />
            <button
              type="submit"
              disabled={loading || !input.trim() || awaitingClarification}
              style={{
                background: loading || !input.trim() ? "#1e293b" : "linear-gradient(135deg,#4f46e5,#7c3aed)",
                color: loading || !input.trim() ? "#475569" : "#fff",
                border: "none", borderRadius: "10px", padding: "12px 20px",
                cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                fontSize: "14px", fontWeight: 600, transition: "all 0.15s",
              }}
            >
              {loading ? "…" : "Send ▶"}
            </button>
          </form>
          <p style={{ textAlign: "center", fontSize: "11px", color: "#334155", marginTop: "8px" }}>
            Powered by LangGraph · Tavily · OpenRouter · Traces in LangSmith
          </p>
        </div>
      </footer>
    </div>
  );
}
