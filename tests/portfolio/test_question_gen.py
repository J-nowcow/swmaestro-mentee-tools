"""Unit tests for portfolio.question_gen — mocks portfolio.llm.call_multimodal."""
import json
from unittest.mock import patch

import pytest

from portfolio.evaluator import EvaluationResult
from portfolio.parser import ParsedPortfolio, PortfolioStats
from portfolio.question_gen import (
    QuestionGenError,
    QuestionResult,
    generate,
)


def _parsed() -> ParsedPortfolio:
    return ParsedPortfolio(
        markdown="# About\nbackend dev",
        images=[],
        stats=PortfolioStats(page_count=1, image_count=0, image_truncated=False, total_chars=12),
    )


def _evaluation() -> EvaluationResult:
    return EvaluationResult(
        overall={"one_liner": "ok", "strengths": [], "weaknesses": ["weak"]},
        criteria=[],
        model_used="gemini-2.5-flash",
        tokens={"input": 0, "output": 0},
    )


def _valid_json() -> str:
    return json.dumps(
        {
            "categories": [
                {"name": f"카테고리 {i}", "questions": ["q1", "q2"], "rationale": "r"}
                for i in range(1, 6)
            ]
        }
    )


@patch("portfolio.question_gen.call_multimodal")
def test_generate_returns_parsed_result(mock_call):
    mock_call.return_value = (_valid_json(), "gemini-2.5-flash", {"input": 10, "output": 5})

    result = generate(_parsed(), _evaluation())

    assert isinstance(result, QuestionResult)
    assert len(result.categories) == 5
    assert result.model_used == "gemini-2.5-flash"


@patch("portfolio.question_gen.call_multimodal")
def test_generate_does_not_pass_images(mock_call):
    """Call 2 must NOT send images (token saving)."""
    mock_call.return_value = (_valid_json(), "gemini-2.5-flash", {})

    generate(_parsed(), _evaluation())

    kwargs = mock_call.call_args.kwargs
    assert kwargs.get("images") in (None, [])


@patch("portfolio.question_gen.call_multimodal")
def test_generate_includes_evaluation_in_prompt(mock_call):
    mock_call.return_value = (_valid_json(), "gemini-2.5-flash", {})

    generate(_parsed(), _evaluation())

    user_text = mock_call.call_args.kwargs["user_text"]
    assert "weak" in user_text  # weakness from evaluation should be visible


@patch("portfolio.question_gen.call_multimodal")
def test_generate_invalid_json_raises(mock_call):
    mock_call.return_value = ("not json", "gemini-2.5-flash", {})

    with pytest.raises(QuestionGenError):
        generate(_parsed(), _evaluation())
