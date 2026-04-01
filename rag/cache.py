"""응답 캐싱 (동일 질문 + 유사 질문)"""
import time
import numpy as np

# 캐시: {질문: (답변, 임베딩벡터, 타임스탬프)}
_cache: dict[str, tuple[str, list[float], float]] = {}
CACHE_TTL = 3600  # 1시간
SIMILARITY_THRESHOLD = 0.92


def get_exact(question: str) -> str | None:
    """동일 질문 캐시 조회"""
    key = question.strip().lower()
    if key in _cache:
        answer, _, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            print(f"[CACHE] exact hit: {question[:40]}")
            return answer
        del _cache[key]
    return None


def get_similar(query_vector: list[float]) -> str | None:
    """유사 질문 캐시 조회 (코사인 유사도 기반)"""
    if not _cache:
        return None

    q = np.array(query_vector)
    q_norm = q / (np.linalg.norm(q) + 1e-10)

    best_score = 0.0
    best_answer = None
    now = time.time()

    expired_keys = []
    for key, (answer, emb, ts) in _cache.items():
        if now - ts >= CACHE_TTL:
            expired_keys.append(key)
            continue
        e = np.array(emb)
        e_norm = e / (np.linalg.norm(e) + 1e-10)
        sim = float(q_norm @ e_norm)
        if sim > best_score:
            best_score = sim
            best_answer = answer

    for k in expired_keys:
        del _cache[k]

    if best_score >= SIMILARITY_THRESHOLD:
        print(f"[CACHE] similar hit: score={best_score:.3f}")
        return best_answer

    return None


def put(question: str, answer: str, query_vector: list[float]):
    """캐시에 저장"""
    key = question.strip().lower()
    _cache[key] = (answer, query_vector, time.time())

    # 캐시 크기 제한 (최대 200개)
    if len(_cache) > 200:
        oldest_key = min(_cache, key=lambda k: _cache[k][2])
        del _cache[oldest_key]
