# 🤖 JobHunter Agent — Autonomous Job Application Powered by Claude AI

> **Proof of concept:** Building a fully autonomous job application agent using Anthropic's Claude AI, Cowork scheduled tasks, and MCP connectors — zero human intervention required after setup.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Claude AI](https://img.shields.io/badge/Claude-Haiku%20%7C%20Sonnet-orange?logo=anthropic)](https://anthropic.com)
[![Cowork](https://img.shields.io/badge/Cowork-Scheduled%20Tasks-purple)](https://claude.ai/download)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🧠 What Is This?

This project is an **experiment in agentic AI** — using Claude as the reasoning engine to automate an entire job search pipeline from end to end, every week, without human input.

The agent wakes up every **Wednesday at 10am**, searches multiple job boards, generates a **custom-tailored resume for each position using Claude Haiku**, applies autonomously via LinkedIn Easy Apply, and sends a full HTML digest to your inbox — all while you're doing something else.

This was built to answer one question: **how far can you push Claude to act as a truly autonomous agent for a real-world, multi-step workflow?**

The answer: pretty far.

---

## 🎬 What the Agent Does (Full Pipeline)

```
Every Wednesday at 10:03 AM
         │
         ▼
┌─────────────────────────────────┐
│  Phase 0 — Pre-flight checks    │
│  • MCP health probe             │
│  • LinkedIn session verification│
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Phase 1 — Job Search           │
│  • Indeed MCP                   │
│  • Dice MCP                     │
│  • ZipRecruiter MCP             │
│  • Filter: location, seniority  │
│  • Cross-MCP deduplication      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Phase 2 — Resume Generation    │
│  • Claude Haiku personalizes    │
│    summary for each JD          │
│  • STAR-method achievement      │
│    bullets with metrics         │
│  • Skills auto-reordered by     │
│    relevance to the JD          │
│  • Cover letter generated       │
│  • Match% score calculated      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Phase 3 — LinkedIn Easy Apply  │
│  • Claude in Chrome navigates   │
│  • Fills form autonomously      │
│  • Uploads personalized resume  │
│  • Submits without confirmation │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Phase 4 — Email Digest         │
│  • HTML email with two sections │
│    ✅ Applied (green)           │
│    📋 Resume Ready (orange)     │
│  • Sorted by Match%             │
│  • Gmail draft created via MCP  │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Phase 5 — Dashboard Update     │
│  • Live Cowork artifact refreshed│
│  • Bar chart: apps by source    │
│  • Doughnut: apps by priority   │
│  • Full table: Match%, status,  │
│    salary, source per job       │
│  • Persistent — stays updated   │
│    across sessions              │
│                                 │
│  Open anytime:                  │
│  "Show my job dashboard"        │
└─────────────────────────────────┘
```

---

## ✨ Key Features & Benefits

| Feature | Benefit |
|---|---|
| 🔍 **Multi-board search** | Covers Indeed, Dice, ZipRecruiter + LinkedIn in one run |
| 🧠 **AI resume personalization** | Each resume mirrors the exact language of the job description — built for AI-era ATS systems |
| ✍️ **Cover letter generation** | Claude Haiku writes a tailored one-paragraph letter per application |
| 🎯 **Match % scoring** | Know before applying how well you match each role (0–100) |
| 🔁 **Zero duplication** | Cross-MCP dedup by URL normalization and company+title pair |
| 🔒 **Thread-safe logging** | Atomic file writes with cross-platform FileLock (`os.O_EXCL`) |
| 📊 **Live dashboard** | Cowork artifact with Chart.js — applications by source, priority, and status |
| 🧪 **Dry-run mode** | Full pipeline simulation without submitting anything |
| 🗓️ **Fully scheduled** | Runs automatically every Wednesday at 10am via Cowork |
| 📬 **Email digest** | Weekly HTML summary with every application's status, salary, and resume link |
| 🧹 **Auto-cleanup** | Personalized resumes older than 90 days are deleted automatically |
| 📈 **ATS optimization** | Resume techniques refresh monthly via Claude Haiku to stay current with AI recruiters |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| AI reasoning | Claude Sonnet (agent orchestration) + Claude Haiku (resume + cover letter generation) |
| Scheduling | Cowork desktop app + scheduled tasks (cron) |
| Job search | Indeed MCP, Dice MCP, ZipRecruiter MCP |
| Browser automation | Claude in Chrome extension (LinkedIn Easy Apply) |
| Email | Gmail MCP (draft creation) |
| Resume generation | `python-docx` — single-column Calibri layout, ATS-optimized |
| Language | Python 3.10+ |
| Logging | Rotating file logs + `run_history.json` (last 52 runs) |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Cowork](https://claude.ai/download) desktop app
- Claude in Chrome browser extension
- MCP connectors configured: Indeed, Dice, ZipRecruiter, Gmail
- An Anthropic API key (for Claude Haiku resume generation)

### Clone the Repository

```bash
git clone https://github.com/silveiraSoft/agent-linkedin-candidate.git
cd agent-linkedin-candidate
```

### Install Dependencies

```bash
pip install anthropic python-docx
```

Dependencies auto-install on first run via `ensure_deps()` if missing.

### Configure Candidate Profile

Edit the `CANDIDATE` dictionary in `linkedin_agent.py`:

```python
CANDIDATE = {
    "name": "Your Name",
    "email": "your@email.com",
    "linkedin": "https://www.linkedin.com/in/yourprofile/",
    "github": "https://github.com/yourusername",
    "address": "Your Address",
    "phone": "+1 (XXX) XXX-XXXX",
    "skills": ["Java", "Spring Boot", "AWS", ...],
    ...
}
```

### Place Your Base Resume

Copy your base `.docx` resume to the project root:
```
agent-linkedin-candidate/
└── YourName-Resume-2026-ATS.docx   ← your base resume
```

Update `BASE_RESUME` in `linkedin_agent.py` to point to it.

### Run Manually (On Demand)

Running the agent manually takes **3 steps and one click**:

---

**Step 1 — Open what's needed**

| Requirement | Why |
|---|---|
| Cowork running in background | Claude needs it to execute |
| Chrome open + Claude in Chrome connected | Required for LinkedIn Easy Apply |
| LinkedIn session active in Chrome | Agent navigates it directly |

---

**Step 2 — Tell Claude in Cowork:**

```
"Ejecuta el agente de empleos ahora"
```

Claude handles everything automatically:
- ✅ Searches Indeed, Dice, ZipRecruiter via MCPs
- ✅ Filters by location, seniority, deduplication
- ✅ Generates a personalized resume + cover letter per job (Claude Haiku)
- ✅ Applies on LinkedIn via Easy Apply (Chrome automation)
- ✅ Logs every application with status, match%, source
- ✅ Creates the weekly email draft in Gmail
- ✅ Updates the live dashboard

---

**Step 3 — Send the email (only manual action required)**

1. Open Gmail → **Drafts (Borradores)**
2. Open the draft: `Weekly Job Applications — Week of {date}`
3. Click **Send**

> The Gmail MCP can only create drafts — sending requires one click from you.

---

**After running — check your dashboard:**

```
"Muéstrame el dashboard de empleos"
```

---

**Advanced CLI options (terminal):**

```bash
# Dry-run — simulate the full pipeline without submitting anything:
python linkedin_agent.py --jobs-file jobs_input.json --dry-run

# Update a job status after a manual Easy Apply:
python linkedin_agent.py --update-status "job-id" applied

# Build the email digest for a specific run:
python linkedin_agent.py --build-email --run-id <run_id>

# Clean up personalized resumes older than 90 days:
python linkedin_agent.py --cleanup --days 90
```

### Schedule Weekly Runs (Cowork)

Create a Cowork scheduled task pointing at `AGENT_TASK_PROMPT.md` with cron `0 10 * * 3` (Wednesdays 10am).

For automatic runs, keep open:
1. Cowork app running in background
2. Chrome with Claude in Chrome extension connected
3. LinkedIn session active in Chrome

---

## 📁 Project Structure

```
agent-linkedin-candidate/
├── linkedin_agent.py           # Main agent — 1233 lines, v3
├── agent_logger.py             # 3-stream rotating log system
├── ats_updater.py              # Monthly ATS technique refresh via Claude Haiku
├── regenerate_resumes.py       # Utility: re-generate resumes with updated formatting
├── AGENT_TASK_PROMPT.md        # Scheduled task instructions (filters, workflow, auth)
├── INSTRUCCIONES_OPERACION.md  # Full operation guide
├── applications_log.json       # Master deduplication + status log
├── ats_techniques_cache.json   # ATS techniques (auto-refreshed monthly)
├── resume-personalized/        # AI-generated resumes and cover letters
│   ├── {Company}-{Role}-{date}.docx
│   └── {Company}-{Role}-{date}-CoverLetter.txt
└── logs/
    ├── run_history.json        # Last 52 run summaries
    ├── mcp_health.json         # MCP health probe results
    ├── errors.log
    └── execution_{mode}.log
```

---

## 🎯 Job Filters (Configurable)

| Filter | Default | Configurable? |
|---|---|---|
| Location | 28-mile radius from Hialeah FL, or Remote USA | ✅ Yes |
| Cities in radius | Miami, Hialeah, Doral, Kendall, Coral Gables, Aventura... | ✅ Yes |
| Role levels | Junior · Mid · Senior · Principal · Staff (IC only) | ✅ Yes |
| Excluded roles | Team Lead · Manager · Director · VP · Head of | ✅ Yes |
| Salary (auto-estimated) | Senior: $145–170k · Principal: $165–195k | ✅ Yes |

---

## 📍 Configuring Location & Search Radius

All location settings live in a **single block** at the top of `linkedin_agent.py` — no hunting through the code:

```python
LOCATION_CONFIG = {
    "base_address":      "6955 NW 186th St, Hialeah, FL 33015",  # ← your home address
    "radius_miles":      28,                                       # ← miles from that address
    "cities_in_radius": [                                          # ← cities within that radius
        # Miami-Dade County
        "miami", "hialeah", "doral", "kendall", "coral gables",
        "miami lakes", "miami gardens", "north miami", "opa-locka",
        "sweetwater", "medley", "aventura",
        # South Broward (within 28mi of Hialeah)
        "pembroke pines", "miramar", "hollywood, fl", "hallandale",
        "sunrise, fl", "plantation, fl", "davie, fl", "cooper city",
    ],
}
```

Change any of these three values and the entire agent updates automatically — the job filter, the resume location preference, and the email digest footer all read from this single config.

### When to update each field

| Scenario | What to edit |
|---|---|
| You moved to a new city | `base_address` + rebuild `cities_in_radius` for the new location |
| You want to cover more area | Increase `radius_miles` + add more cities to `cities_in_radius` |
| You want a tighter area | Decrease `radius_miles` + remove cities from `cities_in_radius` |
| Remote only, no on-site | Set `cities_in_radius` to `[]` |
| Specific cities only | List exactly those cities in `cities_in_radius` regardless of radius |

> ⚠️ **Important:** `cities_in_radius` is what the agent actually uses to filter jobs.
> If you change `radius_miles` but not `cities_in_radius`, the filter won't change.
> Always keep both in sync.

---

---

## 📊 Live Dashboard

One of the standout features of this agent is its **live Cowork artifact dashboard** — a persistent, auto-refreshing view of every job application, built with Chart.js and rendered directly inside the Cowork interface.

### How to open it

Just ask Claude in Cowork:
```
"Muéstrame el dashboard de empleos"
```
or
```
"Refresh my job agent dashboard"
```

### What you see

```
┌─────────────────────────────────────────────────────────────┐
│  📋 Job Application Dashboard                    [Refresh]  │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  Total       │  ✅ Applied  │  📄 Resume   │  ❌ Errors    │
│    7         │     1        │   Ready: 6   │     0         │
├──────────────┴──────────────┴──────────────┴───────────────┤
│                                                             │
│  Applications by Source          Applications by Priority   │
│  ┌──────────────────────┐       ┌──────────────────────┐   │
│  │  ████ ZipRecruiter 4 │       │    ◉ HIGH   3 (43%)  │   │
│  │  ██   Indeed      2  │       │    ◉ MEDIUM 2 (29%)  │   │
│  │  █    LinkedIn    1  │       │    ◉ LOW    2 (29%)  │   │
│  └──────────────────────┘       └──────────────────────┘   │
│             Bar chart                   Doughnut chart      │
├─────────────────────────────────────────────────────────────┤
│  Company        │ Role          │ Source  │ Match% │ Status │
│─────────────────┼───────────────┼─────────┼────────┼────────│
│  Fidelity       │ Sr Java Eng   │ Indeed  │  87%   │ ✅     │
│  TCS Fuel       │ Sr Software   │ Ziprecr │  82%   │ 📄     │
│  Keeper Security│ Backend Dev   │ Dice    │  74%   │ 📄     │
│  ...            │ ...           │ ...     │  ...   │ ...    │
└─────────────────────────────────────────────────────────────┘
```

### What makes it valuable

- **Real-time data** — reads `applications_log.json` live on every open, so the table always reflects the latest status
- **Match% column** — shows at a glance which roles are the strongest fit before you follow up
- **Source breakdown** — see which job board is producing the most results so you can optimize where the agent searches
- **Priority distribution** — understand your pipeline at a high level: how many HIGH vs MEDIUM vs LOW priority roles
- **Status badges** — ✅ Applied / 📄 Resume Ready / ❌ Error — color-coded for instant scanning
- **Persistent** — unlike a chat response that scrolls away, the artifact stays and can be reopened any time
- **No refresh needed** — every time you open it, it pulls the latest data from your log automatically

### Why a dashboard matters for job searching

Without visibility into your pipeline, you lose track of: which companies you applied to, which roles are strongest matches, whether the agent is actually working, and where your applications are coming from. The dashboard turns the agent's activity log into a **command center** you can check in 10 seconds.

---
## 💡 Lessons Learned Building This Agent

- **Architectural handoff matters** — Claude (MCP caller) and Python (executor) need an explicit contract. We used `jobs_input.json` as the boundary, and `--jobs-file` as the entry point.
- **Email timing is everything** — building the email before Easy Apply completes is a silent bug. The fix: explicit `--update-status` + `--build-email --run-id` as separate phases.
- **FileLock is non-negotiable** — concurrent writes to `applications_log.json` corrupt the file without atomic locking. Cross-platform `os.O_EXCL` solved it for both Windows and Linux.
- **run_id > date filtering** — runs that cross midnight (started before 12am, finished after) break date-based email filtering. A UUID per run fixes this permanently.
- **AI-era ATS systems read semantics** — LLMs evaluate resumes for semantic alignment with the JD, not just keyword presence. Having Claude Haiku mirror the JD's exact language and framing is measurably better than keyword stuffing.

---

## 🤝 Contributing

This is an exploratory project. PRs welcome — especially around:
- Support for additional job board MCPs
- Better match scoring (semantic embeddings vs keyword count)
- Resume section reordering beyond skill groups
- Interview scheduling automation

---

## 📄 License

MIT — use freely, build on it, share back.

---

*Built with ❤️ using [Claude AI](https://anthropic.com) + [Cowork](https://claude.ai/download) — 2026*
