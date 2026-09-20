# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: Nguyễn Đình Khang
- Mã học viên: 2A202602584
- Nhóm: ActionPlan
- Repository/branch: K4-L3A-RAG-Pipeline-ActionPlan / `khangnd`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Module / Công việc cụ thể | Nội dung mình thực hiện | File / Commit liên quan | Trạng thái |
|---|---|---|---|
| Task 7 - Hybrid retrieval | Xây dựng cơ chế hợp nhất kết quả từ BM25 và tìm kiếm ngữ nghĩa bằng thuật toán RRF; đồng thời chuẩn hóa dữ liệu trả về bao gồm nội dung đoạn, thông tin mô tả và điểm số. | `src/task7_hybrid_retrieval.py` | Hoàn thành |
| Task 8 - PageIndex fallback | Tích hợp PageIndex theo hướng không dùng vector; tái sử dụng mã tài liệu, gọi API và xử lý trường hợp dịch vụ không phản hồi. | `src/task8_pageindex_vectorless.py`, `.env.example` | Hoàn thành |
| Task 9 - Retrieval pipeline | Thiết kế luồng làm việc hoàn chỉnh: phân loại câu hỏi trước, gọi truy xuất kết hợp, lọc theo ngưỡng điểm, và tự động chuyển sang PageIndex nếu cần. | `src/task9_retrieval_pipeline.py` | Hoàn thành |
| Task 10 - Generation with ciation | Xử lý sinh câu trả lời dựa trên thông tin đã tìm thấy; hỗ trợ các nhà cung cấp AI khác nhau qua biến môi trường và ghi rõ nguồn tham khảo. | `src/task10_generation.py` | Hoàn thành |
| Demo | Kết nối bước tạo câu trả lời vào giao diện Streamlit, hiển thị rõ câu trả lời, cách thức truy xuất và các tài liệu đã dùng. | `app.py` | Hoàn thành |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Dùng Reciprocal Rank Fusion (RRF) để kết hợp BM25 và semantic retrieval trong Task 7.  
   **Lý do/evidence:** BM25 phù hợp với truy vấn chứa từ khóa hoặc tên văn bản cụ thể, trong khi semantic retrieval hỗ trợ câu hỏi diễn đạt tự nhiên. RRF kết hợp thứ hạng của hai nguồn mà không cần chuẩn hóa trực tiếp các loại score khác nhau.  
   **Trade-off:** Cần chạy nhiều retriever hơn nên tăng chi phí/thời gian truy xuất so với chỉ dùng một phương pháp.

2. **Quyết định:** Dùng PageIndex làm vectorless fallback trong Task 8–9 thay vì phụ thuộc hoàn toàn vào vector store.  
   **Lý do/evidence:** Khi hybrid retrieval không có kết quả đủ tốt hoặc semantic embedding không khả dụng, PageIndex vẫn có thể truy xuất theo cấu trúc tài liệu. Pipeline có trường `retrieval_method` để cho biết nguồn kết quả.  
   **Trade-off:** Phụ thuộc API bên ngoài, cần `PAGEINDEX_API_KEY`, và thời gian phản hồi có thể chậm hơn truy xuất local.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
  - `pytest tests/test_contracts.py -q`
  - `python -m src.task7_hybrid_retrieval`
  - `python -m src.task8_pageindex_vectorless`
  - `python -m src.task9_retrieval_pipeline`
  - `python -m src.task10_generation`
  - Query demo: “Mục tiêu phát triển du lịch Việt Nam đến năm 2030 là gì?” và “Định hướng phát triển du lịch biển, đảo là gì?”

- Kết quả trước/sau nếu có:
  - Các contract test chạy thành công: `15 passed`.
  - Pipeline trả về các chunk nguồn, phương thức truy xuất và câu trả lời có citation.
  - Task 10 gọi thành công OpenAI khi cấu hình `LLM_PROVIDER`, `LLM_MODEL` và `OPENAI_API_KEY` hợp lệ.

- Lỗi đã phát hiện và cách xử lý:
  - Lỗi PageIndex trả về evidence dạng object/list khó đọc: bổ sung xử lý trích xuất nội dung đệ quy trước khi đưa vào context.
  - Lỗi thiếu `LLM_MODEL` hoặc `OPENAI_API_KEY`: xác định cấu hình `.env` bị để trống/ghi đè bởi file mẫu; bổ sung hướng dẫn kiểm tra biến môi trường và khởi động lại Streamlit.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Thông báo lỗi từ LLM provider hiện còn chung chung vì exception được bắt để UI không bị dừng, nên người dùng khó biết chính xác lỗi cấu hình hay lỗi API.

- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Bổ sung logging và thông báo lỗi phân loại rõ hơn trong chế độ development; đồng thời thêm evaluation tự động cho chất lượng retrieval và citation.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20-09-2026
- Tên thành viên: Nguyễn Đình Khang 
