"""Supabase Storage REST wrapper + portfolio submission helpers.

Pattern follows rag/db.py — pure requests, no SDK.
"""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone, timedelta

import requests as req

from rag import db

BUCKET = "portfolio-uploads"
TABLE_SUBMISSIONS = "portfolio_submissions"


def _supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").rstrip("/")


def _headers() -> dict:
    api_key = os.getenv("SUPABASE_KEY", "")
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
    }


def _kst_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=9)))


def _new_storage_path() -> str:
    now = _kst_now()
    date_dir = now.strftime("%Y%m%d")
    timestamp = now.strftime("%H%M%S")
    rand = secrets.token_hex(3)
    return f"{date_dir}/{timestamp}-{rand}"


def upload_file(path: str, content: bytes, content_type: str) -> bool:
    """Upload bytes to Storage. Returns True on success, False otherwise."""
    base = _supabase_url()
    if not base:
        return False
    url = f"{base}/storage/v1/object/{BUCKET}/{path}"
    headers = {**_headers(), "Content-Type": content_type, "x-upsert": "true"}
    try:
        resp = req.post(url, headers=headers, data=content, timeout=30)
        if resp.status_code in (200, 201):
            return True
        print(f"[PORTFOLIO STORAGE] upload failed {resp.status_code}: {resp.text[:200]}", flush=True)
        return False
    except Exception as e:
        print(f"[PORTFOLIO STORAGE] upload exception: {e}", flush=True)
        return False


def get_signed_url(path: str, expires_in: int = 3600) -> str | None:
    """Generate a signed download URL valid for `expires_in` seconds."""
    base = _supabase_url()
    if not base:
        return None
    url = f"{base}/storage/v1/object/sign/{BUCKET}/{path}"
    headers = {**_headers(), "Content-Type": "application/json"}
    try:
        resp = req.post(url, headers=headers, json={"expiresIn": expires_in}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            signed = data.get("signedURL") or data.get("signedUrl")
            if signed:
                return f"{base}/storage/v1{signed}"
    except Exception as e:
        print(f"[PORTFOLIO STORAGE] sign exception: {e}", flush=True)
    return None


def upload_submission(
    zip_bytes: bytes,
    ip_hash: str,
    file_size: int,
    page_count: int,
    image_count: int,
    image_truncated: bool,
) -> dict:
    """Best-effort: upload zip + meta.json, insert DB row, return submission dict.

    Returns a dict with at least {storage_path} even if Storage fails,
    so the caller can continue and patch later.
    """
    storage_path = _new_storage_path()
    zip_path = f"{storage_path}/original.zip"
    meta_path = f"{storage_path}/meta.json"

    upload_file(zip_path, zip_bytes, "application/zip")
    meta = {
        "ip_hash": ip_hash,
        "file_size": file_size,
        "page_count": page_count,
        "image_count": image_count,
        "image_truncated": image_truncated,
        "created_at": _kst_now().isoformat(),
    }
    upload_file(meta_path, json.dumps(meta, ensure_ascii=False).encode("utf-8"), "application/json")

    row = {
        "ip_hash": ip_hash,
        "storage_path": storage_path,
        "file_size": file_size,
        "page_count": page_count,
        "image_count": image_count,
        "image_truncated": image_truncated,
        "status": "pending",
    }
    db.insert(TABLE_SUBMISSIONS, row)

    return {"storage_path": storage_path}


def attach_result_md(
    storage_path: str,
    result_md: str,
    eval_summary: str,
    model_used: str,
    used_byok: bool,
    used_fallback: bool,
    tokens_input: int,
    tokens_output: int,
) -> None:
    """Best-effort: upload result.md and update DB row to status='done'."""
    md_path = f"{storage_path}/result.md"
    upload_file(md_path, result_md.encode("utf-8"), "text/markdown")

    base = _supabase_url()
    if not base:
        return
    update_url = f"{base}/rest/v1/{TABLE_SUBMISSIONS}?storage_path=eq.{storage_path}"
    headers = {
        **_headers(),
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    payload = {
        "eval_summary": eval_summary,
        "model_used": model_used,
        "used_byok": used_byok,
        "used_fallback": used_fallback,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "status": "done",
    }
    try:
        req.patch(update_url, headers=headers, json=payload, timeout=5)
    except Exception as e:
        print(f"[PORTFOLIO STORAGE] update exception: {e}", flush=True)


def mark_error(storage_path: str, error: str) -> None:
    base = _supabase_url()
    if not base:
        return
    update_url = f"{base}/rest/v1/{TABLE_SUBMISSIONS}?storage_path=eq.{storage_path}"
    headers = {**_headers(), "Content-Type": "application/json", "Prefer": "return=minimal"}
    try:
        req.patch(update_url, headers=headers, json={"status": "error", "error": error[:500]}, timeout=5)
    except Exception:
        pass


def list_submissions(limit: int = 50) -> list[dict]:
    return db.select(
        TABLE_SUBMISSIONS,
        {"order": "created_at.desc"},
        limit=limit,
    )
