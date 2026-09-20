"""
Task 8 — PageIndex vectorless fallback.

PageIndex 0.2.8 là cloud API:
- Upload PDF bằng submit_document().
- Chờ document sẵn sàng cho retrieval.
- Query bằng submit_query() và poll get_retrieval().
- Cache source -> document ID để không upload lại.
"""

import json
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


load_dotenv()

ROOT_DIR = Path(__file__).parent.parent
LEGAL_DIR = ROOT_DIR / "data" / "landing" / "legal"
CACHE_PATH = ROOT_DIR / "data" / "indexes" / "pageindex_document_ids.json"

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
POLL_INTERVAL_SECONDS = 2
DOCUMENT_TIMEOUT_SECONDS = 180
RETRIEVAL_TIMEOUT_SECONDS = 60


def _build_client():
    """Khởi tạo PageIndex cloud client."""
    try:
        from pageindex import PageIndexClient
    except ImportError as exc:
        raise RuntimeError(
            "Chưa cài pageindex. Chạy: python -m pip install -e '.[dev]'"
        ) from exc

    if not PAGEINDEX_API_KEY:
        raise RuntimeError(
            "Thiếu PAGEINDEX_API_KEY trong file .env. "
            "Lấy API key từ PageIndex rồi thêm: PAGEINDEX_API_KEY=..."
        )

    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


def _load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}

    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(mapping: dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _legal_pdfs() -> list[Path]:
    return sorted(
        path
        for path in LEGAL_DIR.glob("*.pdf")
        if path.is_file() and not path.name.startswith(".")
    )


def _wait_until_retrieval_ready(client: Any, document_id: str) -> None:
    """Chờ PageIndex xử lý document xong, có giới hạn thời gian."""
    deadline = time.monotonic() + DOCUMENT_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        if client.is_retrieval_ready(document_id):
            return
        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(
        f"PageIndex chưa sẵn sàng sau {DOCUMENT_TIMEOUT_SECONDS}s: {document_id}"
    )


def _wait_for_retrieval(client: Any, retrieval_id: str) -> dict:
    """Poll kết quả query cho tới completed hoặc timeout."""
    deadline = time.monotonic() + RETRIEVAL_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        response = client.get_retrieval(retrieval_id)
        status = response.get("status")

        if status == "completed":
            return response
        if status == "failed":
            raise RuntimeError(
                f"PageIndex retrieval failed: {response}"
            )

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(
        f"PageIndex retrieval timeout after {RETRIEVAL_TIMEOUT_SECONDS}s"
    )


def upload_documents() -> None:
    """Upload PDF chính sách mới và cache source -> document ID."""
    client = _build_client()
    mapping = _load_cache()

    for path in _legal_pdfs():
        source = path.name

        if source in mapping:
            continue

        response = client.submit_document(str(path))
        document_id = response["doc_id"]

        _wait_until_retrieval_ready(client, document_id)
        mapping[source] = document_id
        _save_cache(mapping)

        print(f"PageIndex ready: {source} -> {document_id}")

def _node_content(node: dict) -> str:
    """Lấy text evidence từ retrieved node của PageIndex."""
    pieces = []

    title = str(node.get("title", "")).strip()
    if title:
        pieces.append(title)

    def collect(value) -> None:
        if isinstance(value, dict):
            text = str(
                value.get("relevant_content")
                or value.get("text")
                or ""
            ).strip()
            if text:
                pieces.append(text)
            return

        if isinstance(value, list):
            for item in value:
                collect(item)
            return

        if isinstance(value, str) and value.strip():
            pieces.append(value.strip())

    collect(node.get("relevant_contents", []))

    if len(pieces) == 1:
        collect(node.get("text", ""))

    return "\n\n".join(dict.fromkeys(pieces))


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về PageIndex SearchResult theo module contract."""
    if top_k <= 0 or not query.strip():
        return []

    mapping = _load_cache()
    if not mapping:
        upload_documents()
        mapping = _load_cache()

    client = _build_client()
    results = []

    for source, document_id in mapping.items():
        try:
            _wait_until_retrieval_ready(client, document_id)

            job = client.submit_query(
                document_id,
                query,
                thinking=False,
            )
            response = _wait_for_retrieval(client, job["retrieval_id"])
            nodes = response.get("retrieved_nodes", [])

        except Exception:
            # Task 9 sẽ thử document/provider khác hoặc trả hybrid result.
            continue

        for rank, node in enumerate(nodes, start=1):
            content = _node_content(node)
            if not content:
                continue

            node_id = str(node.get("node_id", rank))
            results.append(
                {
                    "id": f"pageindex::{document_id}::{node_id}",
                    "content": content,
                    # API không trả score chuẩn hoá, dùng rank-based score.
                    "score": float(1 / rank),
                    "metadata": {
                        "source": source,
                        "title": Path(source).stem,
                        "doc_type": "legal",
                        "url": None,
                        "chunk_index": rank - 1,
                    },
                    "retrieval_method": "pageindex",
                }
            )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    upload_documents()

    for result in pageindex_search(
        "Chiến lược phát triển du lịch đến năm 2030 là gì?",
        top_k=3,
    ):
        print(result)