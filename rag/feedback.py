"""피드백 로깅 (Supabase 우선, Google Sheets 폴백)"""
import os
from datetime import datetime, timezone, timedelta

import requests as req

from rag import db


def log_feedback(question: str, answer: str, feedback_type: str, session_id: str = ""):
    """👍/👎 피드백 저장"""
    kst = timezone(timedelta(hours=9))
    ts = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[FEEDBACK] {ts} | sid={session_id} | {feedback_type} | Q: {question[:50]}")

    db.insert("feedback", {
        "session_id": session_id,
        "question": question,
        "answer": answer[:500],
        "feedback_type": feedback_type,
    })

    webhook_url = os.getenv("LOG_WEBHOOK_URL")
    if webhook_url:
        try:
            req.post(webhook_url, json={
                "type": "feedback",
                "timestamp": ts,
                "session_id": session_id,
                "question": question,
                "answer": answer[:500],
                "feedback_type": feedback_type,
            }, timeout=5)
        except Exception:
            pass
