"""
ats_updater.py — Auto-updates ATS/recruiter technique intelligence every 30 days.

Queries Claude Haiku for current AI-era recruitment best practices and caches
the result in ats_techniques_cache.json. Included as context in every resume
generation prompt so the agent stays current as hiring AI evolves.

Refresh cadence: every 30 days automatically on first run of the week.
"""

import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
ATS_CACHE_FILE = BASE_DIR / "ats_techniques_cache.json"
ATS_REFRESH_DAYS = 30


# Default baseline (used if Anthropic API is unavailable)
DEFAULT_TECHNIQUES = """
ATS & AI Recruiter Best Practices (2025-2026 baseline):

SEMANTIC MATCHING (transformer-based ATS: LinkedIn AI, Workday, Greenhouse AI):
- Mirror exact phrases from the job description — not synonyms, exact strings
- Skill clusters (e.g., "Spring Boot + AWS Lambda + Microservices") score higher than isolated keywords
- Job title in summary should echo the exact posting title

QUANTIFIED IMPACT (critical differentiator in AI ranking):
- Include at least 3 numbers in top experience role: scale (users/transactions), performance (latency%), velocity (time saved)
- Format: action verb + technology + quantified result (e.g., "reduced API latency by 35%")
- ATS models trained on FAANG job descriptions weight $, %, and numeric scale heavily

FORMAT REQUIREMENTS (parser compatibility):
- Single-column layout only — multi-column causes 40%+ parsing errors in Workday ATS
- Standard fonts (Calibri, Arial, Times) — exotic fonts cause character garbling
- Sections labeled exactly: Professional Summary, Technical Skills, Professional Experience, Education
- No tables, text boxes, headers/footers with content, or images in text flow

SKILLS SECTION:
- Front-load skills that appear in the JD in the first 3 groups shown
- Separate technical categories clearly (Backend, Cloud, Frontend, etc.)
- Include both full names and abbreviations: "Java Spring Boot (Spring WebFlux, Project Reactor)"

AI TOOLS SIGNAL (strong positive in 2026):
- Listing Amazon Q, GitHub Copilot, Claude Code signals AI-augmented productivity
- Recruiters in 2026 filter FOR candidates who use AI tools actively

CAREER TRAJECTORY SIGNAL:
- Show progression: years of exp + company names + recency of relevant tech
- Principal/Staff roles: emphasize architecture decisions, system design, scale
- Senior roles: emphasize technical execution, cross-team impact, measurable delivery

HUMAN RECRUITER ENGAGEMENT (after passing ATS):
- Company-specific fit statement in summary — shows research, not template spam
- Named projects and real systems (not generic descriptions)
- GitHub link on resume — active repos are checked by technical recruiters
""".strip()


def get_current_ats_techniques():
    """Return current ATS techniques from cache or refresh via Claude Haiku.

    Called at the start of each agent run. If the cache is older than 30 days,
    queries Claude Haiku for updated techniques and saves to cache.
    Fallback: returns the built-in default baseline if API is unavailable.
    """
    cache = _load_cache()
    if cache and not _is_stale(cache):
        return cache.get("techniques", DEFAULT_TECHNIQUES)

    # Try to refresh via Claude Haiku
    refreshed = _refresh_from_haiku()
    if refreshed:
        _save_cache(refreshed)
        return refreshed

    return cache.get("techniques", DEFAULT_TECHNIQUES) if cache else DEFAULT_TECHNIQUES


def _load_cache():
    if ATS_CACHE_FILE.exists():
        try:
            return json.loads(ATS_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _is_stale(cache):
    try:
        last = datetime.date.fromisoformat(cache.get("last_updated", "2000-01-01"))
        return (datetime.date.today() - last).days >= ATS_REFRESH_DAYS
    except Exception:
        return True


def _save_cache(techniques):
    data = {
        "last_updated": datetime.date.today().isoformat(),
        "next_refresh": (
            datetime.date.today() + datetime.timedelta(days=ATS_REFRESH_DAYS)
        ).isoformat(),
        "techniques": techniques,
    }
    ATS_CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _refresh_from_haiku():
    """Query Claude Haiku for the latest ATS techniques. Returns None on failure."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        today = datetime.date.today()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            messages=[{
                "role": "user",
                "content": (
                    f"You are a recruiting expert specializing in AI-powered ATS systems "
                    f"as of {today.strftime('%B %Y')}. "
                    "List the TOP 15 most impactful techniques that make a senior software "
                    "engineer's resume rank highest in AI recruiter systems like LinkedIn AI, "
                    "Workday AI, Greenhouse, HireVue, and Lever in use today. "
                    "Include: semantic keyword matching, quantified achievements, format rules, "
                    "skill taxonomy signals, career trajectory indicators, and AI tool signals. "
                    "Be specific, current, and actionable. Format as a structured bullet list "
                    "grouped by category."
                ),
            }],
        )
        techniques = msg.content[0].text.strip()
        print(f"  [ats_updater] Refreshed ATS techniques from Claude Haiku ({today})")
        return techniques
    except Exception as e:
        print(f"  [ats_updater] Haiku refresh failed: {e}. Using cached/default techniques.")
        return None


def get_cache_status():
    """Return a dict describing the cache state (for logging)."""
    cache = _load_cache()
    if not cache:
        return {"status": "no_cache", "using": "default_baseline"}
    stale = _is_stale(cache)
    return {
        "status": "stale" if stale else "fresh",
        "last_updated": cache.get("last_updated"),
        "next_refresh": cache.get("next_refresh"),
        "using": "refreshing" if stale else "cached",
    }
