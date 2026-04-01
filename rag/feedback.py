"""피드백 로깅 (Google Sheets 같은 웹훅 사용, feedback 시트로 분기)"""
import os
from datetime import datetime, timezone, timedelta

import requests as req


def log_feedback(question: str, answer: str, feedback_type: str):
    """👍/👎 피드백을 Google Sheets에 저장"""
    kst = timezone(timedelta(hours=9))
    ts = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[FEEDBACK] {ts} | {feedback_type} | Q: {question[:50]}")

    webhook_url = os.getenv("LOG_WEBHOOK_URL")
    if webhook_url:
        try:
            req.post(webhook_url, json={
                "type": "feedback",
                "timestamp": ts,
                "question": question,
                "answer": answer[:500],
                "feedback_type": feedback_type,
            }, timeout=5)
        except Exception:
            pass
