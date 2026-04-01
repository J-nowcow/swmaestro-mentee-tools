"""Supabase REST API 래퍼"""
import os

import requests as req

_BASE_URL = None
_API_KEY = None


def _init():
    global _BASE_URL, _API_KEY
    if _BASE_URL is None:
        _BASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
        _API_KEY = os.getenv("SUPABASE_KEY", "")
    return bool(_BASE_URL and _API_KEY)


def _headers():
    return {
        "apikey": _API_KEY,
        "Authorization": f"Bearer {_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def insert(table: str, data: dict):
    """테이블에 행 삽입"""
    if not _init():
        return
    try:
        req.post(
            f"{_BASE_URL}/rest/v1/{table}",
            headers=_headers(),
            json=data,
            timeout=5,
        )
    except Exception:
        pass


def select(table: str, params: dict | None = None, limit: int = 100) -> list[dict]:
    """테이블 조회"""
    if not _init():
        return []
    try:
        headers = _headers()
        headers["Prefer"] = "return=representation"
        resp = req.get(
            f"{_BASE_URL}/rest/v1/{table}",
            headers=headers,
            params={**(params or {}), "limit": limit},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def upsert(table: str, data: dict):
    """테이블에 upsert (있으면 업데이트, 없으면 삽입)"""
    if not _init():
        return
    try:
        headers = _headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
        req.post(
            f"{_BASE_URL}/rest/v1/{table}",
            headers=headers,
            json=data,
            timeout=5,
        )
    except Exception:
        pass
