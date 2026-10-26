# -*- coding: utf-8 -*-
"""Đọc danh sách học sinh từ file Excel, Word, CSV hoặc TXT.

Dùng cho nút "Nhập từ file" ở màn hình Học sinh. Kết quả là danh sách
``{"ho_ten": ..., "ma_hs": ...}`` theo đúng thứ tự trong file, đã bỏ trùng
và bỏ dòng tiêu đề.

Excel đọc được cả .xlsx/.xlsm (openpyxl) và .xls kiểu cũ (xlrd).
"""
import io
import re

# Từ khoá nhận ra dòng tiêu đề và cột họ tên
TU_KHOA_TEN = ("họ và tên", "họ tên", "họ, tên", "tên học sinh", "họ lót",
               "họ đệm", "họ", "tên")
TU_KHOA_MA = ("mã hs", "mã học sinh", "mã số", "mã", "mshs", "stt mã")


def _chuan_hoa(chuoi) -> str:
    """Bỏ số thứ tự ở đầu dòng, gộp khoảng trắng."""
    chuoi = str(chuoi).replace(" ", " ")
    chuoi = re.sub(r"^\s*\d+\s*[\.\)\-:]\s*", "", chuoi)
    chuoi = re.sub(r"^\s*(hs|học sinh|em)\s*[:\-]\s*", "", chuoi, flags=re.I)
    return re.sub(r"\s+", " ", chuoi).strip()


def giong_ho_ten(chuoi) -> bool:
    """Đoán một chuỗi có phải họ tên người không.

    Chấp nhận 2–7 tiếng, mỗi tiếng viết hoa chữ đầu, không có chữ số.
    Nhờ vậy loại được dòng tiêu đề ("Họ và tên") và dòng ghi chú.
    """
    chuoi = _chuan_hoa(chuoi)
    if not chuoi or any(ch.isdigit() for ch in chuoi):
        return False
    if any(ch in chuoi for ch in "@:/\\"):
        return False
    tu = chuoi.split()
    if not 2 <= len(tu) <= 7:
        return False
    if not (tu[0][0].isalpha() and tu[0][0].isupper()):
        return False
    # Cho phép vài tiếng viết thường (một số danh sách ghi "Nguyễn văn An")
    so_viet_hoa = sum(1 for t in tu if t[0].isalpha() and t[0].isupper())
    if so_viet_hoa / len(tu) < 0.6:
        return False
    # Loại dòng tiêu đề và ghi chú thường gặp
    if chuoi.casefold().startswith(("họ và", "họ tên", "danh sách", "lớp",
                                    "stt", "tt", "tổng")):
        return False
    return True


def _la_tieu_de(o) -> str:
    """Dòng tiêu đề cột: trả về 'ten', 'ma' hoặc ''."""
    chuoi = _chuan_hoa(o).casefold()
    if not chuoi or len(chuoi) > 40:
        return ""
    if any(k in chuoi for k in ("mã", "mshs")) and "tên" not in chuoi:
        return "ma"
    if "tên" in chuoi or chuoi in ("họ", "họ lót", "họ đệm"):
        return "ten"
    return ""


def _tu_bang(cac_dong) -> list:
    """cac_dong: danh sách dòng, mỗi dòng là danh sách ô (chuỗi).

    Tìm dòng tiêu đề để biết cột họ tên/cột mã; không có tiêu đề thì chọn
    cột có nhiều ô giống họ tên nhất.
    """
    cac_dong = [[_chuan_hoa(o) for o in dong] for dong in cac_dong]
    cac_dong = [d for d in cac_dong if any(x for x in d)]

    cot_ten = cot_ma = None
    bat_dau = 0
    for i, dong in enumerate(cac_dong[:6]):
        nhan = [_la_tieu_de(o) for o in dong]
        if "ten" in nhan:
            cot_ten = nhan.index("ten")
            cot_ma = nhan.index("ma") if "ma" in nhan else None
            bat_dau = i + 1
            # "Họ lót" + "Tên" tách hai cột: ghép lại
            if cot_ten + 1 < len(nhan) and nhan[cot_ten + 1] == "ten":
                cot_ten = (cot_ten, cot_ten + 1)
            break

    phan_con = cac_dong[bat_dau:]
    if cot_ten is None:
        # Không có tiêu đề: chọn cột nhiều họ tên nhất
        so_cot = max((len(d) for d in phan_con), default=0)
        tot_nhat, ti_le = None, 0.0
        for c in range(so_cot):
            gia_tri = [d[c] for d in phan_con if c < len(d) and d[c]]
            if not gia_tri:
                continue
            ti_le_cot = sum(1 for v in gia_tri if giong_ho_ten(v)) / len(gia_tri)
            if ti_le_cot > ti_le:
                tot_nhat, ti_le = c, ti_le_cot
        if tot_nhat is None or ti_le < 0.5:
            return []
        cot_ten = tot_nhat

    ket_qua = []
    for dong in phan_con:
        if isinstance(cot_ten, tuple):
            phan = [dong[c] if c < len(dong) else "" for c in cot_ten]
            ten = " ".join(x for x in phan if x)
        else:
            ten = dong[cot_ten] if cot_ten < len(dong) else ""
        ten = _chuan_hoa(ten)
        if not ten:
            continue
        if not giong_ho_ten(ten):
            continue
        ma = ""
        if cot_ma is not None and cot_ma < len(dong):
            ma = dong[cot_ma].strip()
        ket_qua.append({"ho_ten": ten, "ma_hs": ma})
    return ket_qua


def _tu_excel(du_lieu: bytes) -> list:
    import pandas as pd

    khung = pd.read_excel(io.BytesIO(du_lieu), header=None, dtype=str)
    cac_dong = khung.fillna("").values.tolist()
    return _tu_bang(cac_dong)


def _tu_word(du_lieu: bytes) -> list:
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    tai_lieu = docx.Document(io.BytesIO(du_lieu))
    ket_qua = []
    for con in tai_lieu.element.body.iterchildren():
        if con.tag.endswith("}tbl"):
            bang = Table(con, tai_lieu)
            cac_dong = [[o.text for o in dong.cells] for dong in bang.rows]
            # Giữ thứ tự xuất hiện, không lặp lại tên đã có
            for muc in _tu_bang(cac_dong):
                if muc["ho_ten"] not in [k["ho_ten"] for k in ket_qua]:
                    ket_qua.append(muc)
        elif con.tag.endswith("}p"):
            doan = Paragraph(con, tai_lieu).text
            ten = _chuan_hoa(doan)
            if giong_ho_ten(ten) and ten not in [k["ho_ten"] for k in ket_qua]:
                ket_qua.append({"ho_ten": ten, "ma_hs": ""})
    return ket_qua


def _tu_van_ban(du_lieu: bytes) -> list:
    for bang_ma in ("utf-8-sig", "utf-8", "cp1258"):
        try:
            chu = du_lieu.decode(bang_ma)
            break
        except UnicodeDecodeError:
            continue
    else:
        chu = du_lieu.decode("latin-1", errors="ignore")

    ket_qua = []
    for dong in chu.splitlines():
        # File CSV/TSV: chọn ô giống họ tên nhất trong dòng
        o = re.split(r"[,;\t]", dong)
        ten = next((x for x in o if giong_ho_ten(x)), "")
        ten = _chuan_hoa(ten)
        if ten and ten not in [k["ho_ten"] for k in ket_qua]:
            ket_qua.append({"ho_ten": ten, "ma_hs": ""})
    return ket_qua


def doc_danh_sach(ten_tep: str, du_lieu: bytes) -> list:
    """Đọc file và trả về danh sách học sinh; file lạ thì đọc như văn bản."""
    ten = (ten_tep or "").lower()
    if ten.endswith((".xlsx", ".xlsm", ".xls")):
        return _tu_excel(du_lieu)
    if ten.endswith(".docx"):
        return _tu_word(du_lieu)
    return _tu_van_ban(du_lieu)


def tao_file_mau() -> bytes:
    """File Excel mẫu để Thầy điền danh sách."""
    import pandas as pd

    khung = pd.DataFrame({
        "STT": [1, 2],
        "Họ và tên": ["Nguyễn Văn An", "Trần Thị Bình"],
        "Mã HS": ["HS01", "HS02"],
    })
    bo_dem = io.BytesIO()
    with pd.ExcelWriter(bo_dem, engine="openpyxl") as ghi:
        khung.to_excel(ghi, index=False, sheet_name="Danh sách")
    return bo_dem.getvalue()
