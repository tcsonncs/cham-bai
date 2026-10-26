# App chấm bài Toán

Chấm bài kiểm tra Toán viết tay qua ảnh chụp: đọc ảnh bằng Gemini, chấm theo
rubric, duyệt điểm, xuất Excel. Dùng cho lớp dạy thêm 3–10 học sinh.

## Thành phần

| Tệp | Việc |
|---|---|
| `app.py` | Giao diện Streamlit, 6 màn hình (thêm màn Chụp bài) |
| `doc_bai.py` | Đọc ảnh: bóc chữ và đọc dấu bút chọn đáp án |
| `cham_bai.py` | Lập rubric, chấm trắc nghiệm bằng quy tắc, chấm tự luận bằng Gemini |
| `nhap_hoc_sinh.py` | Đọc danh sách học sinh từ Excel/Word/CSV/TXT |
| `luu_tru.py` | Lưu trữ SQLite |
| `luu_tru_sheets.py` | Lưu trữ Google Sheets qua Apps Script |
| `xuat_file.py` | Xuất Excel |
| `cau_hinh.py` | Khoá API, mô hình, gọi Gemini |

## Chạy trên máy

```
pip install -r requirements.txt
```

Tạo tệp `.env` với dòng `GEMINI_API_KEY=...`, rồi:

```
streamlit run app.py
```

Trên Windows bấm đúp `CHAY_APP.bat`.

## Đưa lên mây

Xem `DEPLOY.md`.

## Nguyên tắc chấm

- Trắc nghiệm: so dấu bút với đáp án bằng quy tắc cố định, không gọi AI.
- Đúng/sai nhiều ý: theo bảng điểm trong rubric.
- Trả lời ngắn: so khớp số/chữ.
- Tự luận: Gemini chấm từng bước, điểm là bội số 0,25, không vượt trần.
- Chỗ không chắc hoặc có dấu gạch bỏ: gắn cờ để giáo viên quyết.
- Điểm gợi ý và điểm chốt lưu riêng để đo độ chính xác của AI.
