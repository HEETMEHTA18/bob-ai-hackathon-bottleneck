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
  Loader2,
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
  Thermometer,
  TrendingUp,
  Users,
  Wind,
  X,
  Zap,
  Activity,
  Bell,
} from "lucide-react"

import { Button } from "@/components/ui/button"

interface LandingPageProps {
  onLogin: (email: string, password: string) => Promise<void>
  onSignup: (email: string, password: string, name: string) => Promise<void>
}

const problemStats = [
  { value: "1.4B", label: "People served by India's grid" },
  { value: "5–8h", label: "Avg outage duration (urban)" },
  { value: "#1", label: "Transformer failures cause outages" },
  { value: "24–72h", label: "Prediction horizon needed" },
]

const workflowSteps = [
  {
    icon: Search,
    title: "PREDICT",
    desc: "ML models forecast 24h/72h failure probability for every transformer, feeder, and breaker using telemetry, weather, and incident history.",
    color: "#2563eb",
    bg: "#eff6ff",
  },
  {
    icon: Brain,
    title: "EXPLAIN",
    desc: "Every risk score surfaces the exact drivers — anomalous temperature, vibration spikes, partial discharge, storm exposure, prior incidents.",
    color: "#7c3aed",
    bg: "#f5f3ff",
  },
  {
    icon: Target,
    title: "PRIORITIZE",
    desc: "Composite risk score (0–100) weights failure probability × grid impact × weather × criticality × (1−redundancy). High-impact assets rank first.",
    color: "#eab308",
    bg: "#fefce8",
  },
  {
    icon: Compass,
    title: "POSITION",
    desc: "Crew planner matches transformer specialists, line crews, and substation teams to at-risk assets by region, specialty, and availability.",
    color: "#16a34a",
    bg: "#ecfdf5",
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
    desc: "The ML layer lives behind a stable FailurePredictor interface. Swap MockFailurePredictor → RealFailurePredictor in one file. Zero changes to risk engine, planners, or frontend. Model versions explicit, no data leakage.",
    highlight: "Drop-in replacement for real ML pipeline",
    color: "#8b5cf6",
  },
  {
    icon: Layers,
    title: "Scenario Simulation",
    desc: "Operators run what-if scenarios: Severe Storm (weather exposure ↑), Heatwave (thermal/load stress ↑), Asset Degradation (accelerated aging). Full pipeline re-runs coherently — predictions → risk → maintenance → crew.",
    highlight: "Before/after risk comparison in one view",
    color: "#16a34a",
  },
]

const demoScenario = [
  { step: 1, title: "Command Center", desc: "Open dashboard → TR-1042 ranked #1 critical (Risk 94/100, Health 38/100)" },
  { step: 2, title: "Asset Intelligence", desc: "Drill down → 8,420 customers at risk, 3 critical facilities, high temp + vibration + overheating incident + severe weather" },
  { step: 3, title: "Risk Breakdown", desc: "See exact drivers: p24=0.72, impact=0.91, weather=0.84, criticality=0.95, redundancy=0.15 → composite 94" },
  { step: 4, title: "Maintenance Planner", desc: "TR-1042 Priority #1: Inspect within 6h, replace bushing, thermal scan. Reason: temp anomaly + PD spike + storm exposure" },
  { step: 5, title: "Crew Planner", desc: "CREW-07 (transformer specialist, Region 3) pre-positioned 2.3km from asset. ETA 12 min. Backup: CREW-12" },
  { step: 6, title: "Scenario Simulator", desc: "Run Severe Storm → TR-1042 risk 94→98, CREW-07 reassigned, TR-2108 enters top 5. Full pipeline updates in <1s" },
  { step: 7, title: "AI Copilot", desc: "Ask: 'Why is TR-1042 critical?' → Grounded answer citing telemetry, weather, incidents, grid impact. No hallucination." },
]

const techStack = [
  { icon: Zap, label: "FastAPI", desc: "Python backend" },
  { icon: Cpu, label: "XGBoost/LSTM", desc: "Failure prediction" },
  { icon: Globe, label: "Open-Meteo", desc: "Live weather" },
  { icon: Bot, label: "Gemini", desc: "AI Copilot" },
  { icon: Database, label: "SQLite", desc: "Asset data" },
  { icon: Activity, label: "React 18", desc: "TypeScript UI" },
  { icon: Shield, label: "Pydantic", desc: "Type-safe contracts" },
  { icon: HardHat, label: "Docker", desc: "Containerized" },
]

const kpis = [
  { value: "30", label: "Grid Assets Monitored" },
  { value: "24h", label: "Failure Prediction Horizon" },
  { value: "0–100", label: "Composite Risk Score" },
  { value: "<1s", label: "Scenario Re-compute" },
  { value: "100%", label: "Offline Demo Ready" },
  { value: "0", label: "External Credentials Needed" },
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
        className={`sticky top-0 z-40 border-b border-[#d4d4d8] bg-[#f5f5f5]/80 backdrop-blur-xl transition-all duration-200 ${
          scrollY > 20 ? "shadow-sm" : ""
        }`}
      >
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <a href="#top" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
              <ShieldAlert className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-zinc-900">GridShield</div>
              <div className="text-[10px] font-medium text-zinc-400">Power Outage Prediction & Grid Equipment Failure Advisor</div>
            </div>
          </a>

          <nav className="hidden items-center gap-7 text-sm text-zinc-500 md:flex">
            <a href="#problem" className="transition-colors hover:text-zinc-900" onClick={(e) => { e.preventDefault(); scrollTo("problem"); }}>Problem</a>
            <a href="#solution" className="transition-colors hover:text-zinc-900" onClick={(e) => { e.preventDefault(); scrollTo("solution"); }}>Solution</a>
            <a href="#differentiators" className="transition-colors hover:text-zinc-900" onClick={(e) => { e.preventDefault(); scrollTo("differentiators"); }}>Differentiators</a>
            <a href="#demo" className="transition-colors hover:text-zinc-900" onClick={(e) => { e.preventDefault(); scrollTo("demo"); }}>Demo</a>
            <a href="#tech" className="transition-colors hover:text-zinc-900" onClick={(e) => { e.preventDefault(); scrollTo("tech"); }}>Tech Stack</a>
          </nav>

          <div className="hidden items-center gap-3 md:flex">
            <Button variant="ghost" className="text-zinc-600 hover:bg-black/5 hover:text-zinc-900" onClick={() => openAuth("login")}>
              Sign in
            </Button>
            <Button className="rounded-lg bg-blue-600 text-white shadow-sm shadow-blue-600/20 hover:bg-blue-700" onClick={() => openAuth("signup")}>
              Get started
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>

          <button className="text-zinc-600 md:hidden" onClick={() => setMobileNav(!mobileNav)} aria-label="Menu">
            {mobileNav ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
        {mobileNav && (
          <div className="border-t border-[#d4d4d8] bg-[#f5f5f5] px-6 py-4 md:hidden animate-fadeIn">
            <div className="flex flex-col gap-1 text-sm text-zinc-600">
              <a href="#problem" onClick={() => scrollTo("problem")} className="rounded-lg px-3 py-2 hover:bg-black/5">Problem</a>
              <a href="#solution" onClick={() => scrollTo("solution")} className="rounded-lg px-3 py-2 hover:bg-black/5">Solution</a>
              <a href="#differentiators" onClick={() => scrollTo("differentiators")} className="rounded-lg px-3 py-2 hover:bg-black/5">Differentiators</a>
              <a href="#demo" onClick={() => scrollTo("demo")} className="rounded-lg px-3 py-2 hover:bg-black/5">Demo Scenario</a>
              <a href="#tech" onClick={() => scrollTo("tech")} className="rounded-lg px-3 py-2 hover:bg-black/5">Tech Stack</a>
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
        <div className="absolute inset-0" aria-hidden="true">
          <img
            loading="lazy"
            src="https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?q=80&w=2400&auto=format&fit=crop"
            alt=""
            className="h-full w-full object-cover opacity-[0.12]"
          />
          <div className="absolute inset-0 bg-[radial-gradient(60%_50%_at_50%_-10%,rgba(37,99,235,0.08),transparent)]" />
        </div>

        <div className="relative z-10 mx-auto flex min-h-[88vh] max-w-6xl flex-col items-center justify-center px-6 py-24 text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-600/15 bg-white px-4 py-1.5 text-xs font-medium text-blue-700 shadow-sm animate-fadeIn">
            <Sparkles className="h-3.5 w-3.5" />
            IBM Bob Hackathon 2026 · Track U1: Power Outage Prediction & Grid Equipment Failure Advisor
          </div>
          <h1 className="max-w-3xl text-balance text-4xl font-bold leading-[1.06] tracking-tight text-zinc-900 sm:text-6xl animate-fadeIn" style={{ animationDelay: "100ms" }}>
            Predict failures before they happen.
            <br />
            <span className="bg-gradient-to-r from-blue-600 via-blue-500 to-sky-400 bg-clip-text text-transparent">
              Explain. Prioritize. Position.
            </span>
          </h1>
          <p className="mt-6 max-w-xl text-pretty text-base leading-relaxed text-zinc-500 sm:text-lg animate-fadeIn" style={{ animationDelay: "200ms" }}>
            GridShield turns asset telemetry, weather forecasts, and incident history into
            actionable intelligence — predicting which equipment will fail in the next 24–72 hours,
            explaining why, ranking by grid impact, and pre-positioning crews before outages occur.
          </p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-3 animate-fadeIn" style={{ animationDelay: "300ms" }}>
            <Button
              className="h-12 rounded-xl bg-blue-600 px-7 text-[15px] font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700"
              onClick={() => openAuth("signup")}
            >
              Start exploring GridShield
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="h-12 rounded-xl border-zinc-200 bg-white px-7 text-[15px] text-zinc-700 shadow-sm hover:bg-white"
              onClick={() => scrollTo("demo")}
            >
              See the demo scenario
            </Button>
          </div>

          <div className="mt-16 grid w-full max-w-3xl grid-cols-2 gap-3 sm:grid-cols-3 sm:grid-cols-6 animate-fadeIn" style={{ animationDelay: "400ms" }}>
            {kpis.map((s) => (
              <div key={s.label} className="glass-card-soft rounded-2xl px-5 py-4 text-center">
                <div className="text-2xl font-bold tabular-nums text-zinc-900" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                  {s.value}
                </div>
                <div className="mt-1 text-[11px] font-medium uppercase tracking-wider text-zinc-400">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Problem ─────────────────────────────────────────── */}
      <section id="problem" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-14 max-w-2xl animate-fadeIn">
          <p className="mb-3 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-red-600">
            <AlertTriangle className="h-3.5 w-3.5" /> The Problem
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">
            Power grids are aging. Failures are discovered reactively.
          </h2>
          <p className="mt-4 text-zinc-500 text-lg">
            Utility operators manage fleets of transformers, feeders, breakers, and switching equipment
            that are decades old, operating under increasing load, and exposed to more frequent extreme weather.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-4 animate-fadeIn" style={{ animationDelay: "100ms" }}>
          {problemStats.map((s) => (
            <div key={s.label} className="card relative overflow-hidden" style={{ borderLeft: "4px solid #c5221f" }}>
              <div className="text-3xl font-bold tabular-nums text-zinc-900" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                {s.value}
              </div>
              <div className="mt-2 text-sm text-zinc-500">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="mt-12 animate-fadeIn" style={{ animationDelay: "200ms" }}>
          <h3 className="text-xl font-bold text-zinc-900 mb-6">Today's operational reality:</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              { icon: Bell, title: "Reactive Discovery", desc: "Failures found after outage starts — not before" },
              { icon: Radio, title: "Calendar-Driven Maintenance", desc: "Fixed schedules ignore actual asset condition" },
              { icon: MapPin, title: "Post-Failure Dispatch", desc: "Crews sent after failure, not pre-positioned" },
              { icon: Layers, title: "Siloed Risk Assessment", desc: "Weather, telemetry, incidents never combined in one view" },
            ].map((item, i) => (
              <div key={i} className="card flex gap-4 p-5">
                <div className="flex-shrink-0 w-11 h-11 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
                  <item.icon className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-zinc-900">{item.title}</h4>
                  <p className="mt-1 text-sm text-zinc-500">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-12 p-6 rounded-2xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 animate-fadeIn" style={{ animationDelay: "300ms" }}>
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-zinc-900">The result: unnecessary outages, delayed restoration, and significant customer impact</h3>
              <p className="mt-2 text-sm text-zinc-600">
                Especially for critical facilities — hospitals, emergency services, water treatment plants —
                where every minute of downtime carries life-safety consequences.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Solution / Workflow ────────────────────────────── */}
      <section id="solution" className="border-y border-[#d4d4d8] bg-white">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-14 max-w-2xl animate-fadeIn">
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-600">Solution</p>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">PREDICT → EXPLAIN → PRIORITIZE → POSITION</h2>
            <p className="mt-4 text-zinc-500 text-lg">
              A complete decision-support loop: from raw data to crew dispatch, with explainability at every step.
            </p>
          </div>

          <div className="relative">
            {/* Connecting line */}
            <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-blue-600 via-yellow-500 to-green-600 -translate-x-1/2" style={{ transform: "translateX(-50%)" }} />

            <div className="grid gap-8 lg:grid-cols-4 relative">
              {workflowSteps.map((step, i) => (
                <div
                  key={step.title}
                  className={`relative animate-fadeIn ${i >= 2 ? "lg:-mt-10" : ""}`}
                  style={{ animationDelay: `${i * 150}ms` }}
                >
                  <div className="relative z-10 flex flex-col items-center">
                    <div
                      className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg"
                      style={{ background: step.bg, color: step.color }}
                    >
                      <step.icon className="h-7 w-7" />
                    </div>
                    <div className="mt-4 text-center">
                      <h3 className="text-lg font-bold text-zinc-900" style={{ color: step.color }}>
                        {step.title}
                      </h3>
                      <p className="mt-2 text-sm text-zinc-500 max-w-xs">{step.desc}</p>
                    </div>
                    {i < workflowSteps.length - 1 && (
                      <div className="hidden lg:block absolute top-[60px] left-[calc(50%+8px)] w-[calc(100%-16px)] h-px bg-gradient-to-r from-transparent via-zinc-200 to-transparent" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Mobile workflow cards */}
          <div className="mt-12 lg:hidden grid gap-4 animate-fadeIn">
            {workflowSteps.map((step, i) => (
              <div key={step.title} className="card flex gap-4 p-5" style={{ borderLeft: `4px solid ${step.color}` }}>
                <div className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: step.bg }}>
                  <step.icon className="h-6 w-6" style={{ color: step.color }} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold tracking-widest" style={{ color: step.color, fontFamily: "'JetBrains Mono', monospace" }}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <h4 className="font-semibold text-zinc-900">{step.title}</h4>
                  </div>
                  <p className="mt-2 text-sm text-zinc-500">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Differentiators ───────────────────────────────── */}
      <section id="differentiators" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-14 max-w-2xl animate-fadeIn">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-purple-600">Key Differentiators</p>
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">Why GridShield is different</h2>
          <p className="mt-4 text-zinc-500">Four architectural choices that make GridShield operational, not academic.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2 animate-fadeIn">
          {differentiators.map((d, i) => (
            <div
              key={d.title}
              className="card p-6 group relative overflow-hidden transition-all hover:shadow-[0_12px_40px_rgba(0,0,0,0.08)]"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity" style={{ background: `linear-gradient(135deg, ${d.color}10, transparent)` }} />
              <div className="relative flex gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: `${d.color}15`, color: d.color }}>
                  <d.icon className="h-6 w-6" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-[15px] font-semibold text-zinc-900">{d.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-zinc-500">{d.desc}</p>
                  <div className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                    <Sparkles className="h-3 w-3" />
                    <span>{d.highlight}</span>
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
            <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">The story we demonstrate end-to-end</h2>
            <p className="mt-4 text-zinc-500">
              A weather event approaches while transformer TR-1042 develops abnormal temperature, vibration,
              partial discharge, and load behavior. Watch the full loop execute.
            </p>
          </div>

          <div className="relative">
            <div className="hidden lg:block absolute left-10 top-0 bottom-0 w-px bg-gradient-to-b from-blue-600 via-amber-500 to-green-600" />
            <div className="grid gap-6 lg:grid-cols-2">
              {demoScenario.map((item, i) => (
                <div
                  key={item.step}
                  className={`relative animate-fadeIn ${i >= 3 ? "lg:-mt-6" : ""}`}
                  style={{ animationDelay: `${i * 80}ms` }}
                >
                  <div className="relative pl-10 lg:pl-0">
                    <div className="absolute left-0 top-1 lg:left-[calc(50%+8px)] lg:-translate-x-full w-7 h-7 rounded-full flex items-center justify-center text-white font-bold text-xs z-10 shadow"
                      style={{ background: i < 2 ? "#2563eb" : i < 4 ? "#eab308" : "#16a34a" }}>
                      {item.step}
                    </div>
                    <div className="card p-5 group hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-shadow">
                      <h4 className="font-semibold text-zinc-900 flex items-center gap-2">
                        <span className="text-xs font-mono text-zinc-400">{item.title}</span>
                      </h4>
                      <p className="mt-2 text-sm text-zinc-500">{item.desc}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-12 p-6 rounded-2xl bg-gradient-to-r from-blue-600 via-blue-700 to-blue-900 text-white animate-fadeIn">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center">
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
        </div>
      </section>

      {/* ── Tech Stack ────────────────────────────────────── */}
      <section id="tech" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-14 max-w-2xl animate-fadeIn">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-zinc-500">Technology</p>
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">Built on solid foundations</h2>
          <p className="mt-4 text-zinc-500">Leveraging proven infrastructure from Gridkavach with GridShield-specific additions.</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 animate-fadeIn">
          {techStack.map((t, i) => (
            <div
              key={t.label}
              className="card p-5 text-center group hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all hover:-translate-y-0.5"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <div className="w-12 h-12 rounded-xl mx-auto mb-3 flex items-center justify-center bg-blue-50 text-blue-600">
                <t.icon className="h-6 w-6" />
              </div>
              <h4 className="font-semibold text-zinc-900">{t.label}</h4>
              <p className="mt-1 text-xs text-zinc-500">{t.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 animate-fadeIn">
          <h3 className="text-xl font-bold text-zinc-900 mb-6 text-center">Architecture at a glance</h3>
          <div className="card p-6 overflow-x-auto">
            <pre className="text-sm font-mono text-zinc-700 leading-relaxed" style={{ fontFamily: "'JetBrains Mono', monospace", whiteSpace: "pre-wrap" }}>
{`Asset Telemetry (temp, vibration, load, voltage, PD)
      +  Incident History
      +  Weather Exposure (Open-Meteo live / mock fallback)
            ↓
    MockFailurePredictor  ←── ML seam (swap → RealFailurePredictor)
            ↓
     FailurePrediction (stable Pydantic contract)
            ↓
   Grid Impact Engine  +  Risk Engine
            ↓
       Risk Ranking (composite score 0–100)
            ↓
    Maintenance Prioritization   +   Crew Pre-Positioning
            ↓
   GridShield Command Center (React 18 + TypeScript)`}
            </pre>
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 py-24 animate-fadeIn">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900 px-8 py-16 text-center shadow-xl shadow-blue-600/20">
          <div className="absolute inset-0 bg-[radial-gradient(60%_80%_at_50%_0%,rgba(255,255,255,0.18),transparent)]" />
          <div className="relative z-10 max-w-2xl mx-auto">
            <h2 className="mx-auto max-w-xl text-balance text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Your first risk ranking in under five minutes.
            </h2>
            <p className="mx-auto mt-4 max-w-md text-blue-100">
              Create an account, explore the Command Center, and trace TR-1042 through the full
              PREDICT → EXPLAIN → PRIORITIZE → POSITION loop.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <Button
                className="h-12 rounded-xl bg-white px-8 text-[15px] font-semibold text-blue-700 shadow-lg hover:bg-blue-50"
                onClick={() => openAuth("signup")}
              >
                Start free
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="h-12 rounded-xl border-white/30 bg-transparent px-8 text-[15px] font-medium text-white hover:bg-white/10"
                onClick={() => scrollTo("demo")}
              >
                View demo walkthrough
              </Button>
            </div>
            <p className="mt-6 text-xs text-blue-200/60">
              For demo access, use the pre-seeded account
            </p>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="border-t border-[#d4d4d8] animate-fadeIn">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-10 text-sm text-zinc-400 sm:flex-row">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-blue-600" />
            <span className="font-medium text-zinc-600">GridShield AI</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#problem" className="hover:text-zinc-800">Problem</a>
            <a href="#solution" className="hover:text-zinc-800">Solution</a>
            <a href="#differentiators" className="hover:text-zinc-800">Differentiators</a>
            <a href="#demo" className="hover:text-zinc-800">Demo</a>
            <a href="#tech" className="hover:text-zinc-800">Tech Stack</a>
          </div>
          <div className="text-xs">IBM Bob Hackathon 2026 · Track U1 · PREDICT → EXPLAIN → PRIORITIZE → POSITION</div>
        </div>
      </footer>

      {/* ── Auth modal ──────────────────────────────────────── */}
      {authOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4 backdrop-blur-sm animate-fadeIn" onClick={() => setAuthOpen(false)}>
          <div
            className="animate-fadeIn w-full max-w-md rounded-3xl border bg-white p-8 shadow-2xl"
            style={{ borderColor: "#d4d4d8" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-7 flex items-start justify-between">
              <div>
                <h3 className="text-xl font-bold tracking-tight text-zinc-900">
                  {authMode === "login" ? "Welcome back" : "Create your account"}
                </h3>
                <p className="mt-1 text-sm text-zinc-400">
                  {authMode === "login" ? "Sign in to your GridShield workspace." : "Start predicting outages in minutes — no card needed."}
                </p>
              </div>
              <button onClick={() => setAuthOpen(false)} className="rounded-lg p-1.5 text-zinc-400 hover:bg-black/5 hover:text-zinc-800" aria-label="Close">
                <X className="h-5 w-5" />
              </button>
            </div>

            {authMode === "login" && (
              <div className="mb-5 rounded-xl border border-blue-600/15 bg-blue-50 px-4 py-3 text-xs text-blue-700">
                <div className="mb-2 font-medium">Quick Demo Access</div>
                <div className="flex items-center justify-between gap-3">
                  <span className="font-mono text-blue-600/70" style={{ fontFamily: "'JetBrains Mono', monospace" }}>Pre-seeded demo account</span>
                  <button
                    type="button"
                    className="shrink-0 rounded-lg bg-blue-600 px-3 py-1.5 text-[11px] font-semibold text-white shadow-sm hover:bg-blue-700"
                    onClick={() => setDemoFill(f => !f)}
                  >
                    {demoFill ? "Clear" : "Auto-fill"}
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
              defaultEmail={demoFill ? "demo@gridshield.ai" : ""}
              defaultPassword={demoFill ? "demo1234" : ""}
            />
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Auth form ──────────────────────────────────────────────── */
function AuthForm({
  mode,
  onClose,
  onSwitch,
  onLogin,
  onSignup,
  inputCls,
  inputEl,
  defaultEmail,
  defaultPassword,
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
  const [name, setName] = React.useState("")
  const [email, setEmail] = React.useState(defaultEmail || "")
  const [password, setPassword] = React.useState(defaultPassword || "")
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  React.useEffect(() => {
    if (defaultEmail) setEmail(defaultEmail)
    if (defaultPassword) setPassword(defaultPassword)
  }, [defaultEmail, defaultPassword])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    if (mode === "signup" && !name.trim()) { setError("Full name is required"); return }
    if (!email.trim()) { setError("Email is required"); return }
    if (!password) { setError("Password is required"); return }
    if (mode === "signup" && password.length < 8) { setError("Password must be at least 8 characters"); return }
    setLoading(true)
    try {
      if (mode === "signup") await onSignup(email.trim(), password, name.trim())
      else await onLogin(email.trim(), password)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      let msg = "Authentication failed"
      if (typeof detail === "string") msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || String(e)).join(", ")
      else if (detail?.message) msg = detail.message
      setError(msg)
      setLoading(false)
    }
  }

  const switchMode = (m: "login" | "signup") => {
    setError("")
    onSwitch(m)
  }

  return (
    <>
      {error && (
        <div className="mb-5 rounded-xl border border-red-600/20 bg-red-50 px-4 py-3 text-sm text-red-600 animate-fadeIn">{String(error)}</div>
      )}

      <form onSubmit={submit} className="space-y-4">
        {mode === "signup" && (
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-500">Full name</label>
            <div className={inputCls}>
              <Bot className="h-4 w-4 text-zinc-400" />
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
          <>
            Don&apos;t have an account?{" "}
            <button className="font-medium text-blue-600 hover:underline" onClick={() => switchMode("signup")}>
              Sign up
            </button>
          </>
        ) : (
          <>
            Already registered?{" "}
            <button className="font-medium text-blue-600 hover:underline" onClick={() => switchMode("login")}>
              Sign in
            </button>
          </>
        )}
      </div>
    </>
  )
}