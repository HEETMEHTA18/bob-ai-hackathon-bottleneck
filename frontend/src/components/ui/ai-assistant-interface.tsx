"use client";

import type React from "react";
import { useState, useRef, useEffect, useCallback } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ArrowUp,
  Search,
  BrainCircuit,
  Loader2,
  Sparkles,
  Zap,
  BarChart3,
  ShieldAlert,
  BatteryCharging,
  CloudSun,
} from "lucide-react";
import { motion } from "framer-motion";
import {
  createChatSession,
  listChatSessions,
  getChatSession,
  sendChatMessage,
  deleteChatSession,
  type ChatSession,
  type ChatMessage,
} from "@/api/client";

// ─── Message Bubble ──────────────────────────────────────────
function MessageBubble({ msg, isLast }: { msg: ChatMessage; isLast: boolean }) {
  const isUser = msg.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
    >
      <div className={`flex max-w-[85%] ${isUser ? "flex-row-reverse" : "flex-row"} gap-3`}>
        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-[#1a73e8] text-white" : "bg-[#e8f0fe] text-[#1a73e8]"
        }`}>
          {isUser ? <span className="text-xs font-bold">You</span> : <Sparkles className="h-4 w-4" />}
        </div>
        <div className={`rounded-2xl px-4 py-3 text-[15px] leading-relaxed ${
          isUser
            ? "bg-[#1a73e8] text-white rounded-br-md"
            : "bg-white text-[#202124] rounded-bl-md border border-[#e0e0e0] shadow-sm"
        }`}>
          {isUser ? (
            <span className="whitespace-pre-wrap">{msg.content}</span>
          ) : (
            <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-headings:text-[#202124] prose-p:my-1.5 prose-table:my-2 prose-th:bg-[#f8f9fa] prose-th:px-3 prose-th:py-1.5 prose-th:text-left prose-th:text-xs prose-th:font-semibold prose-th:text-[#5f6368] prose-td:px-3 prose-td:py-1.5 prose-td:text-sm prose-code:bg-[#f1f3f4] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-[#c7254e] prose-code:before:content-none prose-code:after:content-none prose-strong:text-[#202124] prose-a:text-[#1a73e8] prose-blockquote:border-[#1a73e8] prose-blockquote:text-[#5f6368]">
              <Markdown remarkPlugins={[remarkGfm]}>{msg.content}</Markdown>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// ─── Thinking Indicator ──────────────────────────────────────
function ThinkingIndicator() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start mb-4">
      <div className="flex gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#e8f0fe] text-[#1a73e8]">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="rounded-2xl rounded-bl-md border border-[#e0e0e0] bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-[#1a73e8]" />
            <span className="text-sm text-[#5f6368]">Thinking...</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Welcome Screen ──────────────────────────────────────────
function WelcomeScreen({ onSend }: { onSend: (msg: string) => void }) {
  const suggestions = [
    { icon: BarChart3, label: "What's my forecast?", color: "text-[#1a73e8]" },
    { icon: ShieldAlert, label: "Check curtailment risk", color: "text-[#e8710a]" },
    { icon: BatteryCharging, label: "Optimize battery dispatch", color: "text-[#0d904f]" },
    { icon: CloudSun, label: "Weather conditions today", color: "text-[#007b83]" },
  ];
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="mb-8 flex flex-col items-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1a73e8] text-white shadow-lg shadow-[#1a73e8]/25">
          <Zap className="h-6 w-6" />
        </div>
        <h1 className="text-[28px] font-bold text-[#202124]">Bottleneck AI Advisor</h1>
        <p className="mt-1 text-[15px] text-[#5f6368]">Power Outage Prediction Intelligence</p>
      </motion.div>
      <div className="grid w-full max-w-lg grid-cols-2 gap-3">
        {suggestions.map((s) => (
          <button
            key={s.label}
            onClick={() => onSend(s.label)}
            className="flex items-center gap-2.5 rounded-xl border border-[#e0e0e0] bg-white p-3.5 text-left text-sm text-[#202124] shadow-sm transition-all hover:border-[#dadce0] hover:bg-[#f8f9fa] hover:shadow-md cursor-pointer"
          >
            <s.icon className={`h-4 w-4 ${s.color}`} />
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Smart Response Generator (fallback) ───
function getSmartResponse(query: string): string {
  const q = query.toLowerCase();
  const has = (...words: string[]) => new RegExp(`\\b(${words.join("|")})\\b`).test(q);
  if (has("forecast", "p50", "p10", "p90", "generation", "output", "power", "solar", "peak"))
    return "Forecast data requires backend connection. Please check the server status.";
  if (has("risk", "curtail"))
    return "Curtailment risk analysis requires live weather data.";
  if (has("battery", "dispatch"))
    return "Battery dispatch optimization requires live data.";
  if (has("weather", "temperature", "wind", "ghi", "cloud"))
    return "Live weather requires backend connection.";
  if (has("hello", "hey", "help"))
    return "Hi! I'm your Bottleneck advisor. I can help with grid failure prediction, risk ranking, crew positioning, and maintenance planning. What would you like to explore?";
  return `I can help with forecasts, risk, battery, weather, or model accuracy. Could you rephrase your question?`;
}

// ─── Main Component ──────────────────────────────────────────
export function AIAssistantInterface({ embed = false }: { embed?: boolean }) {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [thinking, setThinking] = useState(false);
  const [searchEnabled, setSearchEnabled] = useState(false);
  const [deepResearchEnabled, setDeepResearchEnabled] = useState(false);
  const [reasonEnabled, setReasonEnabled] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const hasMessages = messages.length > 0;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  useEffect(() => {
    if (!hasMessages) inputRef.current?.focus();
  }, [hasMessages]);

  const createNewSession = useCallback(async () => {
    try {
      const r = await createChatSession();
      setActiveSessionId(r.data.id);
      setMessages([]);
      window.history.replaceState(null, "", `/ai?session=${r.data.id}`);
    } catch {
      const id = Math.random().toString(36).slice(2, 10);
      setActiveSessionId(id);
      setMessages([]);
      window.history.replaceState(null, "", `/ai?session=${id}`);
    }
  }, []);

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || thinking) return;

    let sessionId = activeSessionId;
    if (!sessionId) {
      try {
        const r = await createChatSession(trimmed.slice(0, 60));
        sessionId = r.data.id;
        setActiveSessionId(sessionId);
        window.history.replaceState(null, "", `/ai?session=${sessionId}`);
      } catch {
        sessionId = Math.random().toString(36).slice(2, 10);
        setActiveSessionId(sessionId);
      }
    }

    const userMsg: ChatMessage = { role: "user", content: trimmed, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setThinking(true);

    try {
      const r = await sendChatMessage(sessionId, trimmed, {
        search: searchEnabled,
        deep_research: deepResearchEnabled,
        reason: reasonEnabled,
        site_id: (window as any).__GRIDSHIELD_SITE__?.id,
      });
      setThinking(false);
      setMessages((prev) => [...prev, r.data.message]);
    } catch {
      await new Promise((res) => setTimeout(res, 800 + Math.random() * 600));
      setThinking(false);
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: getSmartResponse(trimmed),
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }

    setSearchEnabled(false);
    setDeepResearchEnabled(false);
    setReasonEnabled(false);
  }, [activeSessionId, thinking, searchEnabled, deepResearchEnabled, reasonEnabled]);

  return (
    <div className="flex h-full flex-col bg-white">
      {!hasMessages ? (
        <WelcomeScreen onSend={sendMessage} />
      ) : (
        <div className="flex-1 overflow-y-auto px-4 pt-6 pb-4">
          <div className="mx-auto max-w-3xl">
            {messages.map((m, i) => (
              <MessageBubble key={i} msg={m} isLast={i === messages.length - 1} />
            ))}
            {thinking && <ThinkingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      <div className="border-t border-[#e0e0e0] bg-white px-4 py-3">
        <div className="mx-auto max-w-3xl">
          <div className="mb-2 flex items-center gap-2">
            <button
              onClick={() => setSearchEnabled(!searchEnabled)}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors cursor-pointer ${
                searchEnabled ? "bg-[#e8f0fe] text-[#1a73e8]" : "bg-[#f1f3f4] text-[#5f6368] hover:bg-[#e8eaed]"
              }`}
            >
              <Search className="h-3 w-3" /> Search
            </button>
            <button
              onClick={() => setDeepResearchEnabled(!deepResearchEnabled)}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors cursor-pointer ${
                deepResearchEnabled ? "bg-[#e8f0fe] text-[#1a73e8]" : "bg-[#f1f3f4] text-[#5f6368] hover:bg-[#e8eaed]"
              }`}
            >
              <BrainCircuit className="h-3 w-3" /> Deep Research
            </button>
            <button
              onClick={() => setReasonEnabled(!reasonEnabled)}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors cursor-pointer ${
                reasonEnabled ? "bg-[#e8f0fe] text-[#1a73e8]" : "bg-[#f1f3f4] text-[#5f6368] hover:bg-[#e8eaed]"
              }`}
            >
              <Sparkles className="h-3 w-3" /> Reason
            </button>
          </div>
          <div className="flex items-end gap-2 rounded-2xl border border-[#e0e0e0] bg-white px-4 py-3 shadow-sm focus-within:border-[#1a73e8] focus-within:ring-2 focus-within:ring-[#e8f0fe] transition-all">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(inputValue);
                }
              }}
              placeholder="Ask about forecasts, risk, battery, weather..."
              rows={1}
              className="min-h-[40px] max-h-32 flex-1 resize-none border-0 bg-transparent py-1 text-[15px] text-[#202124] placeholder:text-[#9aa0a6] focus:outline-none"
            />
            <button
              onClick={() => sendMessage(inputValue)}
              disabled={!inputValue.trim() || thinking}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#1a73e8] text-white transition-all hover:bg-[#1557b0] disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
            >
              {thinking ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
            </button>
          </div>
          <p className="mt-2 text-center text-[11px] text-[#9aa0a6]">
            Bottleneck AI · Power outage prediction · Data from Open-Meteo
          </p>
        </div>
      </div>
    </div>
  );
}
