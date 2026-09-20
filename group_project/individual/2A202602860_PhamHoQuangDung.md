# Individual contribution report

---

## Thông tin

- Họ và tên: Phạm Hồ Quang Dũng
- Mã học viên: 2A202602860
- Nhóm: ActionPlan
- Repository/branch: K4-L3A-RAG-Pipeline-ActionPlan / main

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1 — Thu thập tài liệu pháp lý | Thu thập thủ công 4 file PDF công khai về chủ đề du lịch Việt Nam (Nghị định, Thông tư hướng dẫn Luật Du lịch, Quyết định phê duyệt Chiến lược phát triển du lịch đến 2030, sách Việt Nam Văn hoá & Du lịch); đặt tên file không dấu | `data/landing/legal/*.pdf`, commit `91d97dd`, `22ad118` | Done |
| Task 2 — Crawl bài viết | Tìm 6 URL báo công khai (Báo Chính phủ, Nhân Dân) về du lịch Việt Nam; implement `crawl_article()` bằng Crawl4AI, lưu JSON đúng schema (`url`, `title`, `date_crawled`, `content_markdown`) | `src/task2_crawl_news.py`, `data/landing/news/article_01..06.json`, commit `91d97dd` | Done |
| Task 3 — Chuẩn hoá Markdown | Implement `convert_legal_docs()` (MarkItDown) và `convert_news_articles()`; thêm logic idempotent (skip file đã tồn tại/không rỗng) để không tạo file trùng/rỗng khi chạy lại | `src/task3_convert_markdown.py`, `data/standardized/legal/*.md`, `data/standardized/news/*.md`, commit `22ad118` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Đặt tên file PDF ở Task 1 theo dạng không dấu, không khoảng trắng (`nghi-dinh-quy-dinh-chi-tiet-luat-du-lich.pdf` thay vì tên gốc có dấu tiếng Việt).
   **Lý do/evidence:** Docstring Task 1 yêu cầu rõ "đặt tên không dấu"; tên có dấu/khoảng trắng dễ gây lỗi khi Task 4 dùng tên file làm `id` ổn định cho chunk.
   **Trade-off:** Mất một phần khả năng đọc trực quan tên file gốc, nhưng đổi lại tên file an toàn để dùng làm ID và tránh lỗi encoding trên các hệ thống khác nhau.

2. **Quyết định:** Kiểm tra thủ công từng PDF bằng MarkItDown trước khi tin tưởng kết quả convert, phát hiện 3/4 file PDF gốc là bản scan (không có lớp text, convert ra 0 ký tự), và thay thế bằng bản PDF có text layer.
   **Lý do/evidence:** Chạy `MarkItDown().convert()` riêng từng file cho thấy 3 file trả về `text_content` rỗng dù không có exception — nếu không kiểm tra sẽ tưởng nhầm là "mất dữ liệu" ở bước sau.
   **Trade-off:** Tốn thời gian tìm lại nguồn PDF khác (không phải scan) thay vì OCR; nhưng tránh được việc phải cài thêm pipeline OCR (Tesseract) phức tạp hơn cho một lab 3 giờ.

## Kiểm thử và kết quả

- Test tôi đã dùng: chạy script Python độc lập gọi `MarkItDown().convert()` trên từng file trong `data/landing/legal/` để đo `len(text_content.strip())`, phát hiện 3 file trả về 0 ký tự.
- Kết quả trước/sau: trước khi thay PDF — chỉ 1/4 file legal convert ra `.md` (dài 122k ký tự), 3 file còn lại bị Task 3 âm thầm skip (do check "nội dung rỗng thì không ghi file"). Sau khi thay 3 PDF bằng bản có text layer — cả 4 file đều convert thành công (24k–122k ký tự mỗi file).
- Lỗi đã phát hiện và cách xử lý: Task 3 ban đầu không có cơ chế báo lỗi khi PDF rỗng, dễ gây hiểu nhầm là "code xoá mất file". Đã thêm điều kiện skip an toàn (không ghi file rỗng, không ghi đè file đã có) để chạy lại nhiều lần không tạo trùng lặp, đúng yêu cầu contract.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: `content_markdown` của 6 bài báo (Task 2) vẫn còn lẫn nhiều nội dung nhiễu từ trang web (menu điều hướng, danh sách tỉnh thành, link "tham khảo thêm", footer bản quyền) chưa được lọc sạch trước khi đưa sang Task 3.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: thêm bước lọc nội dung (loại bỏ nav/footer, chỉ giữ phần bài viết chính) trước khi ghi ra Markdown ở Task 3, để giảm nhiễu cho việc chunking/embedding ở Task 4.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20-09-2026
- Tên thành viên: Phạm Hồ Quang Dũng
