"""IP rate limit + daily RPD counter for portfolio coach.

Storage: Supabase Postgres via rag.db wrapper.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from rag import db

IP_DAILY_LIMIT = 5
DAILY_CAP_DEFAULT = 240

TABLE_RATELIMIT = "portfolio_ratelimit"
TABLE_DAILY = "portfolio_daily_count"

_DEFAULT_SALT = "smt-portfolio-coach-default-salt"


@dataclass
class RateLimitStatus:
    allowed: bool
    remaining: int
    reset_at: datetime | None


def hash_ip(raw_ip: str) -> str:
    salt = os.getenv("IP_HASH_SALT", _DEFAULT_SALT)
    return hashlib.sha256(f"{salt}|{raw_ip}".encode("utf-8")).hexdigest()


def _kst_today() -> str:
    return datetime.now(timezone(timedelta(hours=9))).date().isoformat()


def _kst_midnight_tomorrow() -> datetime:
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    tomorrow = now.date() + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=kst)


def check_and_increment_ip(ip_hash: str) -> RateLimitStatus:
    """Check & increment per-IP daily counter atomically.

    Note: Streamlit Cloud is single-process, so a read-then-upsert is acceptable.
    """
    today = _kst_today()
    rows = db.select(
        TABLE_RATELIMIT,
        {
            "ip_hash": f"eq.{ip_hash}",
            "window_date": f"eq.{today}",
        },
        limit=1,
    )
    current = rows[0]["count"] if rows else 0

    if current >= IP_DAILY_LIMIT:
        return RateLimitStatus(
            allowed=False, remaining=0, reset_at=_kst_midnight_tomorrow()
        )

    new_count = current + 1
    db.upsert(
        TABLE_RATELIMIT,
        {
            "ip_hash": ip_hash,
            "window_date": today,
            "count": new_count,
        },
    )
    return RateLimitStatus(
        allowed=True,
        remaining=IP_DAILY_LIMIT - new_count,
        reset_at=_kst_midnight_tomorrow(),
    )


def check_and_increment_rpd(num_calls: int = 2, byok: bool = False) -> tuple[bool, int]:
    """Check & increment global daily RPD counter.

    BYOK callers do not consume the shared quota.

    Returns:
        (allowed, remaining)
    """
    today = _kst_today()
    rows = db.select(TABLE_DAILY, {"date": f"eq.{today}"}, limit=1)
    if rows:
        current = rows[0].get("count", 0)
        cap = rows[0].get("cap", DAILY_CAP_DEFAULT)
    else:
        current = 0
        cap = DAILY_CAP_DEFAULT

    if byok:
        return True, cap - current

    if current + num_calls > cap:
        return False, cap - current

    db.upsert(
        TABLE_DAILY,
        {
            "date": today,
            "count": current + num_calls,
            "cap": cap,
        },
    )
    return True, cap - (current + num_calls)


def get_today_status() -> dict:
    """Return today's counter snapshot for sidebar display."""
    today = _kst_today()
    rows = db.select(TABLE_DAILY, {"date": f"eq.{today}"}, limit=1)
    if rows:
        return {
            "daily_used": rows[0].get("count", 0),
            "daily_cap": rows[0].get("cap", DAILY_CAP_DEFAULT),
            "today": today,
        }
    return {"daily_used": 0, "daily_cap": DAILY_CAP_DEFAULT, "today": today}


def get_ip_status(ip_hash: str) -> dict:
    today = _kst_today()
    rows = db.select(
        TABLE_RATELIMIT,
        {"ip_hash": f"eq.{ip_hash}", "window_date": f"eq.{today}"},
        limit=1,
    )
    used = rows[0]["count"] if rows else 0
    return {"ip_used": used, "ip_limit": IP_DAILY_LIMIT}
