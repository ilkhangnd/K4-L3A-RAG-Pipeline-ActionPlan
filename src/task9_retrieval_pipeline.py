"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc PageIndex fallback SearchResult."""
    if top_k <= 0 or not query.strip():
        return []

    retrieval_k = top_k * 2

    # Tương thích trạng thái hiện tại: EMBEDDING_MODEL="bm25" sẽ làm
    # semantic_search raise ValueError. Khi nhóm đổi sang embedding model
    # thật, dense search sẽ tự hoạt động mà không cần sửa Task 9.
    try:
        dense = semantic_search(query, top_k=retrieval_k)
    except ValueError as exc:
        if "BM25 is a lexical retriever" not in str(exc):
            raise
        dense = []

    sparse = lexical_search(query, top_k=retrieval_k)

    # RRF chỉ chạy đúng một lần, kể cả khi dense hoặc sparse đang rỗng.
    primary_results = (
        rerank_rrf([dense, sparse], top_k=top_k)
        if use_reranking
        else dense[:top_k]
    )

    # Fallback phải dùng cosine score gốc của dense retrieval,
    # tuyệt đối không dùng RRF score.
    best_dense_score = max(
        (float(item["score"]) for item in dense),
        default=0.0,
    )

    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback[:top_k]
        except Exception:
            # PageIndex/provider lỗi không được làm UI crash.
            pass

    return primary_results[:top_k]


if __name__ == "__main__":
    for result in retrieve("chiến lược phát triển du lịch", top_k=3):
        print(result)