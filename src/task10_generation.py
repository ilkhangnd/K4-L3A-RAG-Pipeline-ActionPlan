"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").casefold()
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Bạn là trợ lý hỏi đáp về du lịch Việt Nam.

Chỉ trả lời bằng thông tin có trong Context.
Mỗi khẳng định thực tế phải có citation theo đúng dạng [Document N].
Không được bịa nguồn, số liệu hoặc citation.
Nếu Context không đủ để trả lời, hãy trả lời:
"Tôi không thể xác minh thông tin này từ nguồn hiện có."
"""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context, không sửa input."""
    if len(chunks) <= 2:
        return list(chunks)

    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title, source và document label để LLM citation."""
    parts = []

    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk["metadata"]
        parts.append(
            f"[Document {index} | Title: {metadata['title']} | "
            f"Source: {metadata['source']}]\n"
            f"{chunk['content']}"
        )

    return "\n\n---\n\n".join(parts)


def _require_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Thiếu {name} trong file .env.")
    return value


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic và trả text thuần."""
    if not LLM_MODEL:
        raise RuntimeError("Thiếu LLM_MODEL trong file .env.")

    if LLM_PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=_require_setting("OPENAI_API_KEY"))
        response = client.responses.create(
            model=LLM_MODEL,
            instructions=system_prompt,
            input=user_message,
            temperature=TEMPERATURE,
        )
        answer = (response.output_text or "").strip()

    elif LLM_PROVIDER == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=_require_setting("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
            ),
        )
        answer = (response.text or "").strip()

    elif LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic

        client = Anthropic(api_key=_require_setting("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=1024,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
        )
        answer = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", "") == "text"
        ).strip()

    else:
        raise ValueError(
            "LLM_PROVIDER phải là: openai, gemini hoặc anthropic."
        )

    if not answer:
        raise RuntimeError("LLM không trả về nội dung.")
    return answer


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Retrieve context, generate answer và trả GenerationResult."""
    chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    reordered_chunks = reorder_for_llm(chunks)
    context = format_context(reordered_chunks)

    user_message = (
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Hãy trả lời bằng tiếng Việt và dùng citation [Document N]."
    )

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception:
        answer = (
            "Tôi chưa thể tạo câu trả lời do lỗi LLM provider. "
            "Vui lòng thử lại sau."
        )

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": (
            "pageindex"
            if chunks[0]["retrieval_method"] == "pageindex"
            else "hybrid"
        ),
    }


if __name__ == "__main__":
    print(generate_with_citation("Chiến lược phát triển du lịch đến năm 2030 là gì?"))