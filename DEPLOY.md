# Đưa app chấm bài lên mây (làm một lần)

Mục tiêu: có một link cố định, mở trên iPhone ở bất cứ đâu, không cần bật máy tính.
Cách làm giống app Công việc: mã để trên GitHub, nhưng app chạy trên Streamlit Cloud.

**Lưu ý quan trọng:** bản đầu tiên này **chưa lưu điểm**. Máy chủ mây bị khởi động
lại là mất dữ liệu. Chỉ dùng để thử giao diện. Muốn dùng thật phải làm tiếp bước
nối Google Sheets.

## A. Tạo kho mã trên GitHub

1. Mở https://github.com/new
2. Ô **Repository name** gõ: `cham-bai`
3. Chọn **Private** (không công khai mã).
4. Bấm **Create repository**.

## B. Tải mã lên

Ở trang kho vừa tạo, bấm **uploading an existing file** (hoặc **Add file** →
**Upload files**), kéo các tệp sau từ `D:\HOC_CLAUDE_CODE\08_AppCongViec\ChamBaiToan`:

- `app.py`
- `cau_hinh.py`
- `cham_bai.py`
- `doc_bai.py`
- `luu_tru.py`
- `xuat_file.py`
- `requirements.txt`

Bấm **Commit changes**.

Sau đó tạo tệp cấu hình: **Add file** → **Create new file**, ô tên gõ đúng
`.streamlit/config.toml`, dán nội dung:

```
[server]
maxUploadSize = 30

[theme]
base = "light"
```

Bấm **Commit changes**.

**Tuyệt đối không tải lên:** `.env`, thư mục `du_lieu`, thư mục `_tam`.

## C. Tạo app trên Streamlit Cloud

1. Mở https://share.streamlit.io → **Sign in with GitHub**.
2. Bấm **Create app** → **Deploy a public app from GitHub** (ô chọn kho sẽ hiện
   cả kho private của Thầy).
3. Chọn: Repository `tcsonncs/cham-bai`, Branch `main`, Main file path `app.py`.
4. Bấm **Advanced settings** → ô **Secrets**, dán đúng hai dòng sau (thay bằng
   khoá Gemini thật, lấy trong tệp `.env` trên máy):

```
GEMINI_API_KEY = "AIza..."
```

5. Bấm **Deploy**. Chờ 2–5 phút.
6. Link app có dạng `https://cham-bai-xxxx.streamlit.app`.

## D. Để app riêng tư

Trong app: menu ba chấm (góc phải) → **Settings** → **Sharing** → chọn
**Only specific people can view this app** → nhập email Google của Thầy.
Chỉ tài khoản được mời mới xem được.

## E. Đưa lên màn hình chính iPhone

Mở link trong Safari → nút **Chia sẻ** → **Thêm vào Màn hình chính**.

## F. Cập nhật app sau này

Sửa tệp trên máy → vào GitHub → mở tệp → nút bút chì → dán nội dung mới →
**Commit changes**. Streamlit Cloud tự cập nhật sau 1–2 phút.

## Bước tiếp theo (bắt buộc trước khi dùng thật)

Nối Google Sheets để điểm không bị mất khi máy chủ khởi động lại. Cần:
- Một trang tính Google (Thầy tạo, đặt tên `ChamBaiToan`).
- Một service account của Google Cloud, tải tệp JSON, dán vào Secrets.
- Chia sẻ trang tính cho email của service account (quyền Sửa).
