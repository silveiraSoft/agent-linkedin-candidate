"""
LinkedIn Job Application Agent — Adalberto Silveira Napoles
============================================================
Runs weekly. For each job found:
  1. Generates a personalized resume tailored to that posting
  2. Saves it to resume-personalized/
  3. Applies via LinkedIn (Easy Apply) using Claude in Chrome
  4. Sends a weekly summary email via Gmail (draft — open Gmail to send)

Priorities:
  1. Backend Java (Spring Boot, WebFlux, reactive programming)
  2. Fullstack (React/Next.js + Spring Boot/Java)
  3. General match (broader skillset)

Location: Remote USA OR on-site within LOCATION_CONFIG["radius_miles"] miles of
          LOCATION_CONFIG["base_address"]
          (edit LOCATION_CONFIG below to change address and radius)

AI-Era Resume Strategy (2025-2026):
  - Semantic keyword matching for transformer-based ATS (Workday, Greenhouse, LinkedIn AI)
  - STAR-method bullets with quantified impact (auto-generated per job via Claude Haiku)
  - Dynamic skill-group reordering to front-load matched skills
  - ATS techniques auto-refreshed every 30 days (ats_updater.py)
  - Full logging: logs/errors.log, logs/applications_*.log, logs/execution_*.log

Usage:
  python linkedin_agent.py                              # demo run (sample jobs)
  python linkedin_agent.py --preflight [--jobs-file PATH]  # check prerequisites only
  python linkedin_agent.py --jobs-file PATH [--auto]    # process jobs from MCP JSON file
  python linkedin_agent.py --update-status JOB_ID STATUS  # update after Easy Apply
  python linkedin_agent.py --build-email [--run-id UUID]  # build email from run results
  python linkedin_agent.py --dry-run --jobs-file PATH   # simulate without side effects
  python linkedin_agent.py --cleanup [--days 90]        # manual resume cleanup
"""

import os
import json
import re
import subprocess
import sys
import datetime
import uuid
import time
import shutil
from pathlib import Path

# ── Dependencies ──────────────────────────────────────────────────────────────
def ensure_deps():
    pkgs = ["python-docx", "anthropic", "requests"]
    for pkg in pkgs:
        try:
            __import__(pkg.replace("-", "_").split(".")[0])
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg,
                                   "--break-system-packages", "-q"])

ensure_deps()

# ── Agent helper modules ──────────────────────────────────────────────────────
try:
    from agent_logger import setup_logging, get_loggers, log_job_result, log_email_result, log_run_summary
    from ats_updater import get_current_ats_techniques, get_cache_status
    _HELPERS_OK = True
except ImportError:
    _HELPERS_OK = False
    def setup_logging(mode="MANUAL"): return None, None, None
    def get_loggers(): return None, None, None
    def log_job_result(*a, **kw): pass
    def log_email_result(*a, **kw): pass
    def log_run_summary(*a, **kw): pass
    def get_current_ats_techniques(): return ""
    def get_cache_status(): return {}

import anthropic
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import requests

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
RESUME_DIR    = BASE_DIR / "resume-personalized"
RESUME_DIR.mkdir(exist_ok=True)
LOG_FILE      = BASE_DIR / "applications_log.json"
HISTORY_FILE  = BASE_DIR / "logs" / "run_history.json"
MCP_HEALTH    = BASE_DIR / "logs" / "mcp_health.json"
(BASE_DIR / "logs").mkdir(exist_ok=True)

CANDIDATE = {
    "name": "Adalberto Silveira Napoles",
    "email": "adalbertosn1982@gmail.com",
    "phone": "+1 (812) 901-8687",
    "linkedin": "https://www.linkedin.com/in/adalbertosilveiranapoles/",
    "github": "https://github.com/silveiraSoft",
    "location": "Hialeah, FL 33015",
    "address": "6955 NW 186th St, Hialeah, FL 33015",  # keep in sync with LOCATION_CONFIG["base_address"]
    "work_auth": "Authorized to work in USA (no sponsorship required)",
    "willing_to_relocate": False,
    "travel_availability": "50%",
    "notice_period": "1 month",
    "remote_preference": "__LOCATION_PREF_PLACEHOLDER__",
    "hispanic_latino": True,
    "disability": False,
    "veteran": False,
    "summary": (
        "Senior Software Engineer with 18+ years of experience designing and delivering "
        "enterprise and web applications across the full SDLC. Specialized in Java (8/11/17/21/25) "
        "and modern backend architectures using Spring Boot, Spring MVC, Spring WebFlux, Spring Data "
        "JPA/Hibernate, Spring Security, Spring Cloud, reactive programming with Project Reactor, and "
        "event-driven microservices on AWS (Lambda, SNS/SQS, S3, API Gateway, RDS, DynamoDB, Cognito). "
        "Services containerized with Docker, deployed to Kubernetes via Jenkins CI/CD. Active AI practitioner: "
        "developed autonomous job-application agent (Python, Claude/Anthropic API, multi-agent orchestration, "
        "retry logic, live dashboard) and AWS infrastructure monitor powered by Amazon Bedrock. "
        "Strong fullstack background with ReactJS, Next.js, Remix, Angular, TypeScript on Node 22. "
        "Fluent in English, Spanish, and Portuguese."
    ),
    "skills": [
        "Java 8/11/17/21/25", "Spring Boot", "Spring WebFlux", "Project Reactor",
        "Spring MVC", "Spring Security", "Spring Cloud", "Spring Data JPA/Hibernate",
        "Reactive Programming", "Microservices", "Event-Driven Architecture",
        "AWS Lambda", "AWS SNS/SQS", "AWS S3", "API Gateway", "RDS", "DynamoDB",
        "Amazon Cognito", "CloudWatch", "IAM", "Parameter Store",
        "ReactJS", "Next.js", "TypeScript", "Node.js 22", "Angular", "Remix",
        "Docker", "Kubernetes", "Jenkins", "CI/CD",
        "PostgreSQL", "MySQL", "Redis", "SQL Server", "Oracle",
        "Clean Architecture", "SOLID", "DDD", "CQRS",
        "OAuth 2.0", "JWT", "AES/RSA Encryption",
        "JUnit 5", "Mockito", "Postman", "SonarQube",
        "Amazon Q", "GitHub Copilot", "Claude Code",
        "Amazon Bedrock", "AI Agents / Claude API", "Python AI Orchestration", "Multi-Agent Systems",
        "REST APIs", "Git", "Agile/SCRUM",
    ],
    "experience": [
        {
            "company": "3HTP Cloud Services",
            "title": "Senior Java Full-Stack Software Engineer",
            "dates": "December 2021 - Present",
            "location": "Miami, FL (Remote)",
            "bullets": [
                "Architected cloud-native financial and identity-validation microservices using Java 17/21, Spring Boot, and Spring WebFlux (Project Reactor), handling 50,000+ daily transactions across 5 distributed services.",
                "Designed voice-biometric authentication mechanism for banking transactions (2023), integrating Spring Security and Amazon Cognito into Talos identity-validation platform -- zero security incidents since launch.",
                "Built event-driven microservice architectures on AWS (SNS/SQS, Lambda), achieving 99.9% uptime and processing real-time financial events with Redis caching and DynamoDB/PostgreSQL persistence.",
                "Optimized performance of legacy Java/Spring Boot systems (Logicalis LEX and SOLVER) using VisualVM and IntelliJ Profiler, reducing API response latency by 35% and cutting memory footprint by 25%.",
                "Designed distributed Complaints Management System with three Spring WebFlux reactive microservices coordinated via AWS SNS/SQS, reducing customer complaint resolution time by 40%.",
                "Implemented AES/RSA encryption and OAuth 2.0/JWT security protocols across microservices, securing 500,000+ encrypted records and passing all enterprise compliance audits.",
                "Full-stack architect on Proteccion digital savings platform -- Next.js + TypeScript frontend, Spring WebFlux backend on AWS, serving 200,000+ end users with sub-200ms response times.",
                "Containerized all microservices with Docker, deployed to Kubernetes with auto-scaling; managed Jenkins CI/CD pipelines with SonarQube quality gates, cutting deployment time from 45 to 12 minutes.",
            ],
        },
        {
            "company": "Cooper Tec",
            "title": "Senior Software Engineer",
            "dates": "May 2021 - November 2021",
            "location": "Brazil (Hybrid)",
            "bullets": [
                "Developed and maintained online card-management systems using PHP 8, PHPUnit, PostgreSQL, MySQL, SQL Server, Oracle, and Docker, serving 50,000+ cardholders.",
                "Designed AES/RSA security algorithm protecting front-end/back-end interactions, reducing unauthorized access attempts by 90% and achieving full PCI-DSS compliance.",
            ],
        },
        {
            "company": "UniCesumar",
            "title": "Senior Software Developer",
            "dates": "December 2016 - April 2021",
            "location": "Brazil (Hybrid)",
            "bullets": [
                "Developed large-scale academic and financial systems using PHP, Java, Spring Boot, JavaScript, and REST/SOAP APIs, supporting 80,000+ students and 2,000+ faculty members.",
                "Built two-step authentication system with Google Authenticator, reducing unauthorized account access by 95%; managed CI/CD with Docker, Git, and Jenkins.",
            ],
        },
        {
            "company": "Personal Projects (Open Source)",
            "title": "AI Systems Engineer",
            "dates": "2025 - Present",
            "location": "Miami, FL",
            "bullets": [
                "Engineered autonomous LinkedIn job-application agent (Python, Anthropic Claude API / Claude Agent SDK) with 4-phase orchestration: MCP-based job search, ATS-optimized resume generation via Claude Haiku, LinkedIn Easy Apply automation via Claude in Chrome, and retry logic with persistent error tracking — autonomously submitting tailored applications weekly to 50+ positions.",
                "Built AWS infrastructure monitoring system powered by Amazon Bedrock: intelligent resource-health analysis, anomaly detection, automated CloudWatch metric aggregation, and natural-language incident summaries — reducing mean time to detect (MTTD) for infrastructure issues.",
            ],
        },
    ],
    "education": [
        "Master in Business Informatics -- CUJAE, Havana, Cuba (2013)",
        "B.Sc. in Computer Sciences -- University of Santiago de Cuba (2006)",
    ],
}

# ── Search Priorities ──────────────────────────────────────────────────────────
SEARCH_PRIORITIES = [
    {
        "priority": 1,
        "label": "Backend Java (Spring Boot / Reactive)",
        "keywords": [
            "Java Spring Boot backend engineer",
            "Java reactive programming Spring WebFlux",
            "Senior Java backend microservices AWS",
            "Spring Boot Java developer Miami remote",
            "Java backend engineer Project Reactor",
        ],
        "required_terms": ["java", "spring"],
    },
    {
        "priority": 2,
        "label": "Fullstack React + Spring Boot",
        "keywords": [
            "fullstack Java React Spring Boot developer",
            "fullstack engineer Next.js Spring Boot Java",
            "senior fullstack Java React developer remote",
            "fullstack developer React Java Miami",
        ],
        "required_terms": ["java", "react"],
    },
    {
        "priority": 3,
        "label": "General Match (broader skills)",
        "keywords": [
            "senior software engineer AWS microservices remote",
            "senior engineer Docker Kubernetes Java AWS",
            "cloud engineer Java AWS microservices Miami",
        ],
        "required_terms": [],
    },
]

# ── Location Config — edit here to change address and radius ──────────────────
#
#  base_address   : full street address used as center of radius search
#  radius_miles   : how many miles from base_address to accept on-site jobs
#  cities_in_radius: city/area name keywords that fall within that radius —
#                    update this list whenever you change base_address or radius_miles
#
LOCATION_CONFIG = {
    "base_address":      "6955 NW 186th St, Hialeah, FL 33015",
    "radius_miles":      28,
    "cities_in_radius": [
        # Miami-Dade County
        "miami", "hialeah", "doral", "kendall", "coral gables",
        "miami lakes", "miami gardens", "north miami", "opa-locka",
        "sweetwater", "medley", "virginia gardens", "miami springs",
        "west miami", "south miami", "cutler bay", "aventura",
        # South Broward (within 28mi)
        "pembroke pines", "miramar", "hollywood, fl", "hallandale",
        "sunrise, fl", "sunrise fl", "city of sunrise",
        "plantation, fl", "plantation fl",
        "davie, fl", "davie fl",
        "cooper city",
    ],
}

# Legacy aliases — do not edit (used internally)
LOCATION_PARAMS = {
    "remote":             "remote",
    "candidate_address":  LOCATION_CONFIG["base_address"],
    "miami_radius_miles": LOCATION_CONFIG["radius_miles"],
}
LOCATION_KEYWORDS = LOCATION_CONFIG["cities_in_radius"]
# Patch CANDIDATE["remote_preference"] with live LOCATION_CONFIG values
CANDIDATE["remote_preference"] = (
    "Remote preferred; open to on-site within "
    + str(LOCATION_CONFIG["radius_miles"]) + " miles of "
    + LOCATION_CONFIG["base_address"]
)


LEADERSHIP_TITLE_KEYWORDS = [
    "team lead", "tech lead", "engineering lead", "lead engineer",
    "engineering manager", "software manager", "development manager",
    "director", "vp ", "vice president", "head of engineering",
    "head of software", "people manager", "staff manager",
    "delivery manager", "project manager", "program manager",
]

# ── Skill Groups ───────────────────────────────────────────────────────────────
SKILL_GROUPS = {
    "Backend": [
        "Java 8/11/17/21/25", "Spring Boot", "Spring WebFlux", "Project Reactor",
        "Spring MVC", "Spring Security", "Spring Cloud", "Spring Data JPA/Hibernate",
        "Reactive Programming", "Microservices", "Event-Driven Architecture", "REST APIs",
    ],
    "Cloud / AWS": [
        "AWS Lambda", "AWS SNS/SQS", "AWS S3", "API Gateway", "RDS", "DynamoDB",
        "Amazon Cognito", "CloudWatch", "IAM", "Parameter Store",
    ],
    "Frontend": ["ReactJS", "Next.js", "TypeScript", "Node.js 22", "Angular", "Remix"],
    "Databases": ["PostgreSQL", "MySQL", "Redis", "SQL Server", "Oracle"],
    "DevOps / Quality": ["Docker", "Kubernetes", "Jenkins", "CI/CD", "SonarQube", "JUnit 5", "Mockito"],
    "Architecture": ["Clean Architecture", "SOLID", "DDD", "CQRS", "OAuth 2.0", "JWT"],
    "AI Tools": ["Amazon Q", "GitHub Copilot", "Claude Code"],
}


# ── Resume Formatting Helpers ──────────────────────────────────────────────────

def _set_spacing(para, before=0, after=0):
    pPr = para._p.get_or_add_pPr()
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:before"), str(int(before * 20)))
    sp.set(qn("w:after"),  str(int(after  * 20)))
    pPr.append(sp)


def _add_section_heading(doc, text):
    NAVY = RGBColor(0x1F, 0x3A, 0x6E)
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = NAVY
    run.font.name = "Calibri"
    pPr = p._p.get_or_add_pPr()
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:before"), str(8 * 20))
    sp.set(qn("w:after"),  str(1 * 20))
    pPr.append(sp)
    pBdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "6")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "1F3A6E")
    pBdr.append(bot)
    pPr.append(pBdr)
    return p


def _sf(run, size=10.5, bold=False, color=None):
    run.font.name = "Calibri"
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = color


# ── Resume Personalization (AI-Era 2025-2026) ─────────────────────────────────

CANDIDATE_RESUME_TEXT = (
    "NAME: Adalberto Silveira Napoles\n"
    "CONTACT: adalbertosn1982@gmail.com | +1 (812) 901-8687 | Hialeah, FL 33015\n"
    "LINKEDIN: https://www.linkedin.com/in/adalbertosilveiranapoles/\n"
    "GITHUB: https://github.com/silveiraSoft\n\n"
    "PROFESSIONAL SUMMARY:\n"
    "Senior Software Engineer 18+ yrs. Java 8/11/17/21/25, Spring Boot, Spring WebFlux, "
    "Project Reactor, AWS (Lambda/SNS/SQS/S3/DynamoDB/Cognito), ReactJS, Next.js, TypeScript, "
    "Docker, Kubernetes, Jenkins. Financial, identity-validation, and savings platforms.\n\n"
    "SKILLS:\n"
    "Java, Spring Boot, Spring WebFlux, Project Reactor, Spring MVC, Spring Security, Spring Cloud, "
    "Spring Data JPA/Hibernate, Reactive Programming, Microservices, Event-Driven Architecture, "
    "AWS Lambda, SNS/SQS, S3, API Gateway, RDS, DynamoDB, Amazon Cognito, CloudWatch, "
    "ReactJS, Next.js, TypeScript, Node.js 22, Angular, Remix, Docker, Kubernetes, Jenkins, "
    "PostgreSQL, MySQL, Redis, OAuth 2.0, JWT, JUnit 5, Mockito, SonarQube\n\n"
    "CURRENT ROLE IMPACT (3HTP Cloud Services, 4+ years):\n"
    "- 50,000+ daily transactions across 5 distributed Java microservices\n"
    "- 99.9% uptime for event-driven AWS (SNS/SQS, Lambda) architecture\n"
    "- 35% API latency reduction via VisualVM/IntelliJ profiling\n"
    "- 500,000+ encrypted records secured with OAuth 2.0, JWT, AES/RSA\n"
    "- 200,000+ end users on Proteccion savings platform (Next.js + Spring WebFlux)\n"
    "- CI/CD deployment time cut from 45 to 12 minutes via Jenkins + Docker + K8s\n"
    "- Voice-biometric auth for banking (Amazon Cognito, Spring Security) -- zero security incidents\n\n"
    "EXPERIENCE:\n"
    "3HTP Cloud Services | Senior Java Full-Stack SE | Dec 2021-Present | Miami FL Remote\n"
    "Cooper Tec | Senior SE | May-Nov 2021 | Brazil Hybrid\n"
    "UniCesumar | Senior SD | Dec 2016-Apr 2021 | Brazil Hybrid\n"
    "ETECSA | Specialist B CS | Sep 2006-2010 | Cuba\n\n"
    "EDUCATION: Master Business Informatics CUJAE Cuba 2013 | BSc Computer Sciences USCU 2006\n"
    "AI TOOLS: Actively using Amazon Q, GitHub Copilot, Claude Code to accelerate development\n"
)


def matched_skills_for(job_description):
    jd = job_description.lower()
    return [s for s in CANDIDATE["skills"] if s.lower() in jd]


def reorder_skill_groups_for_job(job_description):
    jd = job_description.lower()
    scored = {group: sum(1 for item in items if item.lower() in jd)
              for group, items in SKILL_GROUPS.items()}
    return dict(sorted(SKILL_GROUPS.items(), key=lambda kv: -scored[kv[0]]))


def generate_personalized_summary(job_title, company, job_description, priority_label):
    try:
        client = anthropic.Anthropic()
        matched = matched_skills_for(job_description)[:15]
        matched_str = ", ".join(matched) if matched else "Java, Spring Boot, AWS"
        ats_context = get_current_ats_techniques()

        prompt = (
            "You are an expert resume writer for senior software engineers in 2026. "
            "Write a Professional Summary OPTIMIZED for AI/ATS recruiters using "
            "transformer-based semantic matching (LinkedIn AI, Workday AI, Greenhouse AI).\n\n"
            "CURRENT ATS BEST PRACTICES (auto-updated monthly):\n"
            + ats_context[:1500] + "\n\n"
            "CANDIDATE FACTS:\n"
            + CANDIDATE_RESUME_TEXT + "\n\n"
            "SKILLS MATCHING THIS JOB: " + matched_str + "\n\n"
            "TARGET JOB:\n"
            "- Company: " + company + "\n"
            "- Title: " + job_title + "\n"
            "- Category: " + priority_label + "\n"
            "- Job Description:\n" + job_description[:2000] + "\n\n"
            "WRITE a 4-5 sentence Professional Summary that:\n"
            "1. MIRRORS exact phrases and keywords from the job description naturally\n"
            "2. Opens with your STRONGEST match to THIS specific role\n"
            "3. Includes at least ONE quantified impact (18+ yrs, 50k+ transactions, 99.9% uptime, etc.)\n"
            "4. Mentions AI tool usage naturally (Amazon Q, GitHub Copilot, Claude Code)\n"
            "5. Ends with a company-specific or domain-specific fit statement\n"
            "6. Sounds HUMAN and specific -- NOT generic template language\n\n"
            "Return ONLY the summary paragraph text. No labels, no headers, no bullets."
        )
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"generate_personalized_summary failed ({e}); using base summary fallback"
        )
        return CANDIDATE["summary"]


def generate_tailored_bullets(job_title, company, job_description):
    try:
        client = anthropic.Anthropic()
        static_bullets = "\n".join("- " + b for b in CANDIDATE["experience"][0]["bullets"])
        ats_context = get_current_ats_techniques()

        prompt = (
            "You are an expert resume writer specializing in AI-era ATS optimization for 2025-2026.\n\n"
            "CURRENT ATS BEST PRACTICES:\n"
            + ats_context[:800] + "\n\n"
            "CANDIDATE 3HTP EXPERIENCE BULLETS (current baseline):\n"
            + static_bullets + "\n\n"
            "ADDITIONAL CANDIDATE METRICS:\n"
            "- Voice-biometric auth for banking (Spring Security + Amazon Cognito) -- zero incidents since 2023\n"
            "- AES/RSA encryption on 500,000+ encrypted records\n"
            "- 50,000+ daily transactions, 99.9% uptime, 35% API latency reduction\n"
            "- Proteccion platform: 200,000+ end users, sub-200ms response times\n"
            "- CI/CD: deployment time cut from 45 to 12 minutes (Jenkins + Docker + K8s)\n"
            "- AI-augmented: Amazon Q, GitHub Copilot, Claude Code daily\n\n"
            "TARGET JOB:\n"
            "- Company: " + company + "\n"
            "- Title: " + job_title + "\n"
            "- Key requirements:\n" + job_description[:2000] + "\n\n"
            "REWRITE into 6-7 STAR-method achievement bullets that:\n"
            "1. Use EXACT keyword phrases from the job description\n"
            "2. Include quantified results (scale, performance, reliability, velocity)\n"
            "3. Put the most relevant bullets FIRST for this specific job\n"
            "4. Reference real systems: Talos, Logicalis LEX, Proteccion, Complaints Mgmt\n"
            "5. Start each bullet with a strong action verb\n"
            "6. Sound human and specific\n\n"
            "Return ONLY the bullet list. Each line starts with - . No headers."
        )
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        bullets = [line.lstrip("-. ").strip()
                   for line in raw.split("\n")
                   if line.strip().startswith("-")]
        return bullets if bullets else CANDIDATE["experience"][0]["bullets"]
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"generate_tailored_bullets failed ({e}); using base bullets fallback"
        )
        return CANDIDATE["experience"][0]["bullets"]


def generate_resume_filename(company, job_title):
    today = datetime.date.today().strftime("%Y-%m-%d")
    c = re.sub(r"[^a-zA-Z0-9]+", "-", company).strip("-")[:25]
    t = re.sub(r"[^a-zA-Z0-9]+", "-", job_title).strip("-")[:35]
    return c + "-" + t + "-" + today + ".docx"


def create_personalized_resume(job_title, company, job_description, priority_label,
                                tailored_summary=None, tailored_bullets=None):
    if tailored_summary is None:
        tailored_summary = generate_personalized_summary(
            job_title, company, job_description, priority_label
        )
    if tailored_bullets is None:
        tailored_bullets = generate_tailored_bullets(job_title, company, job_description)

    ordered_skill_groups = reorder_skill_groups_for_job(job_description)

    NAVY = RGBColor(0x1F, 0x3A, 0x6E)
    GRAY = RGBColor(0x55, 0x55, 0x55)

    doc = Document()
    sec = doc.sections[0]
    sec.top_margin    = Inches(0.75)
    sec.bottom_margin = Inches(0.75)
    sec.left_margin   = Inches(0.8)
    sec.right_margin  = Inches(0.8)
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _sf(p.add_run(CANDIDATE["name"].upper()), size=20, bold=True, color=NAVY)
    _set_spacing(p, before=0, after=3)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _sf(p.add_run(CANDIDATE["email"] + "  |  " + CANDIDATE["phone"] + "  |  " + CANDIDATE["location"]),
        size=10, color=GRAY)
    _set_spacing(p, before=0, after=2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _sf(p.add_run("LinkedIn: " + CANDIDATE["linkedin"] + "  |  GitHub: " + CANDIDATE["github"]),
        size=9.5, color=GRAY)
    _set_spacing(p, before=0, after=4)

    _add_section_heading(doc, "PROFESSIONAL SUMMARY")
    p = doc.add_paragraph(tailored_summary)
    _sf(p.runs[0], size=10.5)
    _set_spacing(p, before=3, after=0)

    _add_section_heading(doc, "TECHNICAL SKILLS")
    for group, items in ordered_skill_groups.items():
        matched_in_group = [s for s in items if s in CANDIDATE["skills"]]
        if not matched_in_group:
            continue
        p = doc.add_paragraph()
        _sf(p.add_run(group + ": "), size=10.5, bold=True, color=NAVY)
        _sf(p.add_run(", ".join(matched_in_group)), size=10.5)
        _set_spacing(p, before=2, after=1)

    _add_section_heading(doc, "PROFESSIONAL EXPERIENCE")
    for i, exp in enumerate(CANDIDATE["experience"]):
        p = doc.add_paragraph()
        _sf(p.add_run(exp["company"]), size=11, bold=True, color=NAVY)
        _sf(p.add_run("  --  " + exp["location"]), size=10.5, color=GRAY)
        _set_spacing(p, before=6, after=1)
        p2 = doc.add_paragraph()
        _sf(p2.add_run(exp["title"]), size=10.5, bold=True)
        _sf(p2.add_run("  |  " + exp["dates"]), size=10, color=GRAY)
        _set_spacing(p2, before=0, after=2)
        bullets = tailored_bullets if i == 0 else exp["bullets"]
        for bullet in bullets:
            bp = doc.add_paragraph(style="List Bullet")
            _sf(bp.add_run(bullet), size=10.5)
            _set_spacing(bp, before=1, after=1)

    _add_section_heading(doc, "EARLIER EXPERIENCE")
    p = doc.add_paragraph()
    _sf(p.add_run(
        "ETECSA -- Cuba  |  Specialist B, Computer Science  |  Sep 2006 - 2010\n"
        "Custom CMS, academic training systems (SAGEC), PHP, JavaScript, MySQL, PostgreSQL."
    ), size=10.5)
    _set_spacing(p, before=3, after=0)

    _add_section_heading(doc, "EDUCATION")
    for edu in CANDIDATE["education"]:
        p = doc.add_paragraph()
        _sf(p.add_run(edu), size=10.5)
        _set_spacing(p, before=3, after=1)

    _add_section_heading(doc, "CERTIFICATIONS")
    for cert in [
        "AWS Partner Business (Accreditation)",
        "AWS Partner Technical (Accreditation)",
        "AWS Certified AI Practitioner -- in progress",
        "AWS Certified Developer - Associate -- in progress",
    ]:
        p = doc.add_paragraph()
        _sf(p.add_run("- " + cert), size=10.5)
        _set_spacing(p, before=2, after=1)

    _add_section_heading(doc, "ADDITIONAL INFORMATION")
    for line in [
        "Work Authorization: " + CANDIDATE["work_auth"],
        "Languages: English (fluent) - Spanish (native) - Portuguese (fluent)",
        "Location Preference: " + CANDIDATE["remote_preference"],
        "Notice Period: " + CANDIDATE["notice_period"] + "  |  Travel: " + CANDIDATE["travel_availability"],
        "AI Tools in active daily use: Amazon Q, GitHub Copilot, Claude Code",
    ]:
        p = doc.add_paragraph()
        _sf(p.add_run(line), size=10.5)
        _set_spacing(p, before=2, after=1)

    filename = generate_resume_filename(company, job_title)
    out = RESUME_DIR / filename
    doc.save(str(out))
    print("  Resume saved: " + filename)
    return out


# ── Application Log ────────────────────────────────────────────────────────────

def load_log():
    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_log(entries):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def already_applied(job_id, log):
    return any(e.get("job_id") == job_id for e in log)



# ── Run ID & File Locking ──────────────────────────────────────────────────────

def generate_run_id():
    """Unique ID per agent run — used to group log entries across midnight."""
    return str(uuid.uuid4())[:12]


class FileLock:
    """Cross-platform file lock using exclusive file creation (works on Windows + Linux)."""
    def __init__(self, filepath):
        self.lockpath = str(filepath) + ".lock"

    def __enter__(self):
        for _ in range(100):          # wait up to 10 s
            try:
                fd = os.open(self.lockpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return self
            except FileExistsError:
                time.sleep(0.1)
        # Force-remove stale lock (older than 60 s) and retry once
        try:
            if time.time() - os.path.getmtime(self.lockpath) > 60:
                os.unlink(self.lockpath)
        except OSError:
            pass
        return self

    def __exit__(self, *_):
        try:
            os.unlink(self.lockpath)
        except OSError:
            pass


def save_log_locked(entries):
    """Thread/process-safe JSON log write."""
    with FileLock(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)


# ── Input Validation & Cross-MCP Deduplication ────────────────────────────────

_REQUIRED_JOB_FIELDS = {"id", "title", "company", "url"}

def validate_jobs_input(jobs):
    """Validate and sanitize a list of job dicts from MCP search results.
    Returns (valid_jobs, skipped_count)."""
    valid, skipped = [], 0
    for job in jobs:
        if not isinstance(job, dict):
            skipped += 1
            continue
        # Ensure all required fields exist and are non-empty strings
        missing = [f for f in _REQUIRED_JOB_FIELDS if not job.get(f)]
        if missing:
            skipped += 1
            continue
        # Normalize fields
        job.setdefault("location", "")
        job.setdefault("description", "")
        job.setdefault("source", "Unknown")
        job.setdefault("salary", None)
        valid.append(job)
    return valid, skipped


def _normalize_url(url):
    """Strip query params and trailing slashes for dedup comparison."""
    url = re.sub(r"\?.*$", "", str(url))
    return url.rstrip("/").lower()


def deduplicate_jobs_cross_mcp(jobs, existing_log):
    """Remove duplicates within the batch and against the existing log.
    Deduplicates by: (1) normalized URL, (2) company+title pair.
    NOTE: status=error entries are intentionally EXCLUDED from seen sets
    so failed jobs can be retried on subsequent runs."""
    # Only non-error entries block re-processing
    processed = [e for e in existing_log if e.get("status") != "error"]
    seen_urls    = {_normalize_url(e.get("url", "")) for e in processed}
    seen_ids     = {e.get("job_id", "") for e in processed}
    seen_pairs   = {(e.get("company", "").lower(), e.get("title", "").lower()) for e in processed}
    batch_urls   = set()
    batch_pairs  = set()
    unique, dupes = [], 0
    for job in jobs:
        nurl  = _normalize_url(job.get("url", ""))
        pair  = (job.get("company", "").lower(), job.get("title", "").lower())
        jid   = job.get("id", "")
        if (nurl  in seen_urls   or nurl  in batch_urls  or
            jid   in seen_ids    or
            pair  in seen_pairs  or pair  in batch_pairs):
            dupes += 1
            continue
        seen_urls.add(nurl);  batch_urls.add(nurl)
        seen_pairs.add(pair); batch_pairs.add(pair)
        unique.append(job)
    return unique, dupes


# ── Match Score & Resume Cleanup ───────────────────────────────────────────────

def estimate_match_score(job_description):
    """Return 0-100 match score: % of candidate skills found in job description."""
    if not job_description:
        return 0
    jd = job_description.lower()
    hits = sum(1 for s in CANDIDATE["skills"] if s.lower() in jd)
    return min(100, int(hits / max(len(CANDIDATE["skills"]), 1) * 100 * 2.5))


def cleanup_old_resumes(days=90, dry_run=False):
    """Delete .docx files in resume-personalized/ older than `days` days.
    Returns list of deleted filenames."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    deleted = []
    for f in RESUME_DIR.glob("*.docx"):
        mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            if not dry_run:
                f.unlink()
            deleted.append(f.name)
    return deleted


# ── Cover Letter Generation ────────────────────────────────────────────────────

def generate_cover_letter(job_title, company, job_description):
    """Generate a one-paragraph cover letter via Claude Haiku for LinkedIn Easy Apply.
    Returns empty string on any failure (cover letter is optional — resume still saved)."""
    try:
        client = anthropic.Anthropic()
        ats_context = get_current_ats_techniques()
        prompt = (
            "You are an expert career coach. Write a ONE-paragraph cover letter (4-5 sentences) "
            "for a Senior Java Full-Stack Engineer applying in 2026.\n\n"
            "ATS CONTEXT:\n" + ats_context[:400] + "\n\n"
            "CANDIDATE FACTS:\n" + CANDIDATE_RESUME_TEXT[:600] + "\n\n"
            "TARGET JOB:\n"
            "- Company: " + company + "\n"
            "- Title: " + job_title + "\n"
            "- Description (excerpt):\n" + job_description[:1000] + "\n\n"
            "RULES:\n"
            "1. Mirror 2-3 exact phrases from the job description naturally\n"
            "2. Lead with the strongest technical match\n"
            "3. Include one quantified impact\n"
            "4. End with genuine enthusiasm for THIS company specifically\n"
            "5. Sound human, NOT generic\n\n"
            "Return ONLY the paragraph. No salutation. No sign-off. No headers."
        )
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"generate_cover_letter failed ({e}); skipping cover letter (resume still saved)"
        )
        return ""


# ── Run History ────────────────────────────────────────────────────────────────

def append_run_history(run_data):
    """Append a run summary entry to logs/run_history.json."""
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = []
    history.append(run_data)
    # Keep last 52 runs (one year of weekly runs)
    history = history[-52:]
    with FileLock(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)



# ── Scoring and Filtering ──────────────────────────────────────────────────────

def score_job(title, description, priority):
    text = (title + " " + description).lower()
    required_hits = sum(1 for t in priority["required_terms"] if t in text)
    if priority["required_terms"] and required_hits < len(priority["required_terms"]):
        return 0
    keyword_hits = sum(1 for kw in CANDIDATE["skills"] if kw.lower() in text)
    return min(100, required_hits * 20 + keyword_hits * 3)


def is_location_match(job_location):
    loc = (job_location or "").lower()
    if "remote" in loc:
        return True
    return any(kw in loc for kw in LOCATION_KEYWORDS)


def is_leadership_role(title, description=""):
    text = (title + " " + description[:500]).lower()
    return any(kw in text for kw in LEADERSHIP_TITLE_KEYWORDS)


def estimate_salary(title, description):
    text = (title + " " + description).lower()
    if any(w in text for w in ["principal", "staff engineer", "architect", "distinguished"]):
        return "$165,000 - $195,000"
    if any(w in text for w in ["fintech", "financial", "security", "cybersecurity", "banking", "payment"]):
        return "$160,000 - $185,000"
    if any(w in text for w in ["senior", "sr.", "sr ", "iii", "level 3"]):
        return "$145,000 - $170,000"
    if any(w in text for w in ["mid", "intermediate", "ii", "level 2"]):
        return "$120,000 - $145,000"
    if any(w in text for w in ["junior", "jr", "entry", "associate", "level 1"]):
        return "$90,000 - $115,000"
    return "$150,000 - $175,000"



# ── Email HTML ─────────────────────────────────────────────────────────────────

def build_email_html(applications, week_str):
    if not applications:
        return (
            "<html><body>"
            "<h2>Weekly Job Application Summary -- " + week_str + "</h2>"
            "<p>No new applications this week.</p>"
            "</body></html>"
        )

    auto_applied = sorted([a for a in applications if a.get("status") == "applied"],
                          key=lambda x: -x.get("match_score", 0))
    resume_ready = sorted([a for a in applications if a.get("status") == "resume_ready"],
                          key=lambda x: -x.get("match_score", 0))
    errored      = [a for a in applications if a.get("status") == "error"]

    def _section_rows(apps):
        if not apps:
            return '<tr><td colspan="9" style="padding:10px;color:#6b7280;font-style:italic;">No entries in this section.</td></tr>'
        by_priority = {}
        for app in apps:
            by_priority.setdefault(app.get("priority_label", "General"), []).append(app)
        rows = ""
        for plabel, paps in by_priority.items():
            rows += (
                '<tr style="background:#1a56db;color:white;">'
                '<td colspan="9" style="padding:8px 12px;font-weight:bold;">Target: ' + plabel + '</td>'
                "</tr>"
            )
            for app in paps:
                st = app.get("status", "pending")
                sc = "#16a34a" if st == "applied" else ("#dc2626" if st == "error" else "#d97706")
                ms = app.get("match_score")
                if ms is None:
                    ms_display = "N/A"
                    ms_color   = "#6b7280"
                else:
                    ms_display = str(ms) + "%"
                    ms_color   = "#16a34a" if ms >= 70 else ("#d97706" if ms >= 40 else "#dc2626")
                rows += (
                    "<tr>"
                    '<td style="padding:6px 12px;">' + app.get("company", "--") + "</td>"
                    '<td style="padding:6px 12px;"><a href="' + app.get("url", "#") + '">' + app.get("title", "--") + "</a></td>"
                    '<td style="padding:6px 12px;">' + app.get("location", "N/A") + "</td>"
                    '<td style="padding:6px 12px;font-size:11px;color:#1a56db;font-weight:bold;">' + app.get("source", "--") + "</td>"
                    '<td style="padding:6px 10px;text-align:center;font-weight:bold;color:' + ms_color + '">' + ms_display + "</td>"
                    '<td style="padding:6px 12px;font-size:11px;color:#555;">' + app.get("resume_file", "--") + "</td>"
                    '<td style="padding:6px 12px;font-size:11px;">' + app.get("salary_submitted", "--") + "</td>"
                    '<td style="padding:6px 12px;font-size:11px;color:#1a56db;">' + str(app.get("salary_offered") or "--") + "</td>"
                    '<td style="padding:6px 12px;color:' + sc + ';font-weight:bold;">' + st.upper() + "</td>"
                    "</tr>"
                )
        return rows

    th = (
        '<thead><tr style="background:#f3f4f6;">'
        '<th style="padding:8px 12px;text-align:left;">Company</th>'
        '<th style="padding:8px 12px;text-align:left;">Position</th>'
        '<th style="padding:8px 12px;text-align:left;">Location</th>'
        '<th style="padding:8px 12px;text-align:left;color:#1a56db;">Source</th>'
        '<th style="padding:8px 10px;text-align:center;">Match%</th>'
        '<th style="padding:8px 12px;text-align:left;">Resume Used</th>'
        '<th style="padding:8px 12px;text-align:left;">Salary Submitted</th>'
        '<th style="padding:8px 12px;text-align:left;">Salary Offered</th>'
        '<th style="padding:8px 12px;text-align:left;">Status</th>'
        "</tr></thead>"
    )

    def _tbl(rows):
        return (
            '<table border="1" cellspacing="0" cellpadding="0" '
            'style="border-collapse:collapse;width:100%;border-color:#e5e7eb;">'
            + th + "<tbody>" + rows + "</tbody></table>"
        )

    def _error_tbl(errs):
        if not errs:
            return '<p style="color:#6b7280;font-style:italic;">No errors.</p>'
        err_th = (
            '<thead><tr style="background:#fef2f2;">'
            '<th style="padding:8px 12px;text-align:left;">Company</th>'
            '<th style="padding:8px 12px;text-align:left;">Position</th>'
            '<th style="padding:8px 12px;text-align:left;">Location</th>'
            '<th style="padding:8px 12px;text-align:left;color:#1a56db;">Source</th>'
            '<th style="padding:8px 12px;text-align:left;color:#dc2626;">Error Type</th>'
            '<th style="padding:8px 12px;text-align:left;color:#dc2626;">Error Message</th>'
            '<th style="padding:8px 10px;text-align:center;">Retries</th>'
            '<th style="padding:8px 12px;text-align:left;">Action</th>'
            '</tr></thead>'
        )
        rows = ""
        for app in errs:
            err_msg   = (app.get("error_message") or "Unknown error")
            err_short = err_msg[:80] + ("..." if len(err_msg) > 80 else "")
            err_type  = app.get("error_type") or "Exception"
            retry_n   = app.get("retry_count", 0)
            rows += (
                '<tr style="background:#fff5f5;">'
                '<td style="padding:6px 12px;font-weight:bold;">' + app.get("company", "--") + "</td>"
                '<td style="padding:6px 12px;">' + app.get("title", "--") + "</td>"
                '<td style="padding:6px 12px;font-size:11px;">' + app.get("location", "N/A") + "</td>"
                '<td style="padding:6px 12px;font-size:11px;color:#1a56db;font-weight:bold;">' + app.get("source", "--") + "</td>"
                '<td style="padding:6px 12px;font-size:11px;color:#dc2626;font-weight:bold;">' + err_type + "</td>"
                '<td style="padding:6px 12px;font-size:11px;color:#7f1d1d;" title="' + err_msg.replace('"', '&quot;') + '">' + err_short + "</td>"
                '<td style="padding:6px 10px;text-align:center;">' + str(retry_n) + "</td>"
                '<td style="padding:6px 12px;">' +
                ('<a href="' + app.get("url", "#") + '" style="color:#1a56db;font-weight:bold;">Apply Manually ↗</a>' if app.get("url") else "--") +
                "</td>"
                "</tr>"
            )
        return (
            '<table border="1" cellspacing="0" cellpadding="0" '
            'style="border-collapse:collapse;width:100%;border-color:#fca5a5;">'
            + err_th + "<tbody>" + rows + "</tbody></table>"
            + '<p style="font-size:12px;color:#6b7280;margin-top:6px;">'
            '💡 Hover over "Error Message" cell to see full error. '
            'To retry: python linkedin_agent.py --jobs-file jobs_input.json (re-run with same file).</p>'
        )

    return (
        '<!DOCTYPE html><html><head><meta charset="UTF-8"></head>'
        '<body style="font-family:Calibri,Arial,sans-serif;max-width:1000px;margin:auto;padding:20px;">'
        '<h2 style="color:#1a56db;">\U0001f4cb Weekly Job Application Report -- ' + week_str + "</h2>"
        "<p>Hello Adalberto,</p>"
        "<p>Automated job application summary for the week of <strong>" + week_str + "</strong>. "
        "Total processed: <strong>" + str(len(applications)) + "</strong> "
        "(" + str(len(auto_applied)) + " auto-applied / " + str(len(resume_ready)) + " resume ready / "
        + str(len(errored)) + " errors).</p>"

        '<h3 style="color:#16a34a;">\u2705 Section 1: Automatically Applied via LinkedIn Easy Apply (' + str(len(auto_applied)) + ")</h3>"
        "<p>Applied automatically. Sorted by match score.</p>"
        + _tbl(_section_rows(auto_applied))

        + '<h3 style="color:#d97706;margin-top:28px;">\U0001f4cb Section 2: Resume Ready -- Manual Apply Needed (' + str(len(resume_ready)) + ")</h3>"
        "<p>Resume saved to <code>resume-personalized/</code>. Apply manually via the source site. Cover letter in same folder (.txt).</p>"
        + _tbl(_section_rows(resume_ready))

        + (
            '<h3 style="color:#dc2626;margin-top:28px;">\u274c Section 3: Failed — Apply Manually (' + str(len(errored)) + ")</h3>"
            '<p style="color:#dc2626;font-size:13px;">These jobs could not be processed automatically. Apply manually via the links below.</p>'
            + _error_tbl(errored)
            if errored else ""
        )

        + '<br><p style="background:#fef3c7;padding:12px;border-left:4px solid #d97706;font-size:13px;">'
        "\u26a0\ufe0f <strong>ACTION REQUIRED:</strong> Open Gmail \u2192 Borradores and click <strong>Send</strong>."
        "</p>"
        '<p style="color:#6b7280;font-size:13px;">'
        "Search: (1) Backend Java/Spring Boot/Reactive \u2192 (2) Fullstack React+Spring Boot \u2192 (3) General<br>"
        "Location: Remote USA or on-site within " + str(LOCATION_CONFIG["radius_miles"]) + " miles of " + LOCATION_CONFIG["base_address"] + "<br>"
        "Match% = skills found in job description vs candidate skill set."
        "</p>"
        '<p style="color:#6b7280;font-size:12px;">'
        "Generated by Cowork Job Agent. "
        'LinkedIn: <a href="' + CANDIDATE["linkedin"] + '">' + CANDIDATE["linkedin"] + "</a>"
        "</p></body></html>"
    )



# ── Pre-Flight Checks ──────────────────────────────────────────────────────────

def run_preflight(jobs_file=None):
    """
    Validate all prerequisites before running the agent.
    Returns dict with preflight_ok (bool) and per-check results.
    Checks marked critical=True block execution if they fail.
    """
    checks = {}

    # ── 0. Cowork agent running (informational — always true when invoked via Cowork) ──
    checks["cowork_agent"] = {
        "name":     "Cowork Agent Running",
        "ok":       True,
        "detail":   "Confirmed — preflight was invoked through Cowork or CLI (implicit)",
        "critical": False,
        "fix":      "Open the Cowork app before starting the agent",
    }

    # ── 1. Base resume file ────────────────────────────────────────────────
    base_resume = BASE_DIR / "SilveiraNapoles-Adalberto-Resume-2026-ATS.docx"
    checks["base_resume"] = {
        "name":     "Base Resume (.docx)",
        "ok":       base_resume.exists(),
        "detail":   "Found: " + str(base_resume) if base_resume.exists()
                    else "NOT FOUND — place SilveiraNapoles-Adalberto-Resume-2026-ATS.docx in " + str(BASE_DIR),
        "critical": True,
        "fix":      "Copy the base .docx file to: " + str(BASE_DIR),
    }

    # ── 2. Jobs input file (only if --jobs-file given) ────────────────────
    if jobs_file:
        jf = Path(jobs_file)
        if jf.exists():
            try:
                with open(jf, encoding="utf-8") as _f:
                    jobs_data = json.load(_f)
                n = len(jobs_data) if isinstance(jobs_data, list) else 0
                checks["jobs_file"] = {
                    "name":     "Jobs Input File",
                    "ok":       n > 0,
                    "detail":   f"{n} jobs found in {jf.name}" if n > 0 else f"File exists but is empty: {jf}",
                    "critical": True,
                    "fix":      "Run the search phase first: ask Claude to search LinkedIn/Indeed/Dice and write jobs_input.json",
                }
            except Exception as exc:
                checks["jobs_file"] = {
                    "name":     "Jobs Input File",
                    "ok":       False,
                    "detail":   f"Parse error: {exc}",
                    "critical": True,
                    "fix":      "Check jobs_input.json is valid JSON",
                }
        else:
            checks["jobs_file"] = {
                "name":     "Jobs Input File",
                "ok":       False,
                "detail":   f"NOT FOUND: {jf}",
                "critical": True,
                "fix":      "Run the search phase first: ask Claude to search LinkedIn/Indeed/Dice and write jobs_input.json",
            }

    # ── 3. Resume output directory writable ───────────────────────────────
    try:
        RESUME_DIR.mkdir(parents=True, exist_ok=True)
        _test = RESUME_DIR / ".preflight_write_test"
        _test.write_text("ok", encoding="utf-8")
        _test.unlink()
        checks["resume_dir"] = {
            "name":     "Resume Output Directory (writable)",
            "ok":       True,
            "detail":   str(RESUME_DIR),
            "critical": True,
            "fix":      "",
        }
    except Exception as exc:
        checks["resume_dir"] = {
            "name":     "Resume Output Directory (writable)",
            "ok":       False,
            "detail":   str(exc),
            "critical": True,
            "fix":      "Check disk space and file permissions on " + str(RESUME_DIR),
        }

    # ── 4. Log directory writable ─────────────────────────────────────────
    log_dir = BASE_DIR / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        checks["log_dir"] = {
            "name":     "Log Directory (writable)",
            "ok":       True,
            "detail":   str(log_dir),
            "critical": True,
            "fix":      "",
        }
    except Exception as exc:
        checks["log_dir"] = {
            "name":     "Log Directory (writable)",
            "ok":       False,
            "detail":   str(exc),
            "critical": True,
            "fix":      "Check permissions on " + str(log_dir),
        }

    # ── 5. python-docx installed ──────────────────────────────────────────
    try:
        import docx as _docx  # noqa: F401
        checks["python_docx"] = {
            "name":     "python-docx library",
            "ok":       True,
            "detail":   "Installed",
            "critical": True,
            "fix":      "",
        }
    except ImportError:
        checks["python_docx"] = {
            "name":     "python-docx library",
            "ok":       False,
            "detail":   "Not installed",
            "critical": True,
            "fix":      "Run: pip install python-docx",
        }

    # ── 6. Anthropic API key (warning only — fallback exists) ─────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    checks["anthropic_api_key"] = {
        "name":     "Anthropic API Key (ANTHROPIC_API_KEY)",
        "ok":       bool(api_key),
        "detail":   "Set ✓" if api_key else "NOT SET — resumes will use base summary/bullets (no personalization)",
        "critical": False,  # fallback exists
        "fix":      "Set ANTHROPIC_API_KEY env var — resumes will be less personalized without it",
    }

    # ── 7. ATS cache readable ─────────────────────────────────────────────
    ats_file = BASE_DIR / "ats_techniques_cache.json"
    if ats_file.exists():
        try:
            with open(ats_file, encoding="utf-8") as _f:
                _ats = json.load(_f)
            checks["ats_cache"] = {
                "name":     "ATS Techniques Cache",
                "ok":       True,
                "detail":   "Expires: " + _ats.get("next_refresh", "unknown"),
                "critical": False,
                "fix":      "",
            }
        except Exception as exc:
            checks["ats_cache"] = {
                "name":     "ATS Techniques Cache",
                "ok":       False,
                "detail":   f"Corrupt cache: {exc}",
                "critical": False,
                "fix":      "Delete ats_techniques_cache.json — it will be rebuilt on next run",
            }
    else:
        checks["ats_cache"] = {
            "name":     "ATS Techniques Cache",
            "ok":       False,
            "detail":   "Not found — will be created on first run (needs internet)",
            "critical": False,
            "fix":      "Run once with internet access to seed the cache",
        }

    # ── Summary ───────────────────────────────────────────────────────────
    critical_failures = [
        {"key": k, **v} for k, v in checks.items()
        if not v["ok"] and v.get("critical")
    ]
    warnings = [
        {"key": k, **v} for k, v in checks.items()
        if not v["ok"] and not v.get("critical")
    ]
    passed = sum(1 for v in checks.values() if v["ok"])

    return {
        "preflight_ok":       len(critical_failures) == 0,
        "passed":             passed,
        "failed_critical":    len(critical_failures),
        "warnings":           len(warnings),
        "critical_failures":  critical_failures,
        "warnings_list":      warnings,
        "checks":             checks,
        "timestamp":          datetime.datetime.now().isoformat(),
    }


# ── Main Orchestration ─────────────────────────────────────────────────────────

def run_agent(jobs_found, mode="MANUAL", run_id=None, dry_run=False):
    """Main orchestration. mode='MANUAL'|'AUTO'. run_id groups log entries for this run."""
    if run_id is None:
        run_id = generate_run_id()

    start_time = datetime.datetime.now()
    error_log, app_log, exec_log = setup_logging(mode)
    ats_status = get_cache_status()
    if app_log:
        app_log.info(f"RUN {run_id} | mode={mode} | dry_run={dry_run} | ATS cache: {ats_status}")

    # Cleanup old resumes at start of run (not in dry-run)
    if not dry_run:
        deleted = cleanup_old_resumes(days=90)
        if deleted and app_log:
            app_log.info(f"Cleaned {len(deleted)} resumes older than 90 days")

    log = load_log()
    applications = []
    skipped = 0
    errors   = 0

    # Validate input jobs
    jobs_found, skip_invalid = validate_jobs_input(jobs_found)
    skipped += skip_invalid
    if app_log and skip_invalid:
        app_log.warning(f"Skipped {skip_invalid} invalid job entries (missing required fields)")

    # Cross-MCP deduplication
    jobs_found, dupes = deduplicate_jobs_cross_mcp(jobs_found, log)
    skipped += dupes
    if app_log:
        app_log.info(f"After dedup: {len(jobs_found)} unique new jobs ({dupes} cross-MCP dupes removed)")

    # Score and sort by priority
    scored_jobs = []
    for job in jobs_found:
        for priority in SEARCH_PRIORITIES:
            score = score_job(job.get("title", ""), job.get("description", ""), priority)
            if score > 0:
                scored_jobs.append((score, priority, job))
                break

    scored_jobs.sort(key=lambda x: -x[0])

    if app_log:
        app_log.info(f"Jobs to evaluate: {len(scored_jobs)}")

    for score, priority, job in scored_jobs:
        jid      = job.get("id") or job.get("url", "")
        title    = job.get("title",    "Unknown Title")
        company  = job.get("company",  "Unknown Company")
        location = job.get("location", "")
        url      = job.get("url",      "")
        desc     = job.get("description", "")
        source   = job.get("source",   "Unknown")

        if not is_location_match(location):
            if app_log:
                log_job_result(app_log, "skip_location", title, company, location)
            skipped += 1
            continue
        if is_leadership_role(title, desc):
            if app_log:
                log_job_result(app_log, "skip_leader", title, company, location)
            skipped += 1
            continue

        if app_log:
            app_log.info(f"Processing [{priority['label']}] {title} @ {company} | score={score}")

        # Check if this job previously errored (dedup allows retry)
        _prior_error = next(
            (e for e in log if e.get("job_id") == jid and e.get("status") == "error"), None
        )
        _prior_retry_count = _prior_error.get("retry_count", 0) if _prior_error else 0

        # ── Retry loop (max 1 retry on transient failures) ────────────────
        MAX_ATTEMPTS = 2
        last_exc = None
        for _attempt in range(MAX_ATTEMPTS):
          try:
            salary       = estimate_salary(title, desc)
            salary_off   = job.get("salary") or "--"
            match_score  = estimate_match_score(desc)

            if dry_run:
                entry = {
                    "job_id":               jid,
                    "title":                title,
                    "company":              company,
                    "location":             location,
                    "url":                  url,
                    "source":               source,
                    "priority_label":       priority["label"],
                    "priority_score":       score,
                    "match_score":          match_score,
                    "description_snippet":  desc[:300],
                    "salary_submitted":     salary,
                    "salary_offered":       salary_off,
                    "status":               "dry_run",
                    "run_id":               run_id,
                    "applied_date":         datetime.date.today().isoformat(),
                }
                applications.append(entry)
                break  # dry_run — no retry needed

            resume_path = create_personalized_resume(
                job_title=title, company=company,
                job_description=desc, priority_label=priority["label"],
            )

            # Cover letter (optional — failure does NOT fail the job)
            cover = generate_cover_letter(title, company, desc)
            cl_path = None
            if cover:
                cl_path = RESUME_DIR / (resume_path.stem + "-CoverLetter.txt")
                cl_path.write_text(cover, encoding="utf-8")

            _status = "resume_ready"
            if _attempt > 0:
                _status = "resume_ready"  # recovered after retry
                if app_log:
                    app_log.info(f"RECOVERED after retry {_attempt}: {title} @ {company}")

            entry = {
                "job_id":               jid,
                "title":                title,
                "company":              company,
                "location":             location,
                "url":                  url,
                "source":               source,
                "priority_label":       priority["label"],
                "priority_score":       score,
                "match_score":          match_score,
                "description_snippet":  desc[:300],
                "resume_file":          resume_path.name,
                "resume_path":          str(resume_path),
                "cover_letter_file":    cl_path.name if cl_path else None,
                "salary_submitted":     salary,
                "salary_offered":       salary_off,
                "status":               _status,
                "retry_count":          _prior_retry_count + _attempt,
                "run_id":               run_id,
                "applied_date":         datetime.date.today().isoformat(),
            }

            # If previously errored, replace that entry; otherwise append
            if _prior_error:
                for _i, _e in enumerate(log):
                    if _e.get("job_id") == jid and _e.get("status") == "error":
                        log[_i] = entry
                        break
            else:
                log.append(entry)
            save_log_locked(log)
            applications.append(entry)

            if app_log:
                log_job_result(app_log, "resume_ready", title, company, location,
                               resume_file=resume_path.name, salary=salary, url=url)
            last_exc = None
            break  # success — exit retry loop

          except Exception as e:
            import traceback, time as _time
            last_exc    = e
            error_msg   = str(e)
            error_type  = type(e).__name__
            tb_str      = traceback.format_exc()
            if _attempt < MAX_ATTEMPTS - 1:
                # First failure — log warning and retry
                if app_log:
                    app_log.warning(
                        f"Attempt {_attempt + 1}/{MAX_ATTEMPTS} FAILED for {title} @ {company}: "
                        f"{error_type}: {error_msg[:80]} — retrying in 3s…"
                    )
                _time.sleep(3)
                continue
            # All attempts exhausted — persist as persistent error
            errors += 1
            total_retries = _prior_retry_count + _attempt + 1
            if app_log:
                log_job_result(app_log, "error", title, company, location,
                               error=f"[attempt {total_retries}] {error_msg}")
            if error_log:
                error_log.error(
                    f"PERSISTENT ERROR (attempt {total_retries}): {title} @ {company}\n" + tb_str
                )
            error_entry = {
                "job_id":               jid,
                "title":                title,
                "company":              company,
                "location":             location,
                "url":                  url,
                "source":               source,
                "priority_label":       priority["label"],
                "priority_score":       score,
                "match_score":          None,
                "description_snippet":  desc[:300],
                "resume_file":          None,
                "cover_letter_file":    None,
                "salary_submitted":     None,
                "salary_offered":       job.get("salary"),
                "status":               "error",
                "error_message":        error_msg,
                "error_type":           error_type,
                "retry_count":          total_retries,
                "run_id":               run_id,
                "applied_date":         datetime.date.today().isoformat(),
            }
            # Replace prior error entry or append
            if _prior_error:
                for _i, _e in enumerate(log):
                    if _e.get("job_id") == jid and _e.get("status") == "error":
                        log[_i] = error_entry
                        break
            else:
                log.append(error_entry)
            save_log_locked(log)
            applications.append(error_entry)

    week_str   = datetime.date.today().strftime("%B %d, %Y")
    email_html = build_email_html(applications, week_str) if not dry_run else ""
    duration   = round((datetime.datetime.now() - start_time).total_seconds(), 2)

    # Append to run_history.json
    if not dry_run:
        sources_counts = {}
        for j in scored_jobs:
            src = j[2].get("source", "unknown")
            sources_counts[src] = sources_counts.get(src, 0) + 1
        append_run_history({
            "run_id":    run_id,
            "mode":      mode,
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "jobs_found":   len(scored_jobs),
            "resumes_generated": len(applications),
            "skipped":   skipped,
            "errors":    errors,
            "sources":   sources_counts,
            "week_str":  week_str,
        })

    if app_log:
        log_run_summary(app_log, len(scored_jobs), len(applications), skipped, errors, week_str)
        app_log.info("EMAIL: Gmail MCP creates drafts only -- open Gmail Borradores and Send.")

    return {
        "run_id":       run_id,
        "applications": applications,
        "email_html":   email_html,
        "week_str":     week_str,
        "count":        len(applications),
        "mode":         mode,
        "errors":       errors,
        "skipped":      skipped,
        "duration":     duration,
    }



# ── Post-Run Helpers ───────────────────────────────────────────────────────────

def update_job_status(job_id, new_status):
    """Update a job entry status after Easy Apply attempt (thread-safe)."""
    with FileLock(LOG_FILE):
        log = load_log()
        updated = False
        for entry in log:
            if entry.get("job_id") == job_id:
                entry["status"]         = new_status
                entry["status_updated"] = datetime.datetime.now().isoformat()
                updated = True
                break
        if updated:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(log, f, indent=2, ensure_ascii=False)
    return updated


def build_email_from_log(run_id=None, run_date=None):
    """Build email HTML from log entries for a specific run_id or date.
    Prefer run_id (exact run); fall back to date if run_id not provided."""
    log = load_log()
    if run_id:
        apps = [e for e in log if e.get("run_id") == run_id]
    elif run_date:
        apps = [e for e in log if e.get("applied_date") == run_date]
    else:
        today = datetime.date.today().isoformat()
        apps  = [e for e in log if e.get("applied_date") == today]
    week_str = datetime.date.today().strftime("%B %d, %Y")
    return build_email_html(apps, week_str)



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="LinkedIn Job Application Agent v3 -- Adalberto Silveira Napoles"
    )
    parser.add_argument("--jobs-file",     default=None,
                        help="Path to JSON file with jobs from MCP searches")
    parser.add_argument("--update-status", nargs=2, metavar=("JOB_ID", "STATUS"),
                        help="Update a job status. STATUS: applied|error|resume_ready")
    parser.add_argument("--build-email",   action="store_true",
                        help="Build and print email HTML from run results")
    parser.add_argument("--run-id",        default=None,
                        help="Run ID for --build-email (preferred over --date)")
    parser.add_argument("--date",          default=None,
                        help="Date filter for --build-email (YYYY-MM-DD)")
    parser.add_argument("--dry-run",       action="store_true",
                        help="Simulate pipeline without generating files or writing logs")
    parser.add_argument("--cleanup",       action="store_true",
                        help="Run resume cleanup and exit")
    parser.add_argument("--days",          type=int, default=90,
                        help="Days threshold for --cleanup (default: 90)")
    parser.add_argument("--auto",          action="store_true",
                        help="Auto/scheduled mode flag")
    parser.add_argument("--preflight",     action="store_true",
                        help="Check all prerequisites and exit without running (JSON output)")
    args = parser.parse_args()
    mode = "AUTO" if args.auto else "MANUAL"

    # ── Mode: --preflight ────────────────────────────────────────────────────
    if args.preflight:
        result = run_preflight(jobs_file=args.jobs_file)
        print(json.dumps(result, indent=2))
        import sys as _sys
        _sys.exit(0 if result["preflight_ok"] else 1)

    # ── Mode: cleanup ────────────────────────────────────────────────────────
    if args.cleanup:
        deleted = cleanup_old_resumes(days=args.days, dry_run=False)
        print(json.dumps({"deleted": len(deleted), "files": deleted}))

    # ── Mode: update-status ───────────────────────────────────────────────────
    elif args.update_status:
        job_id, new_status = args.update_status
        ok = update_job_status(job_id, new_status)
        print(json.dumps({"ok": ok, "job_id": job_id, "status": new_status}))

    # ── Mode: build-email ─────────────────────────────────────────────────────
    elif args.build_email:
        html = build_email_from_log(run_id=args.run_id, run_date=args.date)
        print(html)

    # ── Mode: --jobs-file (main flow + optional --dry-run) ────────────────────
    elif args.jobs_file:
        with open(args.jobs_file, "r", encoding="utf-8") as jf:
            jobs_data = json.load(jf)
        run_id = generate_run_id()
        result = run_agent(jobs_data, mode=mode, run_id=run_id, dry_run=args.dry_run)

        prefix = "[DRY-RUN] " if args.dry_run else ""
        summary = {
            "run_id":   result["run_id"],
            "mode":     result["mode"],
            "dry_run":  args.dry_run,
            "count":    result["count"],
            "skipped":  result["skipped"],
            "errors":   result["errors"],
            "duration": result["duration"],
            "week_str": result["week_str"],
            "jobs": [
                {
                    "job_id":      a["job_id"],
                    "title":       a["title"],
                    "company":     a["company"],
                    "url":         a["url"],
                    "source":      a["source"],
                    "match_score": a.get("match_score", 0),
                    "resume_file": a.get("resume_file"),
                    "cover_letter_file": a.get("cover_letter_file"),
                    "status":      a["status"],
                }
                for a in result["applications"]
            ],
        }
        print(json.dumps(summary, indent=2))

        if not args.dry_run:
            linkedin_jobs = [j for j in summary["jobs"] if "linkedin.com" in (j.get("url") or "")]
            if linkedin_jobs:
                print("\n-- LinkedIn Easy Apply jobs (" + str(len(linkedin_jobs)) + "):")
                for j in linkedin_jobs:
                    print("  python linkedin_agent.py --update-status \"" + j["job_id"] + "\" applied")
            print("\n-- After all Easy Apply attempts:")
            print("  python linkedin_agent.py --build-email --run-id " + result["run_id"])

    # ── Mode: demo / no --jobs-file provided ─────────────────────────────────
    else:
        print(json.dumps({
            "warning": "No --jobs-file provided. Running DEMO MODE with 2 test jobs.",
            "hint": "For real runs use: python linkedin_agent.py --jobs-file jobs_input.json",
            "hint2": "For dry-run test: python linkedin_agent.py --jobs-file jobs_input.json --dry-run"
        }, indent=2))
        sample_jobs = [
            {
                "id": "test-001", "title": "Senior Java Backend Engineer",
                "company": "TechCorp Miami", "location": "Remote (USA)",
                "url": "https://www.linkedin.com/jobs/view/test-001",
                "description": (
                    "Senior Java Spring Boot Spring WebFlux reactive programming "
                    "AWS Lambda SNS/SQS microservices PostgreSQL Docker Kubernetes "
                    "OAuth 2.0 JWT JUnit 5 Mockito."
                ),
                "source": "test",
            },
            {
                "id": "test-002", "title": "Java Spring Boot Developer",
                "company": "Sunrise Tech Corp", "location": "Sunrise, FL",
                "url": "https://www.indeed.com/jobs/view/test-002",
                "description": "Java Spring Boot microservices AWS developer on-site Sunrise FL.",
                "source": "test",
            },
        ]
        run_id = generate_run_id()
        result = run_agent(sample_jobs, mode=mode, run_id=run_id, dry_run=True)
        print(json.dumps({
            "run_id": result["run_id"], "count": result["count"],
            "mode": "DEMO", "dry_run": True, "week_str": result["week_str"]
        }, indent=2))
