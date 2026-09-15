import * as React from "react"
import {
  AlertTriangle,
  ArrowRight,
  BarChart2,
  Bot,
  Brain,
  CheckCircle2,
  Compass,
  Cpu,
  Database,
  Eye,
  Globe,
  HardHat,
  Layers,
  Lock,
  Mail,
  MapPin,
  Menu,
  Radio,
  Search,
  Shield,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  Wind,
  X,
  Zap,
  Activity,
  Bell,
  GitBranch,
} from "lucide-react"

import { Button } from "@/components/ui/button"

interface LandingPageProps {
  onLogin: (email: string, password: string) => Promise<void>
  onSignup: (email: string, password: string, name: string) => Promise<void>
}

const problemStats = [
  { value: "1.4B", label: "People served by India's grid" },
  { value: "5–8h",  label: "Avg outage duration (urban)" },
  { value: "#1",    label: "Transformer failures cause outages" },
  { value: "24–72h",label: "Prediction horizon needed" },
]

const workflowSteps = [
  {
    icon: Search,
    step: "01",
    title: "PREDICT",
    desc: "XGBoost models forecast 24 h / 72 h failure probability for every transformer, feeder, and breaker using telemetry, weather, and incident history.",
    color: "#2563eb",
    bg: "#eff6ff",
    border: "#bfdbfe",
  },
  {
    icon: Brain,
    step: "02",
    title: "EXPLAIN",
    desc: "Every risk score surfaces the exact drivers — anomalous temperature, vibration spikes, partial discharge, storm exposure, and prior incidents.",
    color: "#7c3aed",
    bg: "#f5f3ff",
    border: "#ddd6fe",
  },
  {
    icon: Target,
    step: "03",
    title: "PRIORITIZE",
    desc: "Composite risk score (0–100) weights failure probability × grid impact × weather × criticality × (1−redundancy). High-impact assets rank first.",
    color: "#d97706",
    bg: "#fffbeb",
    border: "#fde68a",
  },
  {
    icon: Compass,
    step: "04",
    title: "POSITION",
    desc: "Crew planner matches transformer specialists, line crews, and substation teams to at-risk assets by region, specialty, and availability — before outages.",
    color: "#16a34a",
    bg: "#f0fdf4",
    border: "#bbf7d0",
  },
]

const differentiators = [
  {
    icon: BarChart2,
    title: "Impact-Aware Risk, Not Just Probability",
    desc: "A medium-probability failure on a transformer serving 8,420 customers and 3 hospitals outranks a high-probability fault on a redundant switch. Risk = f(probability × impact × weather × criticality × (1−redundancy)).",
    highlight: "Grid impact weighted equally with failure probability",
    color: "#2563eb",
  },
  {
    icon: Eye,
    title: "Explainability at Every Layer",
    desc: "No black boxes. For every high-risk asset: which telemetry readings are anomalous, weather contribution, customers/critical facilities at risk, recommended action with reasoning, assigned crew and specialty.",
    highlight: "Every number has a traceable 'why'",
    color: "#7c3aed",
  },
  {
    icon: Cpu,
    title: "Clean ML Integration Seam",
    desc: "The ML layer lives behind a stable FailurePredictor interface. Swap MockFailurePredictor → RealFailurePredictor in one file. Zero changes to risk engine, planners, or frontend.",
    highlight: "Drop-in replacement for any future ML model",
    color: "#0891b2",
  },
  {
    icon: Layers,
    title: "Scenario Simulation",
    desc: "Run what-if scenarios: Severe Storm, Heatwave, Asset Degradation. Full pipeline re-runs coherently — predictions → risk → maintenance → crew — in under 1 second.",
    highlight: "Before/after risk comparison in one view",
    color: "#16a34a",
  },
]

const demoScenario = [
  { step: 1, title: "Command Center",    desc: "Open dashboard → TR-1042 ranked #1 critical (Risk 94/100, Health 38/100)", phase: "predict" },
  { step: 2, title: "Asset Intelligence",desc: "Drill down → 8,420 customers at risk, 3 critical facilities, high temp + vibration + overheating incident + severe weather", phase: "predict" },
  { step: 3, title: "Risk Breakdown",    desc: "See exact drivers: p24=0.72, impact=0.91, weather=0.84, criticality=0.95, redundancy=0.15 → composite 94", phase: "explain" },
  { step: 4, title: "Maintenance Planner",desc: "TR-1042 Priority #1: Inspect within 6 h, replace bushing, thermal scan. Reason: temp anomaly + PD spike + storm exposure", phase: "prioritize" },
  { step: 5, title: "Crew Planner",      desc: "CREW-07 (transformer specialist, Region 3) pre-positioned 2.3 km from asset. ETA 12 min. Backup: CREW-12", phase: "position" },
  { step: 6, title: "Scenario Simulator",desc: "Run Severe Storm → TR-1042 risk 94→98, CREW-07 reassigned, TR-2108 enters top 5. Full pipeline updates in <1 s", phase: "position" },
  { step: 7, title: "AI Copilot",        desc: "Ask: 'Why is TR-1042 critical?' → Grounded answer citing telemetry, weather, incidents, grid impact. No hallucination.", phase: "explain" },
]

const phaseColor: Record<string, { color: string; bg: string }> = {
  predict:   { color: "#2563eb", bg: "#2563eb" },
  explain:   { color: "#7c3aed", bg: "#7c3aed" },
  prioritize:{ color: "#d97706", bg: "#d97706" },
  position:  { color: "#16a34a", bg: "#16a34a" },
}

const techStack = [
  { icon: Zap,       label: "FastAPI",         desc: "Python backend",      color: "#2563eb" },
  { icon: Cpu,       label: "XGBoost",         desc: "Failure prediction",  color: "#7c3aed" },
  { icon: Globe,     label: "Open-Meteo",      desc: "Live weather",        color: "#0891b2" },
  { icon: Bot,       label: "Gemini",          desc: "AI Copilot",          color: "#16a34a" },
  { icon: Database,  label: "SQLite / PG",     desc: "Asset data",          color: "#d97706" },
  { icon: Activity,  label: "React 18",        desc: "TypeScript UI",       color: "#dc2626" },
  { icon: Shield,    label: "Pydantic",        desc: "Type-safe contracts", color: "#7c3aed" },
  { icon: HardHat,   label: "Docker",          desc: "Containerized",       color: "#374151" },
]

const kpis = [
  { value: "30",    label: "Assets Monitored" },
  { value: "24 h",  label: "Prediction Horizon" },
  { value: "0–100", label: "Risk Score" },
  { value: "<1 s",  label: "Scenario Re-compute" },
  { value: "100%",  label: "Offline Ready" },
  { value: "0",     label: "Credentials Needed" },
]

export function LandingPage({ onLogin, onSignup }: LandingPageProps) {
  const [authOpen, setAuthOpen] = React.useState(false)
  const [authMode, setAuthMode] = React.useState<"login" | "signup">("login")
  const [demoFill, setDemoFill] = React.useState(false)
  const [mobileNav, setMobileNav] = React.useState(false)
  const [scrollY, setScrollY] = React.useState(0)

  React.useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY)
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const openAuth = (mode: "login" | "signup") => {
    setAuthMode(mode)
    setAuthOpen(true)
  }

  const inputCls =
    "flex h-12 w-full items-center gap-3 rounded-xl border bg-white px-4 focus-within:border-blue-500/60 focus-within:ring-2 focus-within:ring-blue-500/10"
  const inputEl =
    "h-full w-full bg-transparent text-sm text-zinc-800 outline-none placeholder:text-zinc-400"

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" })
    setMobileNav(false)
  }

  return (
    <div className="h-screen overflow-y-auto bg-[#f5f5f5] text-zinc-800 antialiased">

      {/* ── Nav ─────────────────────────────────────────────── */}
      <header
        className={`sticky top-0 z-40 border-b border-[#d4d4d8] bg-[#f5f5f5]/90 backdrop-blur-xl transition-all duration-200 ${
          scrollY > 20 ? "shadow-sm" : ""
        }`}
      >
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          {/* Logo */}
          <a href="#top" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
              <Zap className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-zinc-900">Bottleneck</div>
              <div className="text-[10px] font-medium text-zinc-400 leading-tight">Power Outage Prediction</div>
            </div>
          </a>

          <nav className="hidden items-center gap-7 text-sm text-zinc-500 md:flex">
            {["Problem","Solution","Differentiators","Demo","Tech Stack"].map(label => (
              <a
                key={label}
                href={`#${label.toLowerCase().replace(" ", "")}`}
                className="transition-colors hover:text-zinc-900"
                onClick={(e) => { e.preventDefault(); scrollTo(label.toLowerCase().replace(" ","")) }}
              >{label}</a>
            ))}
          </nav>

          <div className="hidden items-center gap-3 md:flex">
            <Button variant="ghost" className="text-zinc-600 hover:bg-black/5 hover:text-zinc-900" onClick={() => openAuth("login")}>Sign in</Button>
            <Button className="rounded-lg bg-blue-600 text-white shadow-sm shadow-blue-600/20 hover:bg-blue-700" onClick={() => openAuth("signup")}>
              Get started <ArrowRight className="h-4 w-4" />
            </Button>
          </div>

          <button className="text-zinc-600 md:hidden" onClick={() => setMobileNav(!mobileNav)} aria-label="Menu">
            {mobileNav ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {mobileNav && (
          <div className="border-t border-[#d4d4d8] bg-[#f5f5f5] px-6 py-4 md:hidden animate-fadeIn">
            <div className="flex flex-col gap-1 text-sm text-zinc-600">
              {["problem","solution","differentiators","demo","techstack"].map(id => (
                <a key={id} href={`#${id}`} onClick={() => scrollTo(id)} className="rounded-lg px-3 py-2 capitalize hover:bg-black/5">{id.replace("techstack","Tech Stack")}</a>
              ))}
              <div className="mt-3 grid grid-cols-2 gap-2">
                <Button variant="outline" className="border-zinc-200 text-zinc-700" onClick={() => openAuth("login")}>Sign in</Button>
                <Button className="bg-blue-600 text-white hover:bg-blue-700" onClick={() => openAuth("signup")}>Get started</Button>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* ── Hero ────────────────────────────────────────────── */}
      <section id="top" className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(37,99,235,0.07),transparent)]" />
        </div>

        <div className="relative z-10 mx-auto flex min-h-[86vh] max-w-6xl flex-col items-center justify-center px-6 py-24 text-center">
          {/* Hackathon badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-600/20 bg-white px-4 py-1.5 text-xs font-semibold text-blue-700 shadow-sm animate-fadeIn">
            <Sparkles className="h-3.5 w-3.5" />
            IBM Bob Hackathon 2026 · Track U1 · Team Bottleneck
          </div>

          <h1 className="max-w-3xl text-balance text-4xl font-bold leading-[1.08] tracking-tight text-zinc-900 sm:text-6xl animate-fadeIn" style={{ animationDelay: "80ms" }}>
            Predict grid failures<br />before they happen.
            <span className="block mt-2 bg-gradient-to-r from-blue-600 via-blue-500 to-sky-400 bg-clip-text text-transparent">
              Explain. Prioritize. Position.
            </span>
          </h1>

          <p className="mt-6 max-w-xl text-pretty text-base leading-relaxed text-zinc-500 sm:text-lg animate-fadeIn" style={{ animationDelay: "180ms" }}>
            Bottleneck fuses asset telemetry, weather forecasts, and incident history into
            actionable intelligence — predicting which equipment will fail in the next 24–72 hours,
            explaining why, ranking by grid impact, and pre-positioning crews before outages occur.
          </p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-3 animate-fadeIn" style={{ animationDelay: "260ms" }}>
            <Button
              className="h-12 rounded-xl bg-blue-600 px-7 text-[15px] font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700"
              onClick={() => openAuth("signup")}
            >
              Start exploring <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="h-12 rounded-xl border-zinc-200 bg-white px-7 text-[15px] text-zinc-700 shadow-sm hover:bg-zinc-50"
              onClick={() => scrollTo("demo")}
            >
              See the demo
            </Button>
          </div>

          {/* KPI strip */}
          <div className="mt-16 grid w-full max-w-3xl grid-cols-3 gap-3 sm:grid-cols-6 animate-fadeIn" style={{ animationDelay: "340ms" }}>
            {kpis.map((s) => (
              <div key={s.label} className="rounded-2xl border border-zinc-200 bg-white/80 px-4 py-4 text-center shadow-sm backdrop-blur-sm">
                <div className="text-xl font-bold tabular-nums text-zinc-900" style={{ fontFamily: "ui-monospace, monospace" }}>
                  {s.value}
                </div>
                <div className="mt-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Problem ─────────────────────────────────────────── */}
      <section id="problem" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-12 max-w-2xl animate-fadeIn">
          <p className="mb-3 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-red-600">
            <AlertTriangle className="h-3.5 w-3.5" /> The Problem
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">
            Power grids are aging. Failures are found too late.
          </h2>
          <p className="mt-4 text-zinc-500 text-lg">
            Utility operators manage fleets of transformers, feeders, and breakers that are decades old,
            overloaded, and exposed to increasingly severe weather — with no unified view of risk.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-4 animate-fadeIn" style={{ animationDelay: "80ms" }}>
          {problemStats.map((s) => (
            <div key={s.label} className="rounded-2xl border border-l-4 bg-white p-6 shadow-sm" style={{ borderLeftColor: "#c5221f", borderColor: "#e5e7eb" }}>
              <div className="text-3xl font-bold tabular-nums text-zinc-900" style={{ fontFamily: "ui-monospace, monospace" }}>{s.value}</div>
              <div className="mt-2 text-sm text-zinc-500">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 animate-fadeIn" style={{ animationDelay: "160ms" }}>
          {[
            { icon: Bell,      title: "Reactive Discovery",       desc: "Failures found after the outage starts — not before" },
            { icon: Radio,     title: "Calendar-Driven Maintenance", desc: "Fixed schedules ignore actual asset condition and weather exposure" },
            { icon: MapPin,    title: "Post-Failure Dispatch",    desc: "Crews sent after failure, never pre-positioned for at-risk zones" },
            { icon: Layers,    title: "Siloed Risk Assessment",   desc: "Weather, telemetry, and incidents never combined in one view" },
          ].map((item) => (
            <div key={item.title} className="flex gap-4 rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600">
                <item.icon className="h-5 w-5" />
              </div>
              <div>
                <h4 className="font-semibold text-zinc-900">{item.title}</h4>
                <p className="mt-1 text-sm text-zinc-500">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-10 flex items-start gap-4 rounded-2xl border border-amber-200 bg-amber-50 p-6 animate-fadeIn" style={{ animationDelay: "240ms" }}>
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-bold text-zinc-900">The result: unnecessary outages, delayed restoration, and life-safety risk</h3>
            <p className="mt-1 text-sm text-zinc-600">
              Especially for critical facilities — hospitals, emergency services, water treatment plants —
              where every minute of downtime carries real consequences.
            </p>
          </div>
        </div>
      </section>

      {/* ── Solution / Workflow ────────────────────────────── */}
      <section id="solution" className="border-y border-[#d4d4d8] bg-white">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-14 max-w-2xl animate-fadeIn">
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-600">Solution</p>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">
              PREDICT → EXPLAIN → PRIORITIZE → POSITION
            </h2>
            <p className="mt-4 text-zinc-500 text-lg">
              A complete decision-support loop: from raw sensor data to crew dispatch,
              with full explainability at every step.
            </p>
          </div>

          {/* 4-step cards */}
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 animate-fadeIn" style={{ animationDelay: "80ms" }}>
            {workflowSteps.map((step, i) => (
              <div
                key={step.title}
                className="rounded-2xl border bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
                style={{ borderColor: step.border, borderLeftWidth: 4, borderLeftColor: step.color }}
              >
                <div className="mb-4 flex items-center justify-between">
                  <div
                    className="flex h-12 w-12 items-center justify-center rounded-xl"
                    style={{ background: step.bg, color: step.color }}
                  >
                    <step.icon className="h-6 w-6" />
                  </div>
                  <span
                    className="text-xs font-bold tabular-nums"
                    style={{ color: step.color, fontFamily: "ui-monospace, monospace" }}
                  >
                    {step.step}
                  </span>
                </div>
                <h3 className="text-base font-bold" style={{ color: step.color }}>{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-500">{step.desc}</p>
              </div>
            ))}
          </div>

          {/* Flow connector */}
          <div className="mt-10 flex items-center justify-center gap-0 overflow-x-auto animate-fadeIn" style={{ animationDelay: "200ms" }}>
            {workflowSteps.map((step, i) => (
              <React.Fragment key={step.title}>
                <div className="flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-bold whitespace-nowrap shadow-sm"
                  style={{ borderColor: step.border, background: step.bg, color: step.color }}>
                  <step.icon className="h-3.5 w-3.5" />{step.title}
                </div>
                {i < workflowSteps.length - 1 && (
                  <ArrowRight className="h-4 w-4 shrink-0 text-zinc-300 mx-1" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* ── Differentiators ───────────────────────────────── */}
      <section id="differentiators" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-14 max-w-2xl animate-fadeIn">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-purple-600">Key Differentiators</p>
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">Why Bottleneck is different</h2>
          <p className="mt-4 text-zinc-500">Four architectural choices that make this operational, not academic.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2 animate-fadeIn" style={{ animationDelay: "80ms" }}>
          {differentiators.map((d) => (
            <div
              key={d.title}
              className="group relative overflow-hidden rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex gap-4">
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
                  style={{ background: `${d.color}15`, color: d.color }}
                >
                  <d.icon className="h-6 w-6" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-[15px] font-semibold text-zinc-900">{d.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-zinc-500">{d.desc}</p>
                  <div
                    className="mt-4 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium"
                    style={{ background: `${d.color}12`, color: d.color }}
                  >
                    <Sparkles className="h-3 w-3" />{d.highlight}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Demo Scenario ─────────────────────────────────── */}
      <section id="demo" className="border-y border-[#d4d4d8] bg-white">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-14 max-w-2xl animate-fadeIn">
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-green-600">Demo Scenario</p>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">
              The story we demonstrate end-to-end
            </h2>
            <p className="mt-4 text-zinc-500">
              A storm approaches while transformer TR-1042 develops abnormal temperature, vibration,
              and partial discharge. Watch the full PREDICT → POSITION loop execute.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 animate-fadeIn" style={{ animationDelay: "80ms" }}>
            {demoScenario.map((item) => {
              const pc = phaseColor[item.phase]
              return (
                <div
                  key={item.step}
                  className="relative rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
                  style={{ borderTopWidth: 3, borderTopColor: pc.bg }}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <div
                      className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white shadow-sm"
                      style={{ background: pc.bg }}
                    >
                      {item.step}
                    </div>
                    <span
                      className="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide"
                      style={{ background: `${pc.bg}18`, color: pc.bg }}
                    >
                      {item.phase}
                    </span>
                  </div>
                  <h4 className="font-semibold text-zinc-900 text-sm">{item.title}</h4>
                  <p className="mt-1.5 text-xs leading-relaxed text-zinc-500">{item.desc}</p>
                </div>
              )
            })}
          </div>

          <div className="mt-10 flex items-start gap-4 rounded-2xl bg-gradient-to-r from-blue-600 via-blue-700 to-blue-900 p-6 text-white animate-fadeIn" style={{ animationDelay: "200ms" }}>
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/20">
              <CheckCircle2 className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-lg">No external credentials required</h3>
              <p className="mt-1 text-blue-100 text-sm">
                The full demo runs offline with deterministic synthetic data. 30 assets, seeded predictions,
                live weather fallback, and rule-based AI copilot — all reproducible, zero setup.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Tech Stack ────────────────────────────────────── */}
      <section id="techstack" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-14 max-w-2xl animate-fadeIn">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-zinc-500">Technology</p>
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">Built on solid foundations</h2>
          <p className="mt-4 text-zinc-500">Production-grade stack with graceful fallbacks — runs fully offline, no keys required.</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 animate-fadeIn" style={{ animationDelay: "60ms" }}>
          {techStack.map((t) => (
            <div
              key={t.label}
              className="rounded-2xl border border-zinc-200 bg-white p-5 text-center shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
            >
              <div
                className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl"
                style={{ background: `${t.color}12`, color: t.color }}
              >
                <t.icon className="h-6 w-6" />
              </div>
              <h4 className="font-semibold text-zinc-900 text-sm">{t.label}</h4>
              <p className="mt-1 text-xs text-zinc-500">{t.desc}</p>
            </div>
          ))}
        </div>

        {/* Architecture block */}
        <div className="mt-12 animate-fadeIn" style={{ animationDelay: "160ms" }}>
          <h3 className="mb-5 text-center text-xl font-bold text-zinc-900">Architecture at a glance</h3>
          <div className="rounded-2xl border border-zinc-200 bg-zinc-950 p-6 overflow-x-auto shadow-sm">
            <pre className="text-sm leading-relaxed text-zinc-300" style={{ fontFamily: "ui-monospace, monospace", whiteSpace: "pre" }}>
{`  Asset Telemetry  +  Incident History  +  Weather (Open-Meteo / mock)
                           ↓
         ┌─────────────────────────────────────┐
         │   XGBoostPredictor  (or Mock)        │  ← swap in one file
         │   FailurePrediction contract         │  ← stable boundary
         └─────────────────────────────────────┘
                           ↓
          Grid Impact Engine  +  Risk Engine
                           ↓
              Risk Ranking  (composite 0–100)
                     ↙              ↘
    Maintenance Planner       Crew Pre-Positioning
                     ↘              ↙
               Bottleneck Command Center  (React 18 + TypeScript)`}
            </pre>
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 py-24 animate-fadeIn">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900 px-8 py-16 text-center shadow-xl shadow-blue-600/20">
          <div className="absolute inset-0 bg-[radial-gradient(60%_80%_at_50%_0%,rgba(255,255,255,0.15),transparent)]" />
          <div className="relative z-10 max-w-2xl mx-auto">
            <h2 className="mx-auto max-w-xl text-balance text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Your first risk ranking in under five minutes.
            </h2>
            <p className="mx-auto mt-4 max-w-md text-blue-100 text-[15px]">
              Create an account, explore the Command Center, and trace TR-1042 through
              the full PREDICT → EXPLAIN → PRIORITIZE → POSITION loop.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Button
                className="h-12 rounded-xl bg-white px-8 text-[15px] font-semibold text-blue-700 shadow-lg hover:bg-blue-50"
                onClick={() => openAuth("signup")}
              >
                Start for free <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="h-12 rounded-xl border-white/30 bg-transparent px-8 text-[15px] font-medium text-white hover:bg-white/10"
                onClick={() => scrollTo("demo")}
              >
                View demo walkthrough
              </Button>
            </div>
            <p className="mt-5 text-xs text-blue-200/60">
              Demo access available — click &ldquo;Sign In&rdquo; for credentials.
            </p>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="border-t border-[#d4d4d8]">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-10 text-sm text-zinc-400 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-white">
              <Zap className="h-3.5 w-3.5" />
            </div>
            <span className="font-semibold text-zinc-700">Bottleneck</span>
            <span className="text-zinc-300">·</span>
            <span className="text-xs text-zinc-400">IBM Bob Hackathon 2026 · Track U1</span>
          </div>
          <div className="flex items-center gap-6 text-xs">
            {["problem","solution","differentiators","demo","techstack"].map(id => (
              <a key={id} href={`#${id}`} className="capitalize hover:text-zinc-800"
                onClick={e => { e.preventDefault(); scrollTo(id) }}>
                {id === "techstack" ? "Tech Stack" : id}
              </a>
            ))}
          </div>
          <div className="text-xs text-zinc-400">PREDICT → EXPLAIN → PRIORITIZE → POSITION</div>
        </div>
      </footer>

      {/* ── Auth modal ──────────────────────────────────────── */}
      {authOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4 backdrop-blur-sm animate-fadeIn"
          onClick={() => setAuthOpen(false)}
        >
          <div
            className="animate-fadeIn w-full max-w-md rounded-3xl border border-zinc-200 bg-white p-8 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-7 flex items-start justify-between">
              <div>
                <h3 className="text-xl font-bold tracking-tight text-zinc-900">
                  {authMode === "login" ? "Welcome back" : "Create your account"}
                </h3>
                <p className="mt-1 text-sm text-zinc-400">
                  {authMode === "login"
                    ? "Sign in to your Bottleneck workspace."
                    : "Start predicting outages in minutes — no card needed."}
                </p>
              </div>
              <button
                onClick={() => setAuthOpen(false)}
                className="rounded-lg p-1.5 text-zinc-400 hover:bg-black/5 hover:text-zinc-800"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {authMode === "login" && (
              <div className="mb-5 rounded-xl border border-blue-600/15 bg-blue-50 px-4 py-3 text-xs text-blue-700">
                <div className="mb-2 font-semibold">Quick Demo Access</div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-blue-600/80">
                    Use the demo account to explore the application.
                  </span>
                  <button
                    type="button"
                    className="shrink-0 rounded-lg bg-blue-600 px-3 py-1.5 text-[11px] font-semibold text-white shadow-sm hover:bg-blue-700"
                    onClick={() => setDemoFill(f => !f)}
                  >
                    {demoFill ? "Clear" : "Fill Demo"}
                  </button>
                </div>
              </div>
            )}

            <AuthForm
              mode={authMode}
              onClose={() => setAuthOpen(false)}
              onSwitch={(m) => setAuthMode(m)}
              onLogin={onLogin}
              onSignup={onSignup}
              inputCls={inputCls}
              inputEl={inputEl}
              defaultEmail={demoFill ? import.meta.env.VITE_DEMO_EMAIL ?? "" : ""}
              defaultPassword={demoFill ? import.meta.env.VITE_DEMO_PASSWORD ?? "" : ""}
            />
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Auth form ──────────────────────────────────────────────── */
function AuthForm({
  mode, onClose, onSwitch, onLogin, onSignup,
  inputCls, inputEl, defaultEmail, defaultPassword,
}: {
  mode: "login" | "signup"
  onClose: () => void
  onSwitch: (m: "login" | "signup") => void
  onLogin: (e: string, p: string) => Promise<void>
  onSignup: (e: string, p: string, n: string) => Promise<void>
  inputCls: string
  inputEl: string
  defaultEmail?: string
  defaultPassword?: string
}) {
  const [name, setName]         = React.useState("")
  const [email, setEmail]       = React.useState(defaultEmail || "")
  const [password, setPassword] = React.useState(defaultPassword || "")
  const [error, setError]       = React.useState("")
  const [loading, setLoading]   = React.useState(false)

  React.useEffect(() => {
    if (defaultEmail)    setEmail(defaultEmail)
    if (defaultPassword) setPassword(defaultPassword)
  }, [defaultEmail, defaultPassword])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    if (mode === "signup" && !name.trim())            { setError("Full name is required"); return }
    if (!email.trim())                                { setError("Email is required"); return }
    if (!password)                                    { setError("Password is required"); return }
    if (mode === "signup" && password.length < 8)     { setError("Password must be at least 8 characters"); return }
    setLoading(true)
    try {
      if (mode === "signup") await onSignup(email.trim(), password, name.trim())
      else                   await onLogin(email.trim(), password)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      let msg = "Authentication failed"
      if (typeof detail === "string")  msg = detail
      else if (Array.isArray(detail))  msg = detail.map((e: any) => e.msg || String(e)).join(", ")
      else if (detail?.message)        msg = detail.message
      setError(msg)
      setLoading(false)
    }
  }

  const switchMode = (m: "login" | "signup") => { setError(""); onSwitch(m) }

  return (
    <>
      {error && (
        <div className="mb-5 rounded-xl border border-red-600/20 bg-red-50 px-4 py-3 text-sm text-red-600 animate-fadeIn">
          {String(error)}
        </div>
      )}
      <form onSubmit={submit} className="space-y-4">
        {mode === "signup" && (
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-500">Full name</label>
            <div className={inputCls}>
              <ShieldAlert className="h-4 w-4 text-zinc-400" />
              <input className={inputEl} placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
          </div>
        )}
        <div>
          <label className="mb-1.5 block text-xs font-medium text-zinc-500">Email</label>
          <div className={inputCls}>
            <Mail className="h-4 w-4 text-zinc-400" />
            <input type="email" className={inputEl} placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-medium text-zinc-500">Password</label>
          <div className={inputCls}>
            <Lock className="h-4 w-4 text-zinc-400" />
            <input type="password" className={inputEl} placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          </div>
          {mode === "signup" && <p className="mt-1 text-xs text-zinc-400">At least 8 characters</p>}
        </div>
        <Button
          type="submit"
          disabled={loading}
          className="h-12 w-full rounded-xl bg-blue-600 text-[15px] font-semibold text-white shadow-sm shadow-blue-600/20 hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
        </Button>
      </form>
      <div className="mt-6 text-center text-sm text-zinc-500">
        {mode === "login" ? (
          <>Don&apos;t have an account?{" "}
            <button className="font-medium text-blue-600 hover:underline" onClick={() => switchMode("signup")}>Sign up</button>
          </>
        ) : (
          <>Already registered?{" "}
            <button className="font-medium text-blue-600 hover:underline" onClick={() => switchMode("login")}>Sign in</button>
          </>
        )}
      </div>
    </>
  )
}
