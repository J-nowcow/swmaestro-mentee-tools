"""Unit tests for portfolio.compose_md."""
from portfolio.compose_md import compose_result_md


def _sample_evaluation() -> dict:
    return {
        "overall": {
            "one_liner": "단단한 구성이지만 정량 지표가 부족합니다.",
            "strengths": ["프로젝트 설명 명확", "기술 선택 근거 명시", "협업 흔적 우수"],
            "weaknesses": ["수치화 부족", "한계 인식 부족", "이미지 캡션 부재"],
        },
        "criteria": [
            {
                "id": i,
                "title": f"기준 {i}",
                "score": 3,
                "evaluation": f"평가 {i}",
                "evidence": f"근거 {i}",
            }
            for i in range(1, 11)
        ],
    }


def _sample_questions() -> dict:
    return {
        "categories": [
            {
                "name": "자기소개 / 첫인상",
                "questions": ["자기소개 부탁드립니다.", "본인을 한 줄로 표현하면?"],
                "rationale": "첫인상이 약함",
            },
            {
                "name": "기여도 명확성",
                "questions": ["프로젝트 A에서 본인의 기여는?"],
                "rationale": "팀 기여 구분 모호",
            },
        ]
    }


def _sample_meta() -> dict:
    return {
        "timestamp": "2026-04-09 15:42 KST",
        "model_used": "gemini-2.5-flash",
        "page_count": 12,
        "image_count": 23,
        "image_truncated": False,
    }


def test_compose_includes_overall_section():
    md = compose_result_md(_sample_evaluation(), _sample_questions(), _sample_meta())
    assert "## 📊 종합 평가" in md
    assert "단단한 구성" in md
    assert "수치화 부족" in md


def test_compose_includes_all_ten_criteria():
    md = compose_result_md(_sample_evaluation(), _sample_questions(), _sample_meta())
    for i in range(1, 11):
        assert f"기준 {i}" in md
        assert f"평가 {i}" in md
        assert f"근거 {i}" in md


def test_compose_includes_question_categories():
    md = compose_result_md(_sample_evaluation(), _sample_questions(), _sample_meta())
    assert "## 🎤 예상 면접 질문" in md
    assert "자기소개 / 첫인상" in md
    assert "프로젝트 A에서 본인의 기여는?" in md


def test_compose_handles_none_questions():
    """Call 2 may fail; result should still render the evaluation."""
    md = compose_result_md(_sample_evaluation(), None, _sample_meta())
    assert "## 📊 종합 평가" in md
    assert "## 📝 10항목 상세 평가" in md
    # Question section should be absent or noted as unavailable
    assert "면접 질문" not in md or "생성에 실패" in md


def test_compose_includes_metadata_block():
    md = compose_result_md(_sample_evaluation(), _sample_questions(), _sample_meta())
    assert "2026-04-09 15:42 KST" in md
    assert "gemini-2.5-flash" in md


def test_compose_renders_score_stars():
    md = compose_result_md(_sample_evaluation(), _sample_questions(), _sample_meta())
    # 3/5 → 3 filled stars
    assert "⭐⭐⭐" in md
