# Hướng dẫn dùng app chấm bài Toán

Cập nhật: 26/10/2026

## 1. Mở app

- **Trên mây (dùng được ở bất cứ đâu, không cần bật máy tính):**
  https://cham-bai-2026.streamlit.app — mở bằng Safari trên iPhone, đăng nhập
  bằng tài khoản Google đã được mời.
- **Trên máy tính:** bấm đúp `CHAY_APP.bat`. Trình duyệt tự mở
  `http://localhost:8501`.
- **Trên iPhone (cùng Wi-Fi với máy tính):** bấm đúp
  `CHAY_APP_DIEN_THOAI.bat`, nhìn dòng IPv4 hiện ra, rồi trên iPhone mở
  Safari gõ `http://<IPv4>:8501`.
- Tắt app: đóng cửa sổ đen.

## 1b. Dùng ở nơi khác (Wi-Fi khác, 4G) — Tailscale

Máy tính và iPhone được nối vào một **mạng riêng** của Tailscale, nên iPhone
vào được app từ bất cứ đâu mà người ngoài không thấy.

- Trên máy tính: cài Tailscale và đăng nhập.
- Trên iPhone: cài **Tailscale** từ App Store, đăng nhập **cùng tài khoản**
  đã dùng trên máy tính, bật công tắc VPN.
- Xem địa chỉ của máy tính bằng lệnh `tailscale ip -4`, rồi trên iPhone mở
  Safari gõ `http://<địa chỉ đó>:8501`.
- Máy tính phải **bật**, app phải **đang chạy** (`CHAY_APP.bat`), máy không
  được ngủ.
- Địa chỉ Tailscale giữ nguyên, không đổi như địa chỉ Wi-Fi trong nhà.

## 2. Trình tự một đợt chấm

1. **Đợt & đề** — tạo đợt, tải file Word đề + biểu điểm, bấm *Nhờ AI lập
   rubric*, đọc lại rubric rồi bấm *Dùng rubric này*.
2. **Học sinh** — dán danh sách họ tên, mỗi dòng một em.
3. **Ảnh & đọc** — chọn từng em, tải ảnh (hoặc chụp), bấm *Đọc bài bằng AI*.
   So nội dung bóc được với ảnh gốc, sửa chỗ sai, kiểm tra bảng trắc nghiệm,
   rồi bấm *Xác nhận nội dung*.
4. **Chấm & duyệt** — chọn em, bấm *Chấm bài*. Xem điểm, mở các câu có dấu ⚠️,
   sửa điểm nếu cần, bấm *Lưu & duyệt bài này*.
5. **Xuất** — tải bảng điểm Excel.

## 3. Cách chụp ảnh cho tốt

- Chụp thẳng, đủ sáng, không bị bóng tay.
- Mỗi trang một ảnh, chụp cả tờ giấy, không cắt mất lề.
- Trang đề trắc nghiệm phải thấy rõ dấu bút khoanh đáp án.
- Ảnh trùng thì bỏ bớt, đừng nạp hai lần cùng một trang.

## 4. Máy chấm những gì

| Phần | Cách chấm |
|---|---|
| Chọn A, B, C, D | Quy tắc cố định: so dấu bút với đáp án. Không gọi AI khi chấm. |
| Đúng/Sai nhiều ý | Quy tắc cố định theo bảng điểm trong rubric. |
| Trả lời ngắn | So khớp số/chữ với đáp án. |
| Tự luận | Gemini chấm theo từng bước của rubric. |

Chỗ nào không chắc, app gắn ⚠️ và để Thầy quyết. Điểm **gợi ý** và điểm
**chốt** lưu riêng để sau này đo được độ chính xác của máy.

## 5. Dữ liệu và chi phí

- Dữ liệu nằm trong `du_lieu\cham_bai.db` và `du_lieu\anh\`. Sao lưu cả thư mục
  này là đủ.
- Khoá API để trong `.env` (không đưa lên mạng, không chép vào tài liệu).
- Mỗi đợt 10 bài tốn khoảng vài nghìn đồng tiền gọi Gemini.

## 6. Chưa có ở bản này

- Chưa nối Google Sheets (dữ liệu mới lưu trên máy).
- Chưa xuất PDF từng học sinh và tin nhắn Zalo.
- Chưa xuất dữ liệu nghiên cứu ẩn danh.
- Chưa đưa lên Streamlit Cloud (mới chạy trên máy và trong Wi-Fi nhà).
