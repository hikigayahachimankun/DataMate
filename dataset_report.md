# DataMate — Báo cáo thống kê dữ liệu Train

> Ngày đối chiếu: **02/11/2026**. Dữ liệu được đọc trực tiếp từ repository [DataMate](https://github.com/hikigayahachimankun/DataMate), nhánh [`analyze_dataset`](https://github.com/hikigayahachimankun/DataMate/tree/analyze_dataset), commit `70d8fb8371888a82b5ce5da4af194ed39b037479`.

## 1. Phạm vi

- Tập được thống kê: **train**, không bao gồm `public_test`.
- Câu hỏi: [`train/train/questions.jsonl`](https://github.com/hikigayahachimankun/DataMate/blob/analyze_dataset/train/train/questions.jsonl).
- Đáp án chuẩn (gold): [`train/train/answers.jsonl`](https://github.com/hikigayahachimankun/DataMate/blob/analyze_dataset/train/train/answers.jsonl).
- Ghép hai file bằng trường `id`; nhóm câu hỏi theo `business_id`; loại đáp án xác định từ trường `type` của bản ghi đáp án.

## 2. Tổng quan

| Chỉ số | Kết quả |
|---|---:|
| Tổng số câu hỏi | 3.000 |
| Tổng số đáp án chuẩn | 3.000 |
| Số `business_id` khác nhau | 30 |
| Số loại đáp án xuất hiện trong gold | 8 |
| Số `id` ghép được giữa câu hỏi và đáp án | 3.000 |
| Số đáp án có `alias` không rỗng | 167 |
| `as_of_date` sớm nhất | 2025-01-15 |
| `as_of_date` muộn nhất | 2026-09-20 |

*Lưu ý:* Khoảng ngày ở trên là giá trị `as_of_date` trong câu hỏi, **không phải** khoảng thời gian của các giao dịch trong file dữ liệu doanh nghiệp.

## 3. Số câu hỏi theo business

| Business | Số câu hỏi | Số loại đáp án xuất hiện |
|---|---:|---:|
| `biz_101` | 40 | 3 |
| `biz_102` | 119 | 5 |
| `biz_103` | 119 | 7 |
| `biz_104` | 119 | 5 |
| `biz_105` | 119 | 7 |
| `biz_106` | 119 | 8 |
| `biz_107` | 40 | 3 |
| `biz_108` | 119 | 5 |
| `biz_109` | 118 | 8 |
| `biz_110` | 40 | 2 |
| `biz_111` | 118 | 5 |
| `biz_112` | 118 | 6 |
| `biz_113` | 40 | 3 |
| `biz_114` | 40 | 3 |
| `biz_115` | 118 | 5 |
| `biz_116` | 118 | 4 |
| `biz_117` | 118 | 7 |
| `biz_118` | 118 | 6 |
| `biz_119` | 118 | 5 |
| `biz_120` | 118 | 5 |
| `biz_121` | 118 | 7 |
| `biz_122` | 118 | 7 |
| `biz_123` | 118 | 8 |
| `biz_124` | 118 | 8 |
| `biz_125` | 40 | 3 |
| `biz_126` | 40 | 3 |
| `biz_127` | 118 | 6 |
| `biz_128` | 118 | 5 |
| `biz_129` | 118 | 6 |
| `biz_130` | 118 | 7 |
| **Tổng** | **3.000** | — |

**Nhận xét:** Phân bố số câu hỏi giữa các business không đồng đều: có business với 40 câu, 118 câu hoặc 119 câu. Vì vậy, khi xây validation/holdout cần chia theo `business_id`, không chia ngẫu nhiên theo câu hỏi.

## 4. Phân bố loại đáp án (`answers.jsonl`)

| `type` | Số đáp án | Tỷ lệ |
|---|---:|---:|
| `boolean` | 23 | 0,77% |
| `date` | 145 | 4,83% |
| `list` | 193 | 6,43% |
| `number` | 1.884 | 62,80% |
| `percent` | 578 | 19,27% |
| `string` | 88 | 2,93% |
| `table` | 19 | 0,63% |
| `unanswerable` | 70 | 2,33% |
| **Tổng** | **3.000** | **100,00%** |

*Tỷ lệ đã làm tròn đến hai chữ số thập phân.*

**Nhận xét:** `number` và `percent` chiếm phần lớn dữ liệu; `boolean` và `table` xuất hiện ít. Khi viết evaluator nên có unit test cho tất cả 8 `type` xuất hiện trong gold.

**Phân biệt:** `unanswerable` là một loại đáp án trong gold (70 câu). `abstain` là lựa chọn bỏ qua khi dự đoán/chấm PA; **không xuất hiện dưới dạng `type` trong tập gold đã thống kê**. Bộ chấm vẫn phải hỗ trợ `abstain` như kế hoạch PBL.

## 5. Kiểm tra tính toàn vẹn

| Kiểm tra | Số ID / bản ghi vi phạm |
|---|---:|
| ID trùng trong `questions.jsonl` | 0 |
| ID trùng trong `answers.jsonl` | 0 |
| ID có trong câu hỏi nhưng không có đáp án | 0 |
| ID có trong đáp án nhưng không có câu hỏi | 0 |
| Bản ghi câu hỏi thiếu/rỗng một trong `id`, `business_id`, `question`, `as_of_date` | 0 |
| Bản ghi đáp án thiếu/rỗng `id`, `type` hoặc thiếu trường `answer` | 0 |

**Kết luận kiểm tra:** Không phát hiện các lỗi trên trong hai file JSONL của commit đã đối chiếu. Điều này không đồng nghĩa mọi phép tính nghiệp vụ hoặc đáp án đều đã được kiểm chứng.

## 6. Việc cần làm tiếp theo trong công đoạn 1

1. Tạo `split_manifest.json`: chọn **20 business development / 5 validation / 5 holdout**; cân bằng dạng dữ liệu, ngành và các loại đáp án; **giữ holdout kín cho kiểm tra cuối**.
2. Xây `evaluate.py` để đối chiếu dự đoán với gold, chấm **PA = (số đúng − số sai) / tổng số câu**, hỗ trợ `abstain` và các kiểu đáp án.
3. Xuất `errors.csv` khi chấm để dễ phân loại lỗi; bổ sung unit tests cho evaluator.

---

**Cách tái lập:** Đọc hai JSONL ở mục 1, đếm theo `business_id` và `type`, kiểm tra ID trùng và phép hiệu hai tập ID. Đây là báo cáo đã tổng hợp từ snapshot GitHub nêu trên; file `scripts/analyze_dataset.py` hiện tại chưa tự xuất toàn bộ nội dung báo cáo này. Nếu dữ liệu nguồn thay đổi, cần chạy thống kê lại.
