import * as React from "react"
import {
  ArrowRight,
  BatteryCharging,
  Bot,
  CloudSun,
  Cpu,
  Database,
  LineChart,
  Lock,
  Mail,
  Menu,
  ShieldAlert,
  Sparkles,
  Sun,
  Wind,
  X,
  Zap,
} from "lucide-react"

import { Button } from "@/components/ui/button"

const features = [
  {
    icon: LineChart,
    title: "Probabilistic forecasting",
    desc: "P10 / P50 / P90 generation bands from Chronos & Lag-Llama foundation models — you get the range, not just a number.",
  },
  {
    icon: ShieldAlert,
    title: "Curtailment risk warnings",
    desc: "Hour-by-hour risk classification (LOW / MEDIUM / HIGH) with the exact action to take before over-generation hits.",
  },
  {
    icon: BatteryCharging,
    title: "Battery dispatch optimizer",
    desc: "Charge, discharge, or curtail — ranked by net revenue and CO₂ avoided for every hour of the horizon.",
  },
  {
    icon: Sparkles,
    title: "Explainable decisions",
    desc: "Every recommendation explains the “why” in plain language, with ₹ savings and tCO₂ impact estimates.",
  },
  {
    icon: Cpu,
    title: "Zero-shot ML inference",
    desc: "Foundation models fine-tuned on your site data — no manual feature engineering, retrains overnight.",
  },
  {
    icon: Zap,
    title: "Real-time anomaly guard",
    desc: "Spike, drop, and data-gap detection with automatic correction before bad data poisons a forecast.",
  },
]

const steps = [
  { n: "01", title: "Connect your site", desc: "Register a solar or wind site, or import SCADA / CSV history." },
  { n: "02", title: "Models forecast", desc: "Foundation models produce P10/P50/P90 curves from live weather." },
  { n: "03", title: "Risk & dispatch", desc: "Curtailment risk plus battery action, ranked by ₹ and CO₂." },
  { n: "04", title: "Simulate & decide", desc: "Perturb cloud or wind to stress-test tomorrow before 5pm." },
]

const stats = [
  { value: "12", label: "Live sites" },
  { value: "200K+", label: "Data points" },
  { value: "15 min", label: "Refresh cycle" },
  { value: "24–72 h", label: "Horizons" },
]

interface LandingPageProps {
  onLogin: (email: string, password: string) => Promise<void>
  onSignup: (email: string, password: string, name: string) => Promise<void>
}

export function LandingPage({ onLogin, onSignup }: LandingPageProps) {
  const [authOpen, setAuthOpen] = React.useState(false)
  const [authMode, setAuthMode] = React.useState<"login" | "signup">("login")
  const [demoFill, setDemoFill] = React.useState(false)
  const [mobileNav, setMobileNav] = React.useState(false)

  const openAuth = (mode: "login" | "signup") => {
    setAuthMode(mode)
    setAuthOpen(true)
  }

  const inputCls =
    "flex h-12 w-full items-center gap-3 rounded-xl border bg-white px-4 focus-within:border-blue-500/60 focus-within:ring-2 focus-within:ring-blue-500/10"
  const inputEl =
    "h-full w-full bg-transparent text-sm text-zinc-800 outline-none placeholder:text-zinc-400"

  return (
    <div className="h-screen overflow-y-auto bg-[#f5f5f5] text-zinc-800 antialiased">
      {/* ── Nav ─────────────────────────────────────────────── */}
      <header className="sticky top-0 z-40 border-b border-[#d4d4d8] bg-[#f5f5f5]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <a href="#top" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
              <Zap className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-zinc-900">Bottleneck AI</div>
              <div className="text-[10px] font-medium text-zinc-400">Renewable Energy Intelligence</div>
            </div>
          </a>

          <nav className="hidden items-center gap-7 text-sm text-zinc-500 md:flex">
            <a href="#features" className="transition-colors hover:text-zinc-900">Features</a>
            <a href="#how" className="transition-colors hover:text-zinc-900">How it works</a>
            <a href="#pipeline" className="transition-colors hover:text-zinc-900">Model</a>
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
          <div className="border-t border-[#d4d4d8] bg-[#f5f5f5] px-6 py-4 md:hidden">
            <div className="flex flex-col gap-1 text-sm text-zinc-600">
              <a href="#features" onClick={() => setMobileNav(false)} className="rounded-lg px-3 py-2 hover:bg-black/5">Features</a>
              <a href="#how" onClick={() => setMobileNav(false)} className="rounded-lg px-3 py-2 hover:bg-black/5">How it works</a>
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
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1509391366360-2e959784a276?q=80&w=2400&auto=format&fit=crop"
            alt=""
            className="h-full w-full object-cover opacity-[0.16]"
          />
          <div className="absolute inset-0 bg-[radial-gradient(60%_50%_at_50%_-10%,rgba(37,99,235,0.10),transparent)]" />
        </div>

        <div className="relative z-10 mx-auto flex min-h-[88vh] max-w-6xl flex-col items-center justify-center px-6 py-24 text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-600/15 bg-white px-4 py-1.5 text-xs font-medium text-blue-700 shadow-sm">
            <Sparkles className="h-3.5 w-3.5" />
            HackOut&apos;26 · Renewable generation intelligence
          </div>
          <h1 className="max-w-3xl text-balance text-4xl font-bold leading-[1.06] tracking-tight text-zinc-900 sm:text-6xl">
            Forecast renewables with confidence,{" "}
            <span className="bg-gradient-to-r from-blue-600 to-sky-400 bg-clip-text text-transparent">
              not guesswork.
            </span>
          </h1>
          <p className="mt-6 max-w-xl text-pretty text-base leading-relaxed text-zinc-500 sm:text-lg">
            Bottleneck turns raw irradiance and wind into P10/P50/P90 forecasts,
            flags curtailment before it costs you money, and tells you exactly
            when to charge, discharge, or sell back to the grid.
          </p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Button
              className="h-12 rounded-xl bg-blue-600 px-7 text-[15px] font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700"
              onClick={() => openAuth("signup")}
            >
              Start analyzing your site
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="h-12 rounded-xl border-zinc-200 bg-white px-7 text-[15px] text-zinc-700 shadow-sm hover:bg-white"
              onClick={() => document.getElementById("pipeline")?.scrollIntoView({ behavior: "smooth" })}
            >
              See how the model works
            </Button>
          </div>

          <div className="mt-16 grid w-full max-w-3xl grid-cols-2 gap-3 sm:grid-cols-4">
            {stats.map((s) => (
              <div key={s.label} className="glass-card-soft rounded-2xl px-6 py-5 text-center">
                <div className="text-2xl font-bold tabular-nums text-zinc-900" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                  {s.value}
                </div>
                <div className="mt-1 text-[11px] font-medium uppercase tracking-wider text-zinc-400">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────── */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-14 max-w-2xl">
          <p className="mb-3 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-blue-600">
            <CloudSun className="h-3.5 w-3.5" /> Platform
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">
            Everything a grid operator needs, in one place.
          </h2>
          <p className="mt-4 text-zinc-500">
            From the weather feed to the final dispatch decision — each layer is
            accountable, explainable, and live.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="glass-card-soft group rounded-2xl p-7 transition-all hover:-translate-y-0.5 hover:shadow-[0_12px_40px_rgba(0,0,0,0.08)]"
            >
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600 ring-1 ring-blue-600/10 transition-transform group-hover:scale-105">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="text-[15px] font-semibold text-zinc-900">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-500">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────── */}
      <section id="how" className="border-y border-[#d4d4d8] bg-white">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-14 max-w-2xl">
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-600">Workflow</p>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">From raw data to a decision in four steps.</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((s, i) => (
              <div key={s.n} className="relative rounded-2xl border border-[#d4d4d8] bg-[#f5f5f5] p-6">
                {i < steps.length - 1 && (
                  <div className="absolute -right-5 top-1/2 z-10 hidden h-px w-8 -translate-y-1/2 text-blue-400 lg:block" />
                )}
                <div className="text-xs font-bold tracking-widest text-blue-500" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                  {s.n}
                </div>
                <h3 className="mt-3 text-[15px] font-semibold text-zinc-900">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Model pipeline ──────────────────────────────────── */}
      <section id="pipeline" className="border-y border-[#d4d4d8] bg-white">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-14 max-w-2xl">
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-600">Model</p>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">Lambda architecture, foundation-model forecasting.</h2>
            <p className="mt-4 text-zinc-500">
              Batch learners refine, a live speed layer ingests weather, and the
              serving layer exposes P10/P50/P90 through one API contract.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {[
              { icon: Sun, label: "Irradiance" },
              { icon: Wind, label: "Wind & temp" },
              { icon: Cpu, label: "Foundation models" },
              { icon: LineChart, label: "P10 / P50 / P90" },
              { icon: Database, label: "Live API + UI" },
            ].map(({ icon: Icon, label }) => (
              <div key={label} className="glass-card-soft flex flex-col items-center justify-center gap-3 rounded-2xl px-4 py-8 text-center">
                <Icon className="h-6 w-6 text-blue-500" />
                <div className="text-xs font-medium text-zinc-600">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900 px-8 py-16 text-center shadow-xl shadow-blue-600/20">
          <div className="absolute inset-0 bg-[radial-gradient(60%_80%_at_50%_0%,rgba(255,255,255,0.18),transparent)]" />
          <div className="relative z-10">
            <h2 className="mx-auto max-w-xl text-balance text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Your first P50 forecast in under ten minutes.
            </h2>
            <p className="mx-auto mt-4 max-w-md text-blue-100">
              Create an account, add a site, and watch the models go to work.
              Demo login:{" "}
              <span className="font-mono text-white" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                demo@bottleneck.com / demo1234
              </span>
            </p>
            <Button
              className="mt-8 h-12 rounded-xl bg-white px-8 text-[15px] font-semibold text-blue-700 shadow-lg hover:bg-blue-50"
              onClick={() => openAuth("signup")}
            >
              Start free
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="border-t border-[#d4d4d8]">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-10 text-sm text-zinc-400 sm:flex-row">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-blue-600" />
            <span className="font-medium text-zinc-600">Bottleneck AI</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#features" className="hover:text-zinc-800">Features</a>
            <a href="#how" className="hover:text-zinc-800">How it works</a>
          </div>
          <div className="text-xs">HackOut&apos;26 · Forecast · Risk · Dispatch · Explain</div>
        </div>
      </footer>

      {/* ── Auth modal ──────────────────────────────────────── */}
      {authOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4 backdrop-blur-sm" onClick={() => setAuthOpen(false)}>
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
                  {authMode === "login" ? "Sign in to your Bottleneck workspace." : "Start forecasting in minutes — no card needed."}
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
                  <span className="font-mono" style={{ fontFamily: "'JetBrains Mono', monospace" }}>demo@bottleneck.com / demo1234</span>
                  <button
                    type="button"
                    className="shrink-0 rounded-lg bg-blue-600 px-3 py-1.5 text-[11px] font-semibold text-white shadow-sm hover:bg-blue-700"
                    onClick={() => setDemoFill(f => !f)}
                  >
                    {demoFill ? "Filled ✓" : "Auto-fill"}
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
              defaultEmail={demoFill ? "demo@bottleneck.com" : ""}
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
        <div className="mb-5 rounded-xl border border-red-600/20 bg-red-50 px-4 py-3 text-sm text-red-600">{String(error)}</div>
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