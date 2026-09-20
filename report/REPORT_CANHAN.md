# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Việt Anh
**Nhóm:** Happy
**Ngày:** 20/9/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao có nghĩa là hai vector hướng về gần như cùng một phía trong không gian vector, thể hiện rằng hai đoạn văn bản có ý nghĩa hoặc ngữ nghĩa rất giống nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Kỹ thuật alternate picking giúp tăng tốc độ đánh phím đáng kể.
- Câu B: Việc gảy lên xuống liên tục hỗ trợ người chơi lead guitar chạy ngón nhanh hơn.
- Tại sao tương đồng: Hai câu sử dụng các từ vựng hoàn toàn khác nhau (alternate picking / gảy lên xuống liên tục, tăng tốc độ / chạy ngón nhanh hơn) nhưng truyền tải cùng một ý nghĩa, chứng minh embedding hiểu nghĩa chứ không chỉ so khớp từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Kỹ thuật alternate picking giúp tăng tốc độ gảy phím đáng kể.
- Câu B: Vòng hòa âm của bài hát này chủ yếu sử dụng các hợp âm thứ.
- Tại sao khác: Hai câu nói về hai khía cạnh hoàn toàn không liên quan đến nhau trong âm nhạc (một bên là kỹ thuật solo/lead, một bên là cấu trúc hợp âm đệm hát), do đó các vector embedding của chúng sẽ có hướng khác xa nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến góc giữa hai vector (phản ánh hướng/ngữ nghĩa) mà không bị ảnh hưởng bởi độ lớn của vector (bị chi phối bởi độ dài của văn bản, tần suất từ). Do đó, nó đánh giá độ tương đồng ngữ nghĩa hiệu quả hơn ngay cả khi hai văn bản có độ dài rất khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Áp dụng công thức `ceil((độ_dài − overlap) / (chunk_size − overlap))`. Ta có: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Nếu overlap tăng lên 100, số lượng chunk sẽ tăng lên: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks. Ta muốn giữ độ chồng chéo (overlap) lớn để đảm bảo ngữ nghĩa không bị đứt gãy ở ranh giới giữa các chunk (ví dụ tránh việc một câu quan trọng bị cắt làm đôi).

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng biểu thức chính quy (regex) với lookbehind `(?<=\.) |(?<=\!) |(?<=\?) |(?<=\.)\n` để tách câu. Việc này đảm bảo giữ lại nguyên vẹn các dấu câu ở cuối mỗi câu thay vì làm mất chúng; tôi cũng lọc bỏ các chuỗi rỗng bằng `.strip()` để xử lý trường hợp văn bản chứa nhiều khoảng trắng thừa.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy cắt thử đoạn văn bản bằng dấu phân cách ưu tiên cao (như `\n\n`), nếu các đoạn con thu được vẫn vượt quá `chunk_size` thì sẽ tiếp tục gọi đệ quy để cắt bằng dấu ưu tiên thấp hơn (như `. `); sau đó, các đoạn nhỏ liền kề sẽ được gom lại (merge) với nhau để độ dài sát với `chunk_size`. Các base case (điều kiện dừng) là: text rỗng, kích thước text đã nhỏ hoặc bằng `chunk_size`, hoặc đã hết dấu phân cách để thử.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Dữ liệu được lưu trữ dạng In-memory bằng một danh sách (`list`) chứa các dictionary ghi nhận ID, nội dung, metadata và vector nhúng (embedding). Khi tìm kiếm (`search`), câu truy vấn được chuyển thành vector, sau đó tính tích vô hướng (Dot Product) với mọi vector trong store để đo độ tương tự, sắp xếp giảm dần và trả về top K kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Trong `search_with_filter`, tôi tiến hành lọc (filter) trước các bản ghi khớp với điều kiện metadata để thu hẹp phạm vi, sau đó mới tính độ tương tự nhằm tối ưu tốc độ. Hàm xóa (`delete_document`) hoạt động bằng cách dùng List Comprehension để giữ lại toàn bộ các bản ghi ngoại trừ bản ghi có ID khớp với `doc_id` cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm gọi phương thức tìm kiếm của Vector Store để lấy các chunk nội dung liên quan, sau đó nối chúng lại bằng dấu xuống dòng để tạo thành chuỗi ngữ cảnh (context). Chuỗi này được ghép nối vào template prompt chuẩn bao gồm cả phần Context và Question trước khi gửi cho LLM để tạo ra câu trả lời cuối cùng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```markdown
=============================== test session starts ===============================

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%] 
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED       [ 23%] 
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED  [ 28%] 
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED        [ 33%] 
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED       [ 45%] 
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED  [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies
 PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

=============================== 42 passed in 0.09s ================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Làm sao để đăng ký bán hàng trên Shopee? | Hướng dẫn mở gian hàng trên Shopee. | cao | 0.152 | Sai |
| 2 | Giá cổ phiếu đang tăng mạnh. | Thị trường chứng khoán thăng hoa. | cao | -0.041 | Sai |
| 3 | Thời tiết hôm nay rất đẹp. | Giá vàng giảm sâu. | thấp | 0.110 | Đúng |
| 4 | Tôi yêu mèo. | Tôi thích mèo. | cao | -0.203 | Sai |
| 5 | Apple ra mắt iPhone 15. | Quả táo rụng xuống sân. | thấp | 0.401 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Điều bất ngờ nhất là các cặp câu đồng nghĩa lại có điểm cosine cực kỳ thấp (thậm chí âm), trong khi cặp không liên quan (như Cặp 5) lại ra điểm cao nhất. Lý do là hệ thống hiện tại đang sử dụng `Mock Embeddings` (băm ngẫu nhiên bằng MD5), tức là vector được sinh ra dựa trên chuỗi byte (ký tự) chứ không hề có mô hình ngôn ngữ nào đứng sau. Điều này chứng minh rằng việc dùng một Embedding Model thật (như OpenAI hay BERT) là bắt buộc để hệ thống hiểu được "ngữ nghĩa" của văn bản thay vì chỉ so khớp ký tự.*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền... | `dieu-khoan-shopee-mall` - "Phẩm bị lỗi. Mỗi Người Bán tại Shopee Mall..." | 0.287 | ❌ Không | Agent trả lời sai hoặc bảo không có thông tin (do lấy nhầm tài liệu). |
| 2 | Khi không đồng ý với quyết định hoàn tiền của Shopee... | `quy-dinh-dang-ban` - "b. Khi đăng bán sản phẩm trên Shopee..." | 0.294 | ❌ Không | Agent báo không tìm thấy thời hạn 2 ngày vì đưa nhầm luật đăng bán. |
| 3 | Người mua có thể yêu cầu trả hàng/hoàn tiền... | `quy-dinh-dang-ban` - "f. Không chứa từ khóa fake/nhái..." | 0.268 | ❌ Không | Agent báo không có thông tin trả hàng. |
| 4 | Người bán vi phạm chính sách chống gian lận bồi thường bao nhiêu? | `seller-return-refund-response` - "gười Mua trong trường hợp..." | 0.364 | ❌ Không | Agent đưa thông tin sai lệch về việc hoàn tiền thay vì mức phạt. |
| 5 | Nếu Shopee Mall phát hiện người bán bán hàng giả... | `dieu-khoan-shopee-mall` - "Người bán trả mức cao hơn giữa 9.818.180 VND..." | 0.266 | ✅ Có | Agent trả lời chuẩn xác con số 9.818.180 VND. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 1 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Tôi nhận thấy việc so sánh điểm số lúc này chưa phản ánh chiến lược chunking nào tốt hơn, mà chỉ cho thấy sự phụ thuộc vào may rủi của Mock Embeddings. Một nhóm khác đã setup API Key thật và kết quả của họ lập tức trả về đúng >90%, cho thấy sức mạnh thực sự của Vector Search nằm ở chất lượng của Embedding Model.*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
