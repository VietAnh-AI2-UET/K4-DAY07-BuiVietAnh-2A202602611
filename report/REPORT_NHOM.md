# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Happy
**Thành viên:** Bùi Việt Anh, Đinh Đức Long, Võ Thành Danh, Hà Anh Tuấn
**Ngày:** 20/9/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Ecommerce

**Tại sao nhóm chọn chủ đề này?**
> Thương mại điện tử (Ecommerce) là một lĩnh vực có nhiều chính sách phức tạp và thường xuyên thay đổi đối với cả người mua và người bán. Việc lựa chọn chủ đề này giúp nhóm thử nghiệm khả năng hệ thống phân loại chính xác tài liệu theo đối tượng (buyer/seller) và hỗ trợ giải đáp các thắc mắc thường gặp về chính sách đổi trả, đăng bán và quy định gian lận của sàn.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền cho người mua | https://help.shopee.vn/portal/4/article/77251 | 2026-09-20 / not-stated | 19.503 | doc_id, title, source_url, retrieved_at, document_version, audience, category, language |
| 2 | Trách nhiệm phản hồi yêu cầu trả hàng và hoàn tiền của người bán | https://help.shopee.vn/portal/4/article/77251 | 2026-09-20 / not-stated | 19.543 | doc_id, title, source_url, retrieved_at, document_version, audience, category, language |
| 3 | Quy định về đăng bán sản phẩm trên Shopee | https://help.shopee.vn/portal/4/article/77246 | 2026-09-20 / not-stated | 21.214 | doc_id, title, source_url, retrieved_at, document_version, audience, category, language |
| 4 | Chính sách chống gian lận và biện pháp xử lý người bán vi phạm Shopee | https://help.shopee.vn/portal/4/article/140097 | 2026-09-20 / not-stated | 6.558 | doc_id, title, source_url, retrieved_at, document_version, audience, category, language |
| 5 | Điều Khoản Dịch Vụ của Shopee Mall (Buyer) | https://help.shopee.vn/portal/4/article/77262 | 2026-09-20 / not-stated | 33.410 | doc_id, title, source_url, retrieved_at, document_version, audience, category, language |
| 6 | Điều Khoản Dịch Vụ của Shopee Mall (Seller) | https://help.shopee.vn/portal/4/article/77262 | 2026-09-20 / not-stated | 33.412 | doc_id, title, source_url, retrieved_at, document_version, audience, category, language |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `quy-dinh-dang-ban` | Định danh duy nhất cho tài liệu, giúp lọc chính xác tài liệu cụ thể. |
| `title` | string | `Quy định về đăng bán sản phẩm` | Hữu ích cho việc hiển thị hoặc lọc tài liệu theo tiêu đề. |
| `source_url` | string | `https://help.shopee.vn/...` | Cung cấp nguồn tham chiếu để người dùng có thể đối chiếu. |
| `retrieved_at` | string | `2026-09-20` | Giúp xác định tính mới, độ cập nhật của tài liệu. |
| `document_version`| string | `not-stated` | Đảm bảo lấy đúng phiên bản chính sách có hiệu lực. |
| `audience` | string | `buyer`, `seller` | Rất quan trọng để lọc chính xác thông tin dựa theo đối tượng hỏi, tránh trộn lẫn quy định của người bán và người mua. |
| `category` | string | `return-refund` | Hỗ trợ phân nhóm và tăng độ chuẩn xác khi tìm kiếm trong một mảng chuyên đề nhất định. |
| `language` | string | `vi` | Lọc ra văn bản đúng với ngôn ngữ truy vấn của người dùng. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `buyer-return-refund-policy.md` | FixedSizeChunker (`fixed_size`) | 44 | 491 ký tự | Kém (thường xuyên cắt ngang câu và từ) |
| `buyer-return-refund-policy.md` | SentenceChunker (`by_sentences`) | 42 | 460 ký tự | Khá (giữ trọn vẹn câu, nhưng tách rời ý của 1 điều khoản) |
| `buyer-return-refund-policy.md` | RecursiveChunker (`recursive`) | 60 | 322 ký tự | Tốt (bảo toàn trọn vẹn cụm/câu/đoạn) |
| `seller-return-refund-response.md` | FixedSizeChunker (`fixed_size`) | 44 | 491 ký tự | Kém (thường xuyên cắt ngang câu và từ) |
| `seller-return-refund-response.md` | SentenceChunker (`by_sentences`) | 42 | 461 ký tự | Khá (giữ trọn vẹn câu, nhưng tách rời ý của 1 điều khoản) |
| `seller-return-refund-response.md` | RecursiveChunker (`recursive`) | 60 | 322 ký tự | Tốt (bảo toàn trọn vẹn cụm/câu/đoạn) |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Bùi Việt Anh**
- **Loại chiến lược:** RecursiveChunker
- **Mô tả & lý do chọn cho chủ đề này:** Phù hợp với văn bản có cấu trúc phân tầng tự nhiên như chính sách, điều khoản của Shopee. Chiến lược này giúp cắt văn bản ưu tiên theo đoạn văn (`\n\n`), sau đó đến câu (`. `) để hạn chế tối đa việc cắt ngang câu hoặc cụm từ, giúp bảo toàn ngữ nghĩa tốt hơn.
- **Code snippet (nếu custom):** (Sử dụng lớp `RecursiveChunker` đã có sẵn trong mã nguồn)

**Thành viên 2 — Hà Anh Tuấn**
- **Loại chiến lược:** SentenceChunker
- **Mô tả & lý do chọn:** Chiến lược này tách văn bản dựa trên ranh giới câu (dấu chấm, chấm than, dấu hỏi). Việc gộp một số câu lại làm một chunk giúp bảo toàn tính toàn vẹn của câu, tránh việc cắt ngang chữ như cắt cứng theo ký tự.
- **Code snippet (nếu custom):** (Sử dụng lớp `SentenceChunker` có sẵn)

**Thành viên 3 — Đinh Đức Long**
- **Loại chiến lược:** RecursiveChunker
- **Mô tả & lý do chọn:** (Cùng lựa chọn với Thành viên 1) Phân rã văn bản đệ quy theo thứ tự dấu phân cách (`\n\n`, `\n`, `. `). Cắt theo cách này mô phỏng khá tốt cấu trúc logic của văn bản mà không cần xử lý ngôn ngữ tự nhiên quá sâu.
- **Code snippet (nếu custom):** (Sử dụng lớp `RecursiveChunker` có sẵn)

**Thành viên 4 — Võ Thành Danh**
- **Loại chiến lược:** FixedSizeChunker
- **Mô tả & lý do chọn:** Cắt văn bản cơ học theo một số lượng ký tự cố định (như 500 ký tự) có kèm theo phần gối đầu (overlap). Đây là chiến lược đơn giản, dễ cài đặt và đảm bảo các khối văn bản (chunk) luôn đồng đều về kích thước.
- **Code snippet (nếu custom):** (Sử dụng lớp `FixedSizeChunker` có sẵn)

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Bùi Việt Anh | RecursiveChunker | 1/10 | Giữ được trọn vẹn câu/đoạn, không cắt ngang chữ | Vẫn có thể tách rời nội dung một mục nếu mục đó dài quá chunk_size |
| Hà Anh Tuấn | SentenceChunker | 4/10 (Đúng 2/5 câu) | Đảm bảo không bao giờ bị đứt nửa câu, bảo toàn trọn vẹn ngữ pháp từng câu | Làm mất ngữ cảnh rộng (mất tiêu đề), đoạn văn bị nát vụn nếu điều khoản quá dài |
| Đinh Đức Long | RecursiveChunker | 1/10 (Đúng 1/5 câu) | Giữ được cấu trúc đoạn và câu linh hoạt so với các cách cắt cứng | Kết quả (1/10) phản ánh nhược điểm trầm trọng của việc dùng Mock Embeddings |
| Võ Thành Danh | FixedSizeChunker | 8/10 (Đúng 4/5 câu) | Đảm bảo các chunk có dung lượng đồng đều, dễ kiểm soát token LLM | Dễ cắt ngang một câu làm câu bị đứt đoạn, phá vỡ ngữ pháp và mất ngữ cảnh |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Về mặt logic, RecursiveChunker là chiến lược tốt nhất cho bộ dữ liệu chính sách Shopee. Các văn bản điều khoản có cấu trúc phân tầng tự nhiên, việc cắt đệ quy theo đoạn văn (`\n\n`) và câu (`. `) giúp bảo toàn nguyên vẹn từng quy định, không làm đứt đoạn ý nghĩa như FixedSizeChunker. Tuy nhiên, kết quả thực tế trên công cụ benchmark bị sai lệch do nhóm đang dùng Mock Embeddings, khiến điểm số của FixedSizeChunker cao bất thường một cách ngẫu nhiên.*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn giao thành công? Riêng thực phẩm tươi sống/đông lạnh thì sao? | Thời hạn chung là 15 ngày kể từ khi đơn cập nhật giao thành công; thực phẩm tươi sống hoặc đông lạnh là 24 giờ. | `buyer-return-refund-policy` |
| 2 | `metadata_filter={"audience": "seller"}`: Khi không đồng ý với quyết định hoàn tiền của Shopee, người bán phải phản hồi trong bao lâu? | Người bán phải phản hồi trong vòng 2 ngày lịch kể từ khi nhận thông báo của Shopee, trừ khi Shopee quy định thời hạn khác. | `seller-return-refund-response` |
| 3 | Người mua có thể yêu cầu trả hàng/hoàn tiền trong những trường hợp nào? | Ví dụ: không nhận/nhận thiếu hàng, hàng giả/nhái, hàng lỗi hoặc hư hại khi vận chuyển, giao sai hàng... | `buyer-return-refund-policy` |
| 4 | Người bán vi phạm chính sách chống gian lận có thể phải bồi thường tối đa bao nhiêu cho mỗi đơn hàng vi phạm? | Từ 28/12/2023, Shopee có thể áp dụng khoản bồi thường lên đến 10.000.000 VND cho mỗi đơn hàng vi phạm. | `shopee-chinh-sach-chong-gian-lan-nguoi-ban` |
| 5 | Nếu Shopee Mall phát hiện người bán bán hàng giả, hàng nhái, hàng không rõ xuất xứ hoặc phân phối bất hợp pháp, mức phí và thời hạn thanh toán là gì? | Người bán trả mức cao hơn giữa 9.818.180 VND và 100% giá trị sản phẩm vi phạm, trong vòng 7 ngày lịch. | `dieu-khoan-shopee-mall` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Câu 1 | SentenceChunker | Có (Top 1) | Điểm số hên xui do chạy bằng Mock Embeddings |
| 2 | Câu 2 | FixedSize / Sentence | Có (Top 2) | Metadata filter hoạt động hoàn hảo, chỉ tìm trong đúng tài liệu của Seller |
| 3 | Câu 3 | FixedSizeChunker | Có (Top 2) | Nội dung trích xuất ngẫu nhiên, không chứa ngữ cảnh cụ thể |
| 4 | Câu 4 | FixedSizeChunker | Có (Top 2) | Tương tự như trên |
| 5 | Câu 5 | FixedSize / Recursive | Có (Top 1 / Top 2) | Tìm đúng file `dieu-khoan-shopee-mall` |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Có, việc lọc metadata đặc biệt phát huy tác dụng ở **Câu hỏi số 2**. Vì kho dữ liệu có 2 tệp chính sách trả hàng với bộ từ vựng y hệt nhau (một cho buyer, một cho seller), nên nếu không có filter `audience: seller`, hệ thống rất dễ lấy nhầm thời hạn phản hồi bên phía người mua.*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. Tầm quan trọng của việc dùng Embedding Model thật: Mock Embeddings khiến kết quả hoàn toàn ngẫu nhiên (chó ngáp phải ruồi), làm sai lệch việc đánh giá các chiến lược Chunking.
> 2. Phân tích lợi hại của từng Chunking: FixedSize dễ code nhưng dễ làm nát ngữ nghĩa, Sentence giữ nguyên câu nhưng làm đứt đoạn văn, Recursive linh hoạt nhất.

**Bài học rút ra khi so sánh trong nhóm:**
> *Cùng một tài liệu và câu hỏi, nhưng nếu chiến lược chunking cắt đứt ngữ cảnh (cắt ngang câu hoặc tách câu khỏi tiêu đề), hệ thống dù có tìm trúng cũng trả về những đoạn văn bản cụt lủn. LLM agent (ở giai đoạn Generation) sau đó sẽ bị thiếu thông tin để trả lời trọn vẹn, gây ra ảo giác (hallucination).*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Nhóm sẽ xây dựng một `HeadingChunker` chuyên biệt để cắt tài liệu dựa trên các thẻ tiêu đề (ví dụ: `## Điều 1, Điều 2`). Với các văn bản quy phạm pháp luật/điều khoản của Shopee, đây là cách duy nhất để bảo toàn ngữ nghĩa tuyệt đối.*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **37 / 40** |
