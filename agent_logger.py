"""
agent_logger.py — Logging system for the LinkedIn Job Agent.

Three log streams:
  logs/errors.log             — all exceptions (rotating, kept forever)
  logs/applications_auto_*.log  — per-run summary when scheduled task fires
  logs/applications_manual_*.log — per-run summary for manual executions
  logs/execution_auto.log     — full debug trace for scheduled runs (rotating)
  logs/execution_manual.log   — full debug trace for manual runs (rotating)
"""

import logging
import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"

_initialized = False
_error_logger = None
_app_logger = None
_exec_logger = None


def setup_logging(mode="MANUAL"):
    """Initialize all loggers. Call once at the start of each run.

    mode = "AUTO"   → scheduled task (Mondays 8am)
    mode = "MANUAL" → user-triggered run
    """
    global _initialized, _error_logger, _app_logger, _exec_logger

    LOGS_DIR.mkdir(exist_ok=True)
    prefix = "auto" if mode == "AUTO" else "manual"
    run_ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ── Error logger ──────────────────────────────────────────────────────────
    _error_logger = logging.getLogger("agent.errors")
    if not _error_logger.handlers:
        err_h = RotatingFileHandler(
            LOGS_DIR / "errors.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        err_h.setFormatter(fmt)
        err_h.setLevel(logging.ERROR)
        _error_logger.setLevel(logging.ERROR)
        _error_logger.addHandler(err_h)

    # ── Per-run applications logger ───────────────────────────────────────────
    _app_logger = logging.getLogger(f"agent.applications.{run_ts}")
    app_path = LOGS_DIR / f"applications_{prefix}_{run_ts}.log"
    app_h = logging.FileHandler(app_path, encoding="utf-8")
    app_h.setFormatter(fmt)
    app_h.setLevel(logging.INFO)
    _app_logger.setLevel(logging.INFO)
    _app_logger.addHandler(app_h)
    # Mirror to console
    con_h = logging.StreamHandler()
    con_h.setFormatter(fmt)
    con_h.setLevel(logging.INFO)
    _app_logger.addHandler(con_h)

    # ── Rotating execution logger ─────────────────────────────────────────────
    _exec_logger = logging.getLogger(f"agent.execution.{prefix}")
    if not _exec_logger.handlers:
        exec_h = RotatingFileHandler(
            LOGS_DIR / f"execution_{prefix}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        exec_h.setFormatter(fmt)
        exec_h.setLevel(logging.DEBUG)
        _exec_logger.setLevel(logging.DEBUG)
        _exec_logger.addHandler(exec_h)

    _initialized = True
    _app_logger.info("=" * 60)
    _app_logger.info(f"Agent run started  [mode={mode}]  {run_ts}")
    _app_logger.info("=" * 60)
    return _error_logger, _app_logger, _exec_logger


def get_loggers():
    """Return current loggers, initializing with MANUAL mode if not yet set up."""
    if not _initialized:
        setup_logging("MANUAL")
    return _error_logger, _app_logger, _exec_logger


def log_job_result(app_log, status, title, company, location, resume_file="",
                   salary="", url="", error=""):
    """Write one structured job result line to the applications log."""
    if status == "applied":
        app_log.info(
            f"APPLIED    | {company:<30} | {title[:45]:<45} | "
            f"{location[:25]:<25} | {salary:<22} | {resume_file}"
        )
    elif status == "resume_ready":
        app_log.info(
            f"RESUME_OK  | {company:<30} | {title[:45]:<45} | "
            f"{location[:25]:<25} | {salary:<22} | {resume_file}"
        )
    elif status == "skip_location":
        app_log.info(f"SKIP_LOC   | {company:<30} | {title[:45]:<45} | {location}")
    elif status == "skip_leader":
        app_log.info(f"SKIP_LEAD  | {company:<30} | {title[:45]:<45}")
    elif status == "skip_dup":
        app_log.info(f"SKIP_DUP   | {company:<30} | {title[:45]:<45}")
    elif status == "error":
        app_log.error(f"ERROR      | {company:<30} | {title[:45]:<45} | {error}")
    else:
        app_log.info(f"{status.upper():<10} | {company:<30} | {title[:45]:<45} | {url}")


def log_email_result(app_log, draft_created, draft_id="", error=""):
    """Log the weekly summary email result."""
    if draft_created:
        app_log.info(
            f"EMAIL      | Draft created in Gmail (id={draft_id}). "
            "ACTION NEEDED: Open Gmail and send the draft manually, "
            "OR the next release will auto-send. Subject: Weekly Job Applications."
        )
    else:
        app_log.error(f"EMAIL      | Failed to create draft: {error}")


def log_run_summary(app_log, total_found, applied, skipped, errors, week_str):
    """Final summary block at end of run."""
    app_log.info("")
    app_log.info("=" * 60)
    app_log.info(f"RUN COMPLETE  [{week_str}]")
    app_log.info(f"  Jobs found    : {total_found}")
    app_log.info(f"  Applied/ready : {applied}")
    app_log.info(f"  Skipped       : {skipped}")
    app_log.info(f"  Errors        : {errors}")
    app_log.info("=" * 60)
