"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Chủ đề:
    Quy định về giáo dục đại học tại Việt Nam.

Yêu cầu:
    1. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    2. Lưu file gốc vào data/landing/legal/.
    3. Đặt tên file không dấu và thể hiện đúng nội dung.
    4. Không bypass WAF.

Nguồn sử dụng:
    Công báo Chính phủ Việt Nam
    https://congbao.chinhphu.vn/

Tài liệu:
    - Thông tư 06/2026/TT-BGDĐT:
      Quy chế tuyển sinh đại học.

    - Thông tư 54/2026/TT-BGDĐT:
      Quy định chương trình đào tạo các trình độ giáo dục đại học.

    - Thông tư 53/2026/TT-BGDĐT:
      Quy chế tuyển sinh và đào tạo sau đại học.
"""

import sys
from pathlib import Path
from urllib.parse import urljoin, unquote

import requests
import truststore
from bs4 import BeautifulSoup


# ============================================================
# 1. THƯ MỤC OUTPUT
# ============================================================

DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "landing"
    / "legal"
)


# ============================================================
# 2. DANH SÁCH VĂN BẢN
# ============================================================

DOCUMENTS = [
    {
        "name": "quy_che_tuyen_sinh_dai_hoc_06_2026.pdf",
        "page_url": (
            "https://congbao.chinhphu.vn/van-ban/"
            "thong-tu-so-06-2026-tt-bgddt-469029.htm"
        ),
        "document_number": "06/2026/TT-BGDĐT",
    },
    {
        "name": "quy_dinh_chuong_trinh_dao_tao_dai_hoc_54_2026.pdf",
        "page_url": (
            "https://congbao.chinhphu.vn/van-ban/"
            "thong-tu-so-54-2026-tt-bgddt-470099.htm"
        ),
        "document_number": "54/2026/TT-BGDĐT",
    },
    {
        "name": "quy_che_tuyen_sinh_dao_tao_sau_dai_hoc_53_2026.pdf",
        "page_url": (
            "https://congbao.chinhphu.vn/van-ban/"
            "thong-tu-so-53-2026-tt-bgddt-470098.htm"
        ),
        "document_number": "53/2026/TT-BGDĐT",
    },
]


# ============================================================
# 3. TẠO HTTP SESSION
# ============================================================

def create_session() -> requests.Session:
    """
    Tạo HTTP session dùng lại cho tất cả request.

    Requests mặc định dùng CA bundle của certifi. Trên Windows, bundle này
    có thể không chứa CA trung gian mà Windows đã tin cậy, dẫn đến lỗi
    CERTIFICATE_VERIFY_FAILED với CDN của Cổng Công báo. Dùng trust store
    của hệ điều hành để vẫn xác minh HTTPS đầy đủ, không tắt verify.
    """

    truststore.inject_into_ssl()
    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/pdf,"
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document,*/*"
            ),
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        }
    )

    return session


# ============================================================
# 4. TẠO THƯ MỤC
# ============================================================

def setup_directory() -> None:
    """
    Tạo thư mục data/landing/legal nếu chưa tồn tại.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("LEGAL DOCUMENT COLLECTION")
    print("=" * 70)
    print(f"Output directory: {DATA_DIR}")
    print()


# ============================================================
# 5. XÁC ĐỊNH LOẠI FILE
# ============================================================

def detect_file_type(
    content: bytes,
    content_type: str,
    url: str,
) -> str | None:
    """
    Kiểm tra file thực tế là PDF hay DOCX.

    PDF:
        thường bắt đầu bằng %PDF

    DOCX:
        thực chất là ZIP nên thường bắt đầu bằng PK
    """

    content_type = content_type.lower()
    decoded_url = unquote(url).lower()

    # PDF magic bytes
    if content.startswith(b"%PDF"):
        return ".pdf"

    # DOCX là file ZIP
    if content.startswith(b"PK"):
        if (
            ".docx" in decoded_url
            or "wordprocessingml" in content_type
            or "application/octet-stream" in content_type
        ):
            return ".docx"

    if "application/pdf" in content_type:
        return ".pdf"

    if "wordprocessingml.document" in content_type:
        return ".docx"

    return None


# ============================================================
# 6. TÌM LINK PDF/DOCX TRÊN TRANG CÔNG BÁO
# ============================================================

def find_download_url(
    session: requests.Session,
    page_url: str,
) -> tuple[str, str] | None:
    """
    Mở trang văn bản của Công báo Chính phủ và tìm link tải.

    Ưu tiên:
        1. PDF
        2. DOCX

    Return:
        (download_url, extension)

    Ví dụ:
        ("https://g7.cdnchinhphu.vn/...", ".pdf")
    """

    print("[PAGE]")
    print(f"  {page_url}")

    try:
        response = session.get(
            page_url,
            timeout=30,
            allow_redirects=True,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"[ERROR] Cannot open page: {error}")
        return None

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    pdf_urls = []
    docx_urls = []

    for tag in soup.find_all("a", href=True):
        href = tag.get("href", "").strip()

        if not href:
            continue

        full_url = urljoin(
            response.url,
            href,
        )

        decoded = unquote(full_url).lower()

        # Link Công báo có thể có dạng:
        # /api/download/stream?...file_name=...pdf
        if ".pdf" in decoded:
            pdf_urls.append(full_url)

        elif ".docx" in decoded:
            docx_urls.append(full_url)

    # Ưu tiên PDF
    if pdf_urls:
        print("[FOUND] PDF download URL")
        print(f"        {pdf_urls[0]}")
        return pdf_urls[0], ".pdf"

    # Nếu không có PDF thì dùng DOCX
    if docx_urls:
        print("[FOUND] DOCX download URL")
        print(f"        {docx_urls[0]}")
        return docx_urls[0], ".docx"

    print("[ERROR] No PDF/DOCX download link found.")
    return None


# ============================================================
# 7. DOWNLOAD FILE
# ============================================================

def download_file(
    session: requests.Session,
    url: str,
    filename: str,
) -> bool:
    """
    Download file và kiểm tra file có thực sự là PDF/DOCX.
    """

    output_path = DATA_DIR / filename

    # --------------------------------------------------------
    # Nếu file đã tồn tại
    # --------------------------------------------------------

    if (
        output_path.exists()
        and output_path.stat().st_size > 0
    ):
        print(
            f"[SKIP] Already exists: "
            f"{output_path.name}"
        )

        return True

    print("[DOWNLOAD]")
    print(f"  {filename}")

    try:
        response = session.get(
            url,
            timeout=60,
            allow_redirects=True,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"[ERROR] Download failed: {error}")
        return False

    content = response.content

    if not content:
        print("[ERROR] Download returned empty content.")
        return False

    content_type = response.headers.get(
        "Content-Type",
        "",
    )

    actual_extension = detect_file_type(
        content=content,
        content_type=content_type,
        url=response.url,
    )

    if actual_extension is None:
        print("[ERROR] Downloaded content is not PDF/DOCX.")
        print(f"        Content-Type: {content_type}")
        return False

    # --------------------------------------------------------
    # Đảm bảo extension đúng với file thật
    # --------------------------------------------------------

    output_path = output_path.with_suffix(
        actual_extension
    )

    # --------------------------------------------------------
    # Một PDF hợp lệ thường > vài KB.
    # Tránh lưu trang HTML lỗi thành PDF.
    # --------------------------------------------------------

    if len(content) < 5_000:
        print(
            "[ERROR] File is unexpectedly small "
            f"({len(content)} bytes)."
        )
        return False

    output_path.write_bytes(content)

    size_mb = len(content) / (
        1024 * 1024
    )

    print(
        f"[OK] Saved: {output_path.name}"
    )

    print(
        f"     Size : {size_mb:.2f} MB"
    )

    return True


# ============================================================
# 8. DOWNLOAD MỘT VĂN BẢN
# ============================================================

def download_document(
    session: requests.Session,
    document: dict,
) -> bool:
    """
    Quy trình:

        Page Công báo
              |
              v
        tìm link PDF/DOCX
              |
              v
          download
              |
              v
        kiểm tra file
              |
              v
            save
    """

    filename = document["name"]
    page_url = document["page_url"]
    document_number = document[
        "document_number"
    ]

    print()
    print("-" * 70)
    print(
        f"Document: {document_number}"
    )
    print("-" * 70)

    # --------------------------------------------------------
    # File đã tồn tại?
    # --------------------------------------------------------

    expected_path = DATA_DIR / filename

    if (
        expected_path.exists()
        and expected_path.stat().st_size > 0
    ):
        print(
            f"[SKIP] Already exists: "
            f"{filename}"
        )

        return True

    # --------------------------------------------------------
    # Tìm link download
    # --------------------------------------------------------

    result = find_download_url(
        session=session,
        page_url=page_url,
    )

    if result is None:
        return False

    download_url, extension = result

    # --------------------------------------------------------
    # Nếu chỉ tìm được DOCX thì đổi extension output
    # --------------------------------------------------------

    if extension == ".docx":
        filename = (
            Path(filename)
            .with_suffix(".docx")
            .name
        )

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    return download_file(
        session=session,
        url=download_url,
        filename=filename,
    )


# ============================================================
# 9. LIỆT KÊ FILE ĐÃ TẢI
# ============================================================

def get_downloaded_documents() -> list[Path]:
    """
    Chỉ lấy PDF và DOCX.

    Không tính:
        .gitkeep
        txt
        json
        file tạm
    """

    if not DATA_DIR.exists():
        return []

    return sorted(
        [
            path
            for path in DATA_DIR.iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                in {".pdf", ".docx"}
                and path.stat().st_size > 0
            )
        ]
    )


# ============================================================
# 10. DOWNLOAD TOÀN BỘ
# ============================================================

def download_documents() -> None:
    """
    Download tất cả tài liệu.
    """

    session = create_session()

    success_count = 0

    for document in DOCUMENTS:

        try:
            success = download_document(
                session=session,
                document=document,
            )

            if success:
                success_count += 1

        except Exception as error:
            print(
                f"[UNEXPECTED ERROR] {error}"
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    files = get_downloaded_documents()

    print()
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(
        f"Successful operations: "
        f"{success_count}/{len(DOCUMENTS)}"
    )

    print(
        f"Documents currently in directory: "
        f"{len(files)}"
    )

    print()

    if files:
        print("Files:")

        for file in files:

            size_kb = (
                file.stat().st_size / 1024
            )

            print(
                f"  - {file.name} "
                f"({size_kb:.1f} KB)"
            )

    print()

    # --------------------------------------------------------
    # Kiểm tra yêu cầu bài tập
    # --------------------------------------------------------

    if len(files) >= 3:

        print(
            "TASK PASSED: "
            "At least 3 PDF/DOCX documents collected."
        )

    else:

        print(
            "TASK NOT PASSED: "
            "Less than 3 documents were collected."
        )

        print(
            "Please check the errors above."
        )


# ============================================================
# 11. MAIN
# ============================================================

def main() -> None:
    """
    Entry point.
    """

    # Tránh lỗi UnicodeEncodeError khi chạy từ Windows shell dùng code page
    # không biểu diễn được đầy đủ tiếng Việt.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    setup_directory()

    download_documents()


if __name__ == "__main__":
    main()

