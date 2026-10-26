# Nối Google Sheets (làm một lần, khoảng 10 phút)

Mục đích: điểm và bài làm nằm trong một trang tính Google, máy chủ mây khởi
động lại cũng không mất.

## 1. Tạo trang tính

1. Mở https://sheets.new
2. Đổi tên tệp thành **ChamBaiToan** (bấm góc trái trên cùng).

## 2. Dán đoạn mã

1. Trong trang tính: menu **Tiện ích** (Extensions) → **Apps Script**.
2. Xoá hết đoạn mã mẫu trong khung soạn thảo.
3. Mở tệp `apps_script\Code.gs` trong thư mục này, chép **toàn bộ** nội dung,
   dán vào khung.
4. Tìm dòng `var TOKEN = 'THAY_TOKEN_VAO_DAY';` — thay `THAY_TOKEN_VAO_DAY`
   bằng mã riêng Claude đã đưa (giữ nguyên hai dấu nháy đơn).
5. Bấm biểu tượng **Save** (đĩa mềm) hoặc Ctrl+S.

## 3. Triển khai

1. Bấm **Deploy** (Triển khai) → **New deployment**.
2. Bấm biểu tượng bánh răng cạnh "Select type" → chọn **Web app**.
3. Điền:
   - Description: `Cham bai Toan`
   - **Execute as**: `Me`
   - **Who has access**: `Anyone`
4. Bấm **Deploy**.
5. Lần đầu Google sẽ hỏi cấp quyền: bấm **Authorize access** → chọn tài khoản →
   nếu hiện "Google hasn't verified this app" thì bấm **Advanced** →
   **Go to ... (unsafe)** → **Allow**.
6. Chép **Web app URL** (dạng `https://script.google.com/macros/s/AKfy.../exec`).

## 4. Khai báo trong Streamlit

1. Mở https://share.streamlit.io → app **cham-bai** → menu ba chấm →
   **Settings** → **Secrets**.
2. Thêm hai dòng (giữ nguyên dòng GEMINI_API_KEY đã có):

```
SHEETS_URL = "https://script.google.com/macros/s/.../exec"
SHEETS_TOKEN = "mã riêng ở bước 2"
```

3. Bấm **Save**. App tự khởi động lại.

## 5. Kiểm tra

Mở app → tạo một đợt thử → mở trang tính Google xem ba thẻ `dot_cham`,
`hoc_sinh`, `bai_lam` đã có dữ liệu chưa.

## Ghi chú

- Ảnh bài làm **không** lưu lên Google Sheets (dung lượng lớn). Ảnh chỉ nằm
  trên máy chủ trong lúc làm việc; máy chủ khởi động lại thì mất ảnh, nhưng
  nội dung đã bóc và điểm vẫn còn.
- Mỗi lần lưu, app gửi lại cả bảng nên trang tính luôn khớp với app. Vì vậy
  **không sửa tay** trong trang tính khi app đang mở.
- Nếu đổi mã TOKEN, phải sửa cả hai nơi (Apps Script và Secrets).
