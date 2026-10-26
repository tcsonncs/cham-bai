# -*- coding: utf-8 -*-
"""Lưu trữ bằng SQLite trên máy.

Cấu trúc đủ để chuyển sang Google Sheets sau: mỗi bảng là một danh sách
bản ghi phẳng, các trường phức tạp lưu bằng JSON.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from cau_hinh import DB_FILE, chuan_bi_thu_muc

SCHEMA = """
CREATE TABLE IF NOT EXISTS dot_cham (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL,
    lop TEXT,
    cap_hoc TEXT,
    ngay_tao TEXT,
    de_bai TEXT,
    dap_an TEXT,
    rubric TEXT
);
CREATE TABLE IF NOT EXISTS hoc_sinh (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dot_id INTEGER NOT NULL,
    ho_ten TEXT NOT NULL,
    ma_hs TEXT
);
CREATE TABLE IF NOT EXISTS bai_lam (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dot_id INTEGER NOT NULL,
    hs_id INTEGER NOT NULL,
    anh TEXT,
    text_doc TEXT,
    text_chot TEXT,
    trac_nghiem TEXT,
    ket_qua TEXT,
    tong_goi_y REAL,
    tong_chot REAL,
    trang_thai TEXT,
    ngay_tao TEXT,
    ngay_cham TEXT
);
"""


def ket_noi():
    chuan_bi_thu_muc()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _json(gia_tri):
    if gia_tri is None:
        return None
    if isinstance(gia_tri, str):
        return gia_tri
    return json.dumps(gia_tri, ensure_ascii=False)


def _doc_json(chuoi):
    if not chuoi:
        return None
    try:
        return json.loads(chuoi)
    except (TypeError, json.JSONDecodeError):
        return chuoi


# ---------- đợt chấm ----------

def tao_dot(ten: str, lop: str, cap_hoc: str) -> int:
    with ket_noi() as conn:
        cur = conn.execute(
            "INSERT INTO dot_cham (ten, lop, cap_hoc, ngay_tao) VALUES (?,?,?,?)",
            (ten, lop, cap_hoc, datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def danh_sach_dot():
    with ket_noi() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM dot_cham ORDER BY id DESC")]


def lay_dot(dot_id: int):
    with ket_noi() as conn:
        r = conn.execute("SELECT * FROM dot_cham WHERE id=?", (dot_id,)).fetchone()
        return dict(r) if r else None


def cap_nhat_dot(dot_id: int, **truong) -> None:
    if not truong:
        return
    cot = ", ".join(f"{k}=?" for k in truong)
    with ket_noi() as conn:
        conn.execute(f"UPDATE dot_cham SET {cot} WHERE id=?",
                     (*truong.values(), dot_id))


# ---------- học sinh ----------

def them_hoc_sinh(dot_id: int, ho_ten: str, ma_hs: str = "") -> int:
    with ket_noi() as conn:
        cur = conn.execute(
            "INSERT INTO hoc_sinh (dot_id, ho_ten, ma_hs) VALUES (?,?,?)",
            (dot_id, ho_ten.strip(), ma_hs.strip()),
        )
        return cur.lastrowid


def danh_sach_hoc_sinh(dot_id: int):
    with ket_noi() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM hoc_sinh WHERE dot_id=? ORDER BY ho_ten", (dot_id,))]


def xoa_hoc_sinh(hs_id: int) -> None:
    with ket_noi() as conn:
        conn.execute("DELETE FROM bai_lam WHERE hs_id=?", (hs_id,))
        conn.execute("DELETE FROM hoc_sinh WHERE id=?", (hs_id,))


# ---------- bài làm ----------

def lay_bai(dot_id: int, hs_id: int):
    with ket_noi() as conn:
        r = conn.execute(
            "SELECT * FROM bai_lam WHERE dot_id=? AND hs_id=? ORDER BY id DESC LIMIT 1",
            (dot_id, hs_id),
        ).fetchone()
        return dict(r) if r else None


def luu_anh_bai(dot_id: int, hs_id: int, danh_sach_anh) -> int:
    """Ghi danh sách ảnh cho bài; tạo mới nếu chưa có."""
    bai = lay_bai(dot_id, hs_id)
    now = datetime.now().isoformat(timespec="seconds")
    with ket_noi() as conn:
        if bai:
            conn.execute("UPDATE bai_lam SET anh=? WHERE id=?",
                         (_json(danh_sach_anh), bai["id"]))
            return bai["id"]
        cur = conn.execute(
            "INSERT INTO bai_lam (dot_id, hs_id, anh, trang_thai, ngay_tao)"
            " VALUES (?,?,?,?,?)",
            (dot_id, hs_id, _json(danh_sach_anh), "moi_tao", now),
        )
        return cur.lastrowid


def cap_nhat_bai(bai_id: int, **truong) -> None:
    if not truong:
        return
    du_lieu = {}
    for k, v in truong.items():
        du_lieu[k] = _json(v) if k in {"anh", "text_doc", "text_chot",
                                       "trac_nghiem", "ket_qua"} else v
    cot = ", ".join(f"{k}=?" for k in du_lieu)
    with ket_noi() as conn:
        conn.execute(f"UPDATE bai_lam SET {cot} WHERE id=?",
                     (*du_lieu.values(), bai_id))


def doc_bai_day_du(bai: dict) -> dict:
    """Chuyển các trường JSON của bản ghi thành dữ liệu dùng được."""
    ket_qua = dict(bai)
    for k in ("anh", "text_doc", "text_chot", "trac_nghiem", "ket_qua"):
        if k in ket_qua:
            ket_qua[k] = _doc_json(ket_qua[k])
    return ket_qua


def lay_anh(bai: dict):
    """Lấy danh sách đường dẫn ảnh còn tồn tại trên ổ đĩa.

    Trên máy chủ mây, ảnh mất sau khi khởi động lại, nên phải lọc bỏ đường dẫn
    không còn tệp.
    """
    ds = _doc_json(bai.get("anh")) or []
    duong_dan = [a["duong_dan"] if isinstance(a, dict) else a for a in ds]
    return [p for p in duong_dan if p and Path(p).exists()]


def luu_file_anh(dot_id: int, hs_id: int, ten: str, du_lieu: bytes) -> str:
    import uuid

    thu_muc = Path(DB_FILE).parent / "anh" / str(dot_id) / str(hs_id)
    thu_muc.mkdir(parents=True, exist_ok=True)
    duoi = Path(ten).suffix.lower() or ".jpg"
    tep = thu_muc / f"{uuid.uuid4().hex}{duoi}"
    tep.write_bytes(du_lieu)
    return str(tep)


def _co_sheets() -> bool:
    """Secrets của Streamlit đã khai báo kho Google Sheets chưa."""
    try:
        import streamlit as st

        return bool(st.secrets.get("SHEETS_URL")) and bool(
            st.secrets.get("SHEETS_TOKEN"))
    except Exception:  # noqa: BLE001
        return False


if _co_sheets():
    # Chạy trên mây: thay các hàm đọc/ghi đĩa bằng bản ghi Google Sheets.
    # Các hàm thuần (doc_bai_day_du, lay_anh, luu_file_anh) giữ nguyên.
    import luu_tru_sheets as _kho_may

    for _ten_ham in (
        "tao_dot", "danh_sach_dot", "lay_dot", "cap_nhat_dot",
        "them_hoc_sinh", "danh_sach_hoc_sinh", "xoa_hoc_sinh",
        "lay_bai", "luu_anh_bai", "cap_nhat_bai",
    ):
        globals()[_ten_ham] = getattr(_kho_may, _ten_ham)
