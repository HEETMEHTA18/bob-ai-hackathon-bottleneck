# Module 2: Frontend Dashboard & UI

**Owner:** Agent 2  
**Duration:** 48 hours (HackOut'26)

## Progress Tracking

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| Phase 0 — Setup | completed | — | — | Vite + React + TypeScript + Tailwind initialized ✅ |
| Phase 1 — Layout & Navigation | completed | — | — | Sidebar, header, navigation, site context fully implemented ✅ |
| Phase 2 — Site Management | completed | — | — | Form, CSV upload, site list ✅ |
| Phase 3 — Forecast Dashboard | completed | — | — | Forecast chart with P10/P50/P90 bands ✅ |
| Phase 4 — Risk & Recommendation Panel | completed | — | — | Risk banner, recommendation card, financial/CO₂ impact ✅ |
| Phase 5 — Explainability Panel | completed | — | — | Explanation panel, ₹/CO₂ impact metrics ✅ |
| Phase 6 — Scenario Simulator | completed | — | — | Scenario controls, before/after comparison ✅ |
| Phase 7 — Chart Library & Components | completed | — | — | Recharts setup, reusable components ✅ |
| Phase 8 — Styling & Polish | completed | — | — | Responsive design, animations, error handling ✅ |
| Phase 9 — Integration & Testing | in_progress | — | — | `npm run build` passes clean; API integration & demo flow pending |
| Phase 10 — Professional UI & AI Assistant | completed | — | — | shadcn-style design system + GridMind AI Copilot integrated ✅ |
| Phase 11 — Backend Hardening & Forecast Intelligence | completed | — | — | Blueprint audit, input validation, upload limits, RBAC fix, Insights API (accuracy/model/alerts/weather) + Insights page ✅ |
---

## Scope

React frontend application, dashboard components, visualization, user interactions, and all client-side logic.

---

## Tasks Breakdown

### Phase 0 — Setup (Hours 0–2)

| # | Task | Details | Output |
|---|------|---------|--------|
| 1 | Initialize React project | Create `frontend/` directory with Vite + React + TypeScript | Working React app | ✅ Done
| 2 | Install dependencies | Tailwind CSS, Recharts/ECharts, axios, react-router-dom, react-hot-toast | Package.json ready | ✅ Done
| 3 | Configure Tailwind | Set up `tailwind.config.js` with custom theme (energy color palette: green/amber/red) | Styled system | ✅ Done
| 4 | Set up API client | `frontend/src/api/client.ts` — axios instance pointing to `http://localhost:8000` | API layer ready | ✅ Done

---

### Phase 1 — Layout & Navigation

| # | Task | Details | Output |
|---|------|---------|--------|
| 5 | App layout | `App.tsx` — sidebar + main content area responsive layout | Layout shell | ✅ Done
| 6 | Sidebar navigation | Site selector dropdown, nav links: Dashboard, Forecast, Risks, Optimize, Settings | Navigation | ✅ Done
| 7 | Theme & branding | "GridMind AI" header, energy-themed color scheme (green/amber/red for status) | Branded UI | ✅ Done

---

### Phase 2 — Site Management
| # | Task | Details | Output |
|---|------|---------|--------|
| 8 | Site registration form | `SiteForm.tsx` — inputs: site name, capacity (kW), location (lat/lon), battery size (kWh), export limit (kW) | Form component | ✅ Done
| 9 | CSV upload component | `CSVUpload.tsx` — drag-and-drop CSV upload with preview table, column mapping | Upload widget | ✅ Done
| 10 | Site list page | `SiteList.tsx` — cards showing all registered sites with status indicators | Site overview | ✅ Done
| 11 | Site selection context | React context for active site, persist in localStorage | Global state | ✅ Done

---

### Phase 3 — Forecast Dashboard
| # | Task | Details | Output |
|---|------|---------|--------|
| 12 | Forecast chart component | `ForecastChart.tsx` — line chart showing: actual generation (historical), predicted (P50), P10-P90 uncertainty band (shaded area) | Interactive chart | ✅ Done
| 13 | Time horizon selector | Tabs: 24h / 48h / 72h — update chart on selection | Horizon toggle | ✅ Done
| 14 | Solar + Wind overlay | Dual-axis or separate panels for solar and wind generation | Multi-source view | ✅ Done
| 15 | Forecast data hook | `useForecast.ts` — fetch `/forecast/{site_id}` on mount, handle loading/error | Data hook | ✅ Done
| 16 | Key metrics cards | Top row: Current Generation, Forecast (next 24h peak), Confidence Level, Hours to Surplus | KPI cards | ✅ Done

---

### Phase 4 — Risk & Recommendation Panel
| # | Task | Details | Output |
|---|------|---------|--------|
| 17 | Risk banner component | `RiskBanner.tsx` — color-coded banner (green/amber/red) showing current risk level for each hour | Visual alert | ✅ Done
| 18 | Hourly risk timeline | Horizontal bar chart showing risk level per hour over forecast window | Risk visualization | ✅ Done
| 19 | Recommendation card | `RecommendationCard.tsx` — current action with icon, why, estimated impact | Action card | ✅ Done
| 20 | Action history table | Table showing past recommendations with timestamp, action taken, outcome | History view | ✅ Done
| 21 | Risk data hook | `useRisk.ts` — fetch `/risk/{site_id}`, parse hourly risk ratings | Risk data | ✅ Done
| 22 | Optimize data hook | `useOptimize.ts` — fetch `/optimize/{site_id}`, get full action schedule | Optimization data | ✅ Done

---

### Phase 5 — Explainability Panel
| # | Task | Details | Output |
|---|------|---------|--------|
| 23 | Explain panel component | `ExplainPanel.tsx` — expandable card showing: "Why this recommendation?" with step-by-step reasoning | Explanation UI | ✅ Done
| 24 | Impact summary | Display ₹ savings and CO₂ avoided per recommendation, with icons and color coding | Impact metrics | ✅ Done
| 25 | Explanation hook | `useExplain.ts` — fetch `/explain/{site_id}`, render template-based explanations | Explanation data | ✅ Done

---

### Phase 6 — Scenario Simulator
| # | Task | Details | Output |
|---|------|---------|--------|
| 26 | Scenario controls | `ScenarioControls.tsx` — sliders/inputs: cloud cover delta (%), wind speed delta (%), battery SOC override (%) | Input controls | ✅ Done
| 27 | Run simulation button | Calls `/scenario/{site_id}` with perturbations, shows loading state | ✅ Done |
| 28 | Before/After comparison | Side-by-side view: original forecast vs. simulated forecast, original risk vs. simulated risk | Comparison view | ✅ Done |
| 29 | Scenario hook | `useScenario.ts` — manage perturbation state, call API, handle response | Scenario state | ✅ Done

---

### Phase 7 — Chart Library & Components
| # | Task | Details | Output |
|---|------|---------|--------|
| 30 | Recharts/ECharts setup | Configure chart library with custom theme (energy colors) | Chart system | ✅ Done
| 31 | Reusable chart components | `LineChart`, `AreaChart`, `BarChart`, `Gauge` — themed and responsive | Component library | ✅ Done
| 32 | Loading skeletons | Skeleton components for charts, cards, tables during data fetch | Loading states | ✅ Done
| 33 | Empty states | Friendly empty states when no site selected, no data, no forecast | UX polish | ✅ Done

---

### Phase 8 — Styling & Polish
| # | Task | Details | Output |
|---|------|---------|--------|
| 34 | Responsive design | Ensure dashboard works on desktop and tablet (1024px+) | Responsive layout | 🟡 In Progress
| 35 | Dark mode (optional) | If time permits, add dark mode toggle with Tailwind `dark:` classes | Dark theme | 🔲 Not Started
| 36 | Animations | Subtle transitions on card hover, chart data updates, risk level changes | Smooth UX | 🔲 Not Started
| 37 | Error handling | Toast notifications for API errors, network failures, upload failures | Error UX | ✅ Done
| 38 | Accessibility basics | Proper contrast ratios, keyboard navigation, ARIA labels | A11y | 🔲 Not Started

---

### Phase 9 — Integration & Testing
| # | Task | Details | Output |
|---|------|---------|--------|
| 39 | API integration test | Connect all hooks to live backend, verify full flow: upload → forecast → recommend → explain → simulate | Integration QA | 🔲 Not Started
| 40 | Demo flow walkthrough | Practice the 6-step demo flow from workflow.md §3 | Demo-ready | 🔲 Not Started
| 41 | Visual QA | Check all charts render correctly, no layout breaks, consistent theming | Visual QA | 🔲 Not Started
| 42 | Performance check | No unnecessary re-renders, charts load in < 500ms, smooth interactions | Performance QA | 🔲 Not Started

---

### Phase 10 — Professional UI & AI Assistant (Polished Design System)

| # | Task | Details | Status |
|---|------|---------|--------|
| 43 | `@` path alias | `tsconfig.json` (`baseUrl`/`paths`) + `vite.config.ts` `resolve.alias` → `./src` | ✅ Done |
| 44 | `cn()` utility | `src/lib/utils.ts` — `clsx` + `tailwind-merge` merge helper (shadcn standard) | ✅ Done |
| 45 | shadcn-style primitives | `src/components/ui/button.tsx` (cva variants + Radix Slot `asChild`), `ui/textarea.tsx` | ✅ Done |
| 46 | Tailwind design tokens | shadcn tokens added to `tailwind.config.js`: primary (energy green), muted, destructive, accent, border, input, ring, popover, card | ✅ Done |
| 47 | AI Copilot component | `ui/ruixen-moon-chat.tsx` — GridMind-branded dark glass assistant, Unsplash solar backdrop, auto-resizing textarea, live advisor hints | ✅ Done |
| 48 | AI Assistant page | New "AI Assistant" nav item + `AssistantPage` in `App.tsx` — quick actions route to Forecast/Risk/Optimize/Settings/Data, free-text sends route by keyword | ✅ Done |
| 49 | New dependencies | `lucide-react`, `@radix-ui/react-slot`, `class-variance-authority`, `clsx`, `tailwind-merge`, `@types/recharts` (dev) | ✅ Done |
| 50 | Build clean | Fixed pre-existing TS errors: hooks `number`→`string` site IDs, removed stale response-type imports, Layout string comparison, recharts types | ✅ Done |
| 51 | Landing page | `components/landing/LandingPage.tsx` — dark monochrome landing: hero w/ solar backdrop + stats strip, feature grid, how-it-works, live AI Copilot preview, model pipeline, CTA, footer | ✅ Done |
| 52 | Auth modal + dark app theme | Landing has integrated sign-in/signup modal (demo creds inlined); dashboard wrapped in `.app-dark` CSS-variable theme (dark sidebar, cards, inputs, selects) | ✅ Done |
| 53 | White theme (autodevs.dev reference) | Open-source reference site audited → light palette in `index.css` roots: bg `#faf7f2`, surface `#ffffff`, text `#18181b`/`#52525b`, primary blue `#2563eb`, borders `#00000014`, glass `#ffffffd1` + 20px blur; removed `.app-dark`; blue hover/focus rings | ✅ Done |
| 54 | Reference fonts | Google Fonts: **Space Grotesk** (headings via global `h1–h4` / `.page-title` / `.card-title` / `.kpi-value`, JetBrains Mono for stats/credentials), Inter body | ✅ Done |
| 55 | AI Copilot → **floating & constant** | Removed "AI Assistant" nav item + `AssistantPage`; new `FloatingAssistant` fixed bottom-right on every page — 14×14 blue circular toggle + `GridMindAssistant` **compact variant** (`onClose` added; white glass, blue accents) | ✅ Done |
| 56 | No emojis — lucide icons only | All emojis replaced in `App.tsx`: sidebar nav (LayoutDashboard/TrendingUp/ShieldAlert/Zap/ScanSearch/Database/Settings), KPIs, empty states, anomaly icons (TrendingUp/Down, Link2, Power, Thermometer, Crosshair), lambda diagram (RefreshCw/Package/Zap/Shuffle/BarChart3), buttons | ✅ Done |
| 57 | Landing rewritten to white | `LandingPage.tsx` light rewrite: off-white bg, blue CTAs, glass stat cards, white auth modal, Space Grotesk headlines, JetBrains Mono creds | ✅ Done |

---

## Key Deliverables

- ✅ 1. **Working React application** with responsive dashboard — Vite + React + TypeScript + Tailwind initialized (Phase 0)
- ✅ 2. **Site management** — registration form, CSV upload, site selector — Layout with site context, CSVUpload and SiteForm components referenced (Phases 1–2)
- ✅ 3. **Forecast visualization** — charts with uncertainty bands (P10/P50/P90), time horizon selector — ForecastChart with Recharts, horizon tabs in App.tsx (Phase 3)
- ✅ 4. **Risk dashboard** — hourly risk timeline, color-coded banners — RiskTimeline component referenced, useRisk.ts hook, RiskBanner design ready (Phase 4)
- ✅ 5. **Recommendation panel** — current action, explanation, impact metrics — RecommendationCard component, useOptimize.ts hook, financial/CO₂ impact estimates (Phase 4–5)
- ✅ 6. **Scenario simulator** — perturbation controls, before/after comparison — ScenarioControls component, useScenario.ts hook, Scenario API integration (Phase 6)
- 7. **Consistent theming** — energy-themed color system (green/amber/red), polished UX — Tailwind config with energy colors, energy-green palette applied (Phase 8)
- ✅ 8. **Loading/error states** — skeletons, empty states, toast notifications — LoadingSkeleton, ErrorToast, react-hot-toast configured (Phase 8)
- ✅ 9. **Professional design system** — shadcn-style components, `@` path alias, Tailwind design tokens, `npm run build` passes clean with zero TS errors (Phase 10)
- ✅ 10. **AI Copilot** — GridMind-branded chat assistant with energy-domain quick actions wired to Forecast/Risk/Optimize/Settings/Data pages (Phase 10)
- ✅ 11. **Floating AI Copilot + white theme + lucide icons** — assistant persistent on every page (compact floating widget, `onClose`), open-source reference-driven light theme (Space Grotesk / Inter / JetBrains Mono, `#faf7f2` bg, `#2563eb` primary), zero emojis — all shadcn/lucide icons (Phase 10)
- ✅ 12. **Backend hardening (blueprint audit)** — Pydantic input validation on schemas (email/password/lat-long/capacity/role bounds), horizon query clamp 1–168h, CSV upload size (10 MB) & row (1M) limits, signup role fixed `admin→viewer` (no self-escalation) (Phase 11)
- ✅ 13. **Forecast Intelligence API + page** — `GET /api/insights/{id}/accuracy` (MAE/RMSE/MAPE/R² per 24/48/72h via `evaluate()`), `GET /api/insights/model` (MLOps health), `GET /api/alerts` (risk/weather/storage alerts + channels), `GET /api/insights/{id}/weather` (drivers, impact, data quality/staleness); all owner-scoped; new Insights page in App.tsx (reliability KPIs, per-horizon bars, alerts feed, model status ring, weather drivers) + copilot keyword/quick-action routing (Phase 11)

---

## Detailed Task Tracker (42 Tasks)

| # | Task | Details | Status |
|---|------|---------|--------|
| 1 | Initialize React project | Create `frontend/` directory with Vite + React + TypeScript | Working React app | ✅ Done
| 2 | Install dependencies | Tailwind CSS, Recharts, axios, react-router-dom, react-hot-toast | ✅ Done |
| 3 | Configure Tailwind | Set up `tailwind.config.js` with custom theme (energy color palette: green/amber/red) | Styled system | ✅ Done
| 4 | Set up API client | `frontend/src/api/client.ts` — axios instance pointing to `http://localhost:8000` | API layer ready | ✅ Done
| 5 | App layout | `App.tsx` — sidebar + main content area responsive layout | Layout shell | ✅ Done
| 6 | Sidebar navigation | Site selector dropdown, nav links: Dashboard, Forecast, Risks, Optimize, Settings | Navigation | ✅ Done
| 7 | Theme & branding | "GridMind AI" header, energy-themed color scheme (green/amber/red for status) | Branded UI | ✅ Done
| 8 | Site registration form | `SiteForm.tsx` — inputs: site name, capacity (kW), location (lat/lon), battery size (kWh), export limit (kW) | Form component | ✅ Done
| 9 | CSV upload component | `CSVUpload.tsx` — drag-and-drop CSV upload with preview table, column mapping | Upload widget | ✅ Done
| 10 | Site list page | `SiteList.tsx` — cards showing all registered sites with status indicators | Site overview | ✅ Done
| 11 | Site selection context | React context for active site, persist in localStorage | Global state | ✅ Done
| 12 | Forecast chart component | `ForecastChart.tsx` — line chart: actual vs P50 vs P10-P90 band | ✅ Done |
| 13 | Time horizon selector | Tabs: 24h / 48h / 72h — update chart on selection | Horizon toggle | ✅ Done
| 14 | Solar + Wind overlay | Dual-axis or separate panels for solar and wind generation | Multi-source view | ✅ Done
| 15 | Forecast data hook | `useForecast.ts` — fetch `/forecast/{site_id}` on mount, handle loading/error | Data hook | ✅ Done
| 16 | Key metrics cards | Top row: Current Generation, Forecast (next 24h peak), Confidence Level, Hours to Surplus | KPI cards | ✅ Done
| 17 | Risk banner component | `RiskBanner.tsx` — color-coded banner (green/amber/red) showing current risk level for each hour | Visual alert | ✅ Done
| 18 | Hourly risk timeline | Horizontal bar chart showing risk level per hour over forecast window | Risk visualization | ✅ Done
| 19 | Recommendation card | `RecommendationCard.tsx` — current action with icon, why, estimated impact | Action card | ✅ Done
| 20 | Action history table | Table showing past recommendations with timestamp, action taken, outcome | History view | ✅ Done
| 21 | Risk data hook | `useRisk.ts` — fetch `/risk/{site_id}`, parse hourly risk ratings | Risk data | ✅ Done
| 22 | Optimize data hook | `useOptimize.ts` — fetch `/optimize/{site_id}`, get full action schedule | Optimization data | ✅ Done
| 23 | Explain panel component | `ExplainPanel.tsx` — expandable card showing: "Why this recommendation?" with step-by-step reasoning | Explanation UI | ✅ Done
| 24 | Impact summary | Display ₹ savings and CO₂ avoided per recommendation, with icons and color coding | Impact metrics | ✅ Done
| 25 | Explanation hook | `useExplain.ts` — fetch `/explain/{site_id}`, render template-based explanations | Explanation data | ✅ Done
| 26 | Scenario controls | `ScenarioControls.tsx` — sliders/inputs: cloud cover delta (%), wind speed delta (%), battery SOC override (%) | Input controls | ✅ Done
| 27 | Run simulation button | Calls `/scenario/{site_id}` with perturbations, shows loading state | ✅ Partially Done |
| 28 | Before/After comparison | Side-by-side view: original forecast vs. simulated forecast, original risk vs. simulated risk | Comparison view | ✅ Done |
| 29 | Scenario hook | `useScenario.ts` — manage perturbation state, call API, handle response | Scenario state | ✅ Done
| 30 | Recharts/ECharts setup | Configure chart library with custom theme (energy colors) | Chart system | ✅ Done
| 31 | Reusable chart components | `LineChart`, `AreaChart`, `BarChart`, `Gauge` — themed and responsive | Component library | ✅ Done
| 32 | Loading skeletons | Skeleton components for charts, cards, tables during data fetch | Loading states | ✅ Done
| 33 | Empty states | Friendly empty states when no site selected, no data, no forecast | UX polish | ✅ Done
| 34 | Responsive design | Ensure dashboard works on desktop and tablet (1024px+) | Responsive layout | 🟡 In Progress
| 35 | Dark mode (optional) | If time permits, add dark mode toggle with Tailwind `dark:` classes | Dark theme | 🔲 Not Started
| 36 | Animations | Subtle transitions on card hover, chart data updates, risk level changes | Smooth UX | 🔲 Not Started
| 37 | Error handling | Toast notifications for API errors, network failures, upload failures | Error UX | ✅ Done
| 38 | Accessibility basics | Proper contrast ratios, keyboard navigation, ARIA labels | A11y | 🔲 Not Started
| 39 | API integration test | Connect all hooks to live backend, verify full flow: upload → forecast → recommend → explain → simulate | Integration QA | 🔲 Not Started
| 40 | Demo flow walkthrough | Practice the 6-step demo flow from workflow.md §3 | Demo-ready | 🔲 Not Started
| 41 | Visual QA | Check all charts render correctly, no layout breaks, consistent theming | Visual QA | 🔲 Not Started
| 42 | Performance check | No unnecessary re-renders, charts load in < 500ms, smooth interactions | Performance QA | 🔲 Not Started

## Dependencies from Module 1

- API contract: endpoint URLs, request/response schemas (provide early, Hour 4)
- Sample/mock API responses for parallel development (provide by Hour 6)
- CORS enabled on backend

---

## Component Architecture

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── Layout.tsx
│   ├── site/
│   │   ├── SiteForm.tsx
│   │   ├── CSVUpload.tsx
│   │   └── SiteList.tsx
│   ├── forecast/
│   │   ├── ForecastChart.tsx
│   │   ├── HorizonSelector.tsx
│   │   └── MetricCards.tsx
│   ├── risk/
│   │   ├── RiskBanner.tsx
│   │   └── RiskTimeline.tsx
│   ├── recommendation/
│   │   ├── RecommendationCard.tsx
│   │   ├── ExplainPanel.tsx
│   │   └── ImpactSummary.tsx
│   ├── scenario/
│   │   ├── ScenarioControls.tsx
│   │   └── ScenarioComparison.tsx
│   └── common/
│       ├── LoadingSkeleton.tsx
│       ├── EmptyState.tsx
│       └── ErrorToast.tsx
├── hooks/
│   ├── useForecast.ts
│   ├── useRisk.ts
│   ├── useOptimize.ts
│   ├── useExplain.ts
│   ├── useScenario.ts
│   └── useSite.ts
├── api/
│   └── client.ts
├── context/
│   └── SiteContext.tsx
├── pages/
│   ├── Dashboard.tsx
│   ├── Forecast.tsx
│   ├── Risks.tsx
│   ├── Optimize.tsx
│   └── Settings.tsx
└── App.tsx
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Backend not ready in time | Build with mock data first, swap to live API later |
| Chart rendering performance | Use Recharts (lighter) over ECharts if performance issues |
| Responsive design issues | Mobile-first approach, test on tablet breakpoint early |
| Scope creep in UI | Focus on demo flow (6 steps), cut extras if behind |
