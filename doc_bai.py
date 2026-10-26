# -*- coding: utf-8 -*-
"""Đọc ảnh bài làm: bóc chữ và đọc dấu bút chọn đáp án trắc nghiệm."""
from pathlib import Path

from cau_hinh import goi_gemini, parse_json

MIME = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}

PROMPT_DOC = """Đây là một trang bài làm môn Toán của học sinh Việt Nam, viết tay
trên đề in sẵn hoặc trên giấy.

Hãy làm ba việc:
1. Đọc họ và tên học sinh nếu có ghi trên trang. Không thấy thì để chuỗi rỗng.
2. Bóc toàn bộ nội dung bài làm, giữ đúng thứ tự câu. Công thức toán viết bằng
   LaTeX đặt trong $...$. Bảng viết bằng bảng Markdown.
3. Ghi lại những chỗ chữ viết không đọc chắc chắn, mỗi chỗ kèm hai cách đọc có thể.

Chỉ trả về JSON đúng định dạng sau, không thêm chữ nào ngoài JSON:
{"ten": "", "noi_dung": "", "cho_khong_ro": []}
"""

PROMPT_DAU_BUT = """Đây là ảnh chụp một trang đề kiểm tra Toán đã in sẵn. Học sinh
làm bài trực tiếp trên tờ đề bằng bút mực.

Nhiệm vụ: xác định học sinh đã CHỌN đáp án nào ở từng câu, dựa vào dấu bút.

Dấu bút của học sinh có thể là: khoanh tròn quanh chữ cái, gạch chân chữ cái,
đánh dấu tích, gạch chéo, tô đậm. Chữ cái in sẵn trên đề KHÔNG phải là đáp án
học sinh chọn — chỉ tính khi có dấu bút của học sinh đè lên hoặc bao quanh.

Quy tắc bắt buộc:
- Xét lần lượt từng câu trắc nghiệm có 4 phương án A, B, C, D trên trang.
- Phân biệt hai loại dấu:
  + Dấu CHỌN: khoanh tròn, gạch chân, đánh tích, tô đậm quanh chữ cái.
  + Dấu BỎ: chữ cái đã khoanh nhưng bị gạch chéo, gạch ngang, gạch đè lên
    hoặc tẩy xoá. Dấu bỏ KHÔNG tính là đáp án.
- Chỉ ghi vào "chon" những chữ cái mang dấu CHỌN còn hiệu lực.
- Nếu sau khi loại dấu bỏ vẫn còn từ hai chữ cái trở lên: ghi cả hai vào "chon"
  và đặt "chac": false.
- Nếu không thấy dấu bút nào, để mảng rỗng.
- Nếu không đọc chắc chắn, đặt "chac": false và ghi lý do vào "dau_hieu".
- Phần "trả lời đúng, sai": ghi ý a), b), c), d) học sinh chọn Đ hay S.
- Phần "trả lời ngắn": ghi số hoặc chữ học sinh viết, kèm số thứ tự câu.

Chỉ trả về JSON đúng định dạng sau, không thêm chữ nào ngoài JSON:
{"ten": "",
 "trac_nghiem": [{"cau": 1, "chon": ["A"], "dau_hieu": "", "chac": true}],
 "dung_sai": [{"cau": 11, "y": "a", "chon": "Đ", "chac": true}],
 "tra_loi_ngan": [{"cau": 12, "tra_loi": "", "chac": true}],
 "ghi_chu": ""}
"""


def mime_cua(ten: str) -> str:
    return MIME.get(Path(ten).suffix.lower(), "image/jpeg")


def _parts(anh: bytes, ten: str, prompt: str):
    from google.genai import types

    return [types.Part.from_bytes(data=anh, mime_type=mime_cua(ten)), prompt]


def doc_trang(anh: bytes, ten: str) -> dict:
    """Bóc chữ một trang."""
    return parse_json(goi_gemini(_parts(anh, ten, PROMPT_DOC)))


def doc_dau_but(anh: bytes, ten: str) -> dict:
    """Đọc dấu bút chọn đáp án trên một trang."""
    return parse_json(goi_gemini(_parts(anh, ten, PROMPT_DAU_BUT)))


def co_the_co_trac_nghiem(noi_dung: str) -> bool:
    """Đoán trang có phần trắc nghiệm để khỏi gọi AI thừa."""
    if not noi_dung:
        return False
    chu = noi_dung.lower()
    if "trắc nghiệm" in chu or "trả lời ngắn" in chu:
        return True
    if "| đúng |" in chu or "đúng | sai" in chu:
        return True
    so_dong_abcd = sum(
        1 for dong in noi_dung.splitlines()
        if dong.strip()[:2] in {"A.", "B.", "C.", "D."}
    )
    return so_dong_abcd >= 8


def doc_ca_bai(danh_sach_anh, tien_do=None) -> dict:
    """Đọc lần lượt các trang của một bài.

    danh_sach_anh: [(tên_tệp, bytes), ...]
    Trả về {"trang": [...], "trac_nghiem": {...}, "dung_sai": [...],
            "tra_loi_ngan": {...}, "ten": ""}
    """
    ket_qua = {"trang": [], "trac_nghiem": [], "dung_sai": [],
               "tra_loi_ngan": [], "ten": ""}
    for i, (ten, du_lieu) in enumerate(danh_sach_anh, 1):
        if tien_do:
            tien_do(i, len(danh_sach_anh), ten)
        trang = doc_trang(du_lieu, ten)
        trang["ten_tep"] = ten
        ket_qua["trang"].append(trang)
        if not ket_qua["ten"] and (trang.get("ten") or "").strip():
            ket_qua["ten"] = trang["ten"].strip()

        if co_the_co_trac_nghiem(trang.get("noi_dung", "")):
            dau_but = doc_dau_but(du_lieu, ten)
            ket_qua["trac_nghiem"].extend(dau_but.get("trac_nghiem") or [])
            ket_qua["dung_sai"].extend(dau_but.get("dung_sai") or [])
            ket_qua["tra_loi_ngan"].extend(dau_but.get("tra_loi_ngan") or [])
            if dau_but.get("ghi_chu"):
                trang["ghi_chu_dau_but"] = dau_but["ghi_chu"]
    return ket_qua


def gop_text(ket_qua_doc: dict) -> str:
    """Gộp nội dung các trang thành một văn bản, có đánh dấu trang."""
    phan = []
    for i, trang in enumerate(ket_qua_doc.get("trang") or [], 1):
        phan.append(f"--- Trang {i} ---\n{(trang.get('noi_dung') or '').strip()}")
    return "\n\n".join(phan)
