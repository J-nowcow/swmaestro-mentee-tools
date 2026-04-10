"""Call 2: category-based interview question generation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from portfolio.evaluator import EvaluationResult
from portfolio.llm import call_multimodal
from portfolio.parser import ParsedPortfolio
from portfolio.prompts import QUESTIONS_SCHEMA, SYSTEM_PROMPT_QUESTIONS


class QuestionGenError(Exception):
    """Raised when LLM response cannot be parsed into a valid QuestionResult."""


@dataclass
class QuestionResult:
    categories: list[dict]
    model_used: str
    tokens: dict


def _validate(data: dict) -> None:
    if "categories" not in data or not isinstance(data["categories"], list):
        raise QuestionGenError("missing or invalid 'categories'")
    for cat in data["categories"]:
        for k in ("name", "questions", "rationale"):
            if k not in cat:
                raise QuestionGenError(f"category missing '{k}'")


def _summarize_evaluation(ev: EvaluationResult) -> str:
    lines = [f"한 줄 총평: {ev.overall.get('one_liner', '')}"]
    weaknesses = ev.overall.get("weaknesses", [])
    if weaknesses:
        lines.append("약점: " + " / ".join(weaknesses))
    strengths = ev.overall.get("strengths", [])
    if strengths:
        lines.append("강점: " + " / ".join(strengths))
    for c in ev.criteria:
        lines.append(
            f"[{c.get('id')}] {c.get('title', '')} ({c.get('score', 0)}/5): {c.get('evaluation', '')}"
        )
    return "\n".join(lines)


def generate(
    parsed: ParsedPortfolio,
    evaluation: EvaluationResult,
    api_key: str | None = None,
    status_callback: Callable[[str], None] | None = None,
) -> QuestionResult:
    """Run Call 2: produce category-based interview questions.

    Notes:
        - Does NOT send images (token saving).
        - Uses the evaluation result as context to focus on weaknesses.

    Raises:
        QuestionGenError: if the LLM response is malformed.
        LLMUnavailableError: if the LLM call fails entirely.
    """
    user_text = (
        "다음은 SW마에스트로 연수생의 포트폴리오와 그에 대한 평가 결과입니다. "
        "평가에서 드러난 약점에 초점을 맞춘 면접 질문을 카테고리별로 만들어주세요.\n\n"
        "## 평가 결과\n"
        + _summarize_evaluation(evaluation)
        + "\n\n## 포트폴리오 본문\n"
        + parsed.markdown
    )

    text, model_used, tokens = call_multimodal(
        system_prompt=SYSTEM_PROMPT_QUESTIONS,
        user_text=user_text,
        images=None,
        response_schema=QUESTIONS_SCHEMA,
        api_key=api_key,
        status_callback=status_callback,
    )

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise QuestionGenError(f"LLM did not return valid JSON: {e}") from e

    _validate(data)

    return QuestionResult(
        categories=data["categories"],
        model_used=model_used,
        tokens=tokens,
    )
