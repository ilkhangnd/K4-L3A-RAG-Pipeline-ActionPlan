import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="Du lịch Việt Nam AI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top right, #d8f3ea 0, transparent 28%),
                #f7faf9;
            color: #17332d;
        }

        .block-container {
            max-width: 1120px;
            padding-top: 2.2rem;
            padding-bottom: 7rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d3b35 0%, #14584b 100%);
        }

        [data-testid="stSidebar"] * {
            color: #f3fffb !important;
        }

        [data-testid="stSidebar"] .stButton button {
            border: 1px solid rgba(255,255,255,.35);
            background: rgba(255,255,255,.10);
            color: white;
        }

        [data-testid="stSidebar"] .stButton button:hover {
            border-color: #9de3ce;
            background: rgba(255,255,255,.18);
        }

        .hero {
            padding: 2rem 2.2rem;
            border-radius: 24px;
            background: linear-gradient(135deg, #0d4b40, #16735e);
            color: white;
            box-shadow: 0 14px 35px rgba(15, 70, 59, .18);
            margin-bottom: 1.6rem;
        }

        .hero h1 {
            margin: 0;
            font-size: 2.4rem;
            line-height: 1.15;
        }

        .hero p {
            margin: .75rem 0 0;
            opacity: .9;
            font-size: 1.02rem;
        }

        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: .3rem .7rem;
            margin-bottom: .8rem;
            color: #d8fff2;
            background: rgba(255, 255, 255, .14);
            font-size: .82rem;
            font-weight: 600;
        }

        .section-title {
            margin: 1.3rem 0 .7rem;
            color: #174f43;
            font-size: 1rem;
            font-weight: 700;
        }

        [data-testid="stChatMessage"] {
            border: 1px solid #dceae5;
            border-radius: 18px;
            background: rgba(255, 255, 255, .82);
            padding: .35rem .85rem;
            margin-bottom: 1rem;
            box-shadow: 0 3px 12px rgba(19, 76, 63, .04);
        }

        [data-testid="stChatInput"] {
            border: 1px solid #b9d8ce;
            border-radius: 16px;
            background: white;
            box-shadow: 0 6px 20px rgba(19, 76, 63, .10);
        }

        [data-testid="stExpander"] {
            border: 1px solid #d7e7e1;
            border-radius: 12px;
            background: #fbfefd;
            margin-top: .55rem;
        }

        .source-meta {
            padding: .75rem .9rem;
            border-left: 4px solid #2f9e7c;
            border-radius: 8px;
            background: #effaf6;
            margin: .5rem 0 .8rem;
        }

        .welcome-card {
            border: 1px dashed #9ccfc0;
            border-radius: 18px;
            padding: 1.3rem 1.4rem;
            background: rgba(255, 255, 255, .72);
            margin-bottom: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "suggested_query" not in st.session_state:
    st.session_state.suggested_query = None


def show_sources(sources: list[dict], retrieval_source: str) -> None:
    """Hiển thị các tài liệu/chunks đã dùng để trả lời."""
    if not sources:
        return

    method_label = {
        "hybrid": "Hybrid retrieval",
        "pageindex": "PageIndex fallback",
        "dense": "Dense search",
        "bm25": "BM25 search",
    }.get(retrieval_source, retrieval_source)

    st.caption(f"📚 Nguồn truy xuất: {method_label}")

    for index, source in enumerate(sources, start=1):
        metadata = source.get("metadata", {})
        title = metadata.get("title", "Không rõ tiêu đề")
        filename = metadata.get("source", "Không rõ nguồn")
        score = float(source.get("score", 0))
        content = source.get("content", "")

        preview = content[:850]
        if len(content) > 850:
            preview += "\n\n…"

        with st.expander(f"📄 Document {index} — {title}"):
            st.markdown(
                f"""
                <div class="source-meta">
                    <b>Nguồn:</b> {filename}<br>
                    <b>Phương thức:</b> {source.get("retrieval_method", "N/A")} &nbsp; · &nbsp;
                    <b>Score:</b> {score:.4f}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(preview)


def show_message(message: dict) -> None:
    """Render một message đã lưu trong session."""
    role = message["role"]
    avatar = "🧭" if role == "assistant" else "👤"

    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

        if role == "assistant":
            show_sources(
                message.get("sources", []),
                message.get("retrieval_source", "none"),
            )


with st.sidebar:
    st.markdown("## 🧭 Du lịch Việt Nam AI")
    st.caption("Trợ lý hỏi đáp dựa trên tài liệu chính sách và thông tin du lịch.")

    st.divider()

    st.markdown("### Cấu hình tìm kiếm")
    top_k = st.slider(
        "Số lượng nguồn tham khảo",
        min_value=3,
        max_value=10,
        value=5,
        help="Số chunks tối đa dùng để tạo câu trả lời.",
    )

    st.divider()

    st.markdown("### Gợi ý")
    st.caption(
        "Câu trả lời chỉ dựa trên nguồn tài liệu được truy xuất và có citation."
    )

    if st.button("🗑️ Xóa lịch sử hội thoại", use_container_width=True):
        st.session_state.messages = []
        st.session_state.suggested_query = None
        st.rerun()


st.markdown(
    """
    <section class="hero">
        <div class="badge">RAG PIPELINE · VIETNAM TOURISM</div>
        <h1>Khám phá du lịch Việt Nam cùng AI</h1>
        <p>
            Hỏi về chính sách, chiến lược phát triển, tài nguyên và định hướng
            du lịch. Mọi câu trả lời đều kèm nguồn tham khảo.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome-card">
            <b>👋 Bạn muốn tìm hiểu điều gì?</b><br>
            Hãy chọn một câu hỏi gợi ý hoặc nhập câu hỏi của riêng bạn.
        </div>
        """,
        unsafe_allow_html=True,
    )

    suggestions = [
        "Mục tiêu phát triển du lịch Việt Nam đến năm 2030 là gì?",
        "Định hướng phát triển du lịch biển, đảo là gì?",
        "Tài nguyên du lịch Việt Nam gồm những nhóm nào?",
    ]

    columns = st.columns(3)
    for column, suggestion in zip(columns, suggestions):
        if column.button(suggestion, use_container_width=True):
            st.session_state.suggested_query = suggestion
            st.rerun()

for message in st.session_state.messages:
    show_message(message)

suggested_query = st.session_state.suggested_query
query = suggested_query or st.chat_input(
    "Nhập câu hỏi về du lịch Việt Nam..."
)

if query:
    st.session_state.suggested_query = None

    user_message = {"role": "user", "content": query}
    st.session_state.messages.append(user_message)

    with st.chat_message("user", avatar="👤"):
        st.markdown(query)

    with st.chat_message("assistant", avatar="🧭"):
        with st.spinner("Đang tìm nguồn và soạn câu trả lời..."):
            try:
                result = generate_with_citation(query, top_k=top_k)
            except Exception:
                result = {
                    "answer": (
                        "Mình chưa thể xử lý câu hỏi lúc này. "
                        "Vui lòng kiểm tra cấu hình API và thử lại."
                    ),
                    "sources": [],
                    "retrieval_source": "none",
                }

        st.markdown(result["answer"])
        show_sources(
            result.get("sources", []),
            result.get("retrieval_source", "none"),
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result.get("sources", []),
            "retrieval_source": result.get("retrieval_source", "none"),
        }
    )