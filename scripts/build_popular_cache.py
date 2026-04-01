"""인기 질문 답변을 사전 생성하여 JSON으로 저장"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from rag.chain import ask

POPULAR_QUESTIONS = [
    "SW마에스트로 지원 자격이 어떻게 되나요?",
    "코딩테스트는 어떻게 준비하면 되나요?",
    "연수생에게 제공되는 혜택은?",
    "멘토는 어떤 분들인가요?",
    "SW마에스트로 지원 기간은 언제인가요?",
    "부산 연수과정은 어떻게 다른가요?",
    "코딩테스트 환경은 어떻게 되나요?",
    "연수과정 중 학업 병행이 가능한가요?",
    "SW마에스트로 경쟁률은 어떻게 되나요?",
    "심층면접은 어떻게 진행되나요?",
]


def main():
    print("인기 질문 사전 캐싱 시작")
    results = []

    for i, q in enumerate(POPULAR_QUESTIONS):
        print(f"[{i+1}/{len(POPULAR_QUESTIONS)}] {q}")
        try:
            answer, _ = ask(q)
            results.append({"question": q, "answer": answer})
            print(f"  OK ({len(answer)}자)")
        except Exception as e:
            print(f"  SKIP: {e}")
        time.sleep(5)  # rate limit

    output = Path("data/popular_cache.json")
    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{len(results)}개 답변 생성 → {output}")


if __name__ == "__main__":
    main()
