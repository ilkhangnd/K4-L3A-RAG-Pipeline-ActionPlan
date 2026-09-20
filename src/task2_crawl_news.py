"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://baochinhphu.vn/9-thang-dau-nam-an-giang-don-gan-235-trieu-luot-khach-thu-gan-58000-ty-dong-tu-du-lich-102260916090853595.htm",
    "https://baochinhphu.vn/du-lich-nhieu-tinh-mien-trung-tang-truong-tich-cuc-dip-2-9-102260903145415612.htm",
    "https://nhandan.vn/suc-hut-cua-du-lich-di-san-di-de-kham-pha-cau-chuyen-dang-sau-moi-diem-den-post989493.html",
    "https://nhandan.vn/luong-du-khach-nga-den-viet-nam-du-bao-cao-ky-luc-trong-nam-2026-post988386.html",
    "https://nhandan.vn/cong-vien-rong-chinh-thuc-dung-don-khach-tu-ngay-139-post988272.html",
    "https://nhandan.vn/phe-duyet-dieu-chinh-bo-sung-de-an-du-lich-tai-vuon-quoc-gia-con-dao-post987148.html",
]


async def crawl_article(url: str) -> dict:
    from datetime import datetime, timezone

    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        if not result.success:
            raise RuntimeError(result.error_message or "crawl failed")
        return {
            "url": url,
            "title": result.metadata.get("title", "Unknown"),
            "date_crawled": datetime.now(timezone.utc).isoformat(),
            "content_markdown": result.markdown,
        }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
