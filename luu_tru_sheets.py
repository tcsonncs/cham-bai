# -*- coding: utf-8 -*-
"""Lưu trữ trên Google Sheets qua một Apps Script Web App.

Cùng tên hàm với `luu_tru` để app không phải sửa. Chỉ dùng khi Secrets có
SHEETS_URL và SHEETS_TOKEN; nếu không, app dùng SQLite trên máy.

Cách làm: mỗi lần ghi thì gửi cả bảng (dữ liệu nhỏ, 3–10 học sinh), phía
Apps Script xoá và ghi lại. Nhờ vậy không cần xử lý từng dòng.
"""
import json
from datetime import datetime

import requests

CAC_BANG = ("dot_cham", "hoc_sinh", "bai_lam")


def co_cau_hinh() -> bool:
    """Kiểm tra Secrets đã có địa chỉ và mã của Apps Script chưa."""
    try:
        import streamlit as st

        return bool(st.secrets.get("SHEETS_URL")) and bool(
            st.secrets.get("SHEETS_TOKEN"))
    except Exception:  # noqa: BLE001
        return False


def _goi(action: str, **them):
    import streamlit as st

    url = st.secrets["SHEETS_URL"]
    goi = {"token": st.secrets["SHEETS_TOKEN"], "action": action, **them}
    resp = requests.post(url, json=goi, timeout=60)
    resp.raise_for_status()
    du_lieu = resp.json()
    if not du_lieu.get("ok"):
        raise RuntimeError(f"Kho Sheets báo lỗi: {du_lieu.get('loi')}")
    return du_lieu


def _du_lieu() -> dict:
    """Đọc toàn bộ kho một lần, giữ trong phiên làm việc."""
    import streamlit as st

    if "_sheets_cache" not in st.session_state:
        st.session_state["_sheets_cache"] = _goi("doc")["du_lieu"]
    return st.session_state["_sheets_cache"]


def _du_lieu_moi() -> dict:
    """Đọc lại từ Google Sheets trước khi sửa, tránh ghi đè dữ liệu máy khác."""
    import streamlit as st

    du_lieu = _goi("doc")["du_lieu"]
    try:
        st.session_state["_sheets_cache"] = du_lieu
    except Exception:  # noqa: BLE001
        pass
    return du_lieu


def _ghi(bang: str, dong: list) -> None:
    import streamlit as st

    _goi("ghi", sheet=bang, rows=dong)
    st.session_state["_sheets_cache"][bang] = dong


def lam_moi() -> None:
    """Bỏ bộ nhớ tạm, lần sau đọc lại từ Google Sheets."""
    import streamlit as st

    st.session_state.pop("_sheets_cache", None)


def _json(gia_tri):
    if gia_tri is None:
        return ""
    if isinstance(gia_tri, str):
        return gia_tri
    return json.dumps(gia_tri, ensure_ascii=False)


def _max_id(dong: list) -> int:
    return max([int(float(x.get("id") or 0)) for x in dong] or [0])


# ---------- đợt chấm ----------

def tao_dot(ten: str, lop: str, cap_hoc: str) -> int:
    dl = _du_lieu_moi()
    ds = dl["dot_cham"]
    moi = {
        "id": _max_id(ds) + 1, "ten": ten, "lop": lop, "cap_hoc": cap_hoc,
        "ngay_tao": datetime.now().isoformat(timespec="seconds"),
        "de_bai": "", "dap_an": "", "rubric": "",
    }
    ds.append(moi)
    _ghi("dot_cham", ds)
    return moi["id"]


def danh_sach_dot():
    return sorted(_du_lieu()["dot_cham"], key=lambda x: int(float(x["id"])),
                  reverse=True)


def lay_dot(dot_id: int):
    for d in _du_lieu()["dot_cham"]:
        if int(float(d["id"])) == int(dot_id):
            return dict(d)
    return None


def cap_nhat_dot(dot_id: int, **truong) -> None:
    dl = _du_lieu_moi()
    for d in dl["dot_cham"]:
        if int(float(d["id"])) == int(dot_id):
            d.update(truong)
            break
    _ghi("dot_cham", dl["dot_cham"])


# ---------- học sinh ----------

def them_hoc_sinh(dot_id: int, ho_ten: str, ma_hs: str = "") -> int:
    dl = _du_lieu_moi()
    ds = dl["hoc_sinh"]
    moi = {"id": _max_id(ds) + 1, "dot_id": int(dot_id),
           "ho_ten": ho_ten.strip(), "ma_hs": (ma_hs or "").strip()}
    ds.append(moi)
    _ghi("hoc_sinh", ds)
    return moi["id"]


def danh_sach_hoc_sinh(dot_id: int):
    ds = [d for d in _du_lieu()["hoc_sinh"]
          if int(float(d["dot_id"])) == int(dot_id)]
    return sorted(ds, key=lambda x: x["ho_ten"])


def xoa_hoc_sinh(hs_id: int) -> None:
    dl = _du_lieu_moi()
    dl["hoc_sinh"] = [d for d in dl["hoc_sinh"]
                      if int(float(d["id"])) != int(hs_id)]
    dl["bai_lam"] = [b for b in dl["bai_lam"]
                     if int(float(b["hs_id"])) != int(hs_id)]
    _ghi("hoc_sinh", dl["hoc_sinh"])
    _ghi("bai_lam", dl["bai_lam"])


# ---------- bài làm ----------

def lay_bai(dot_id: int, hs_id: int):
    ds = [b for b in _du_lieu()["bai_lam"]
          if int(float(b["dot_id"])) == int(dot_id)
          and int(float(b["hs_id"])) == int(hs_id)]
    return max(ds, key=lambda x: int(float(x["id"]))) if ds else None


def luu_anh_bai(dot_id: int, hs_id: int, danh_sach_anh) -> int:
    dl = _du_lieu_moi()
    bai = lay_bai(dot_id, hs_id)
    now = datetime.now().isoformat(timespec="seconds")
    if bai:
        bai["anh"] = _json(danh_sach_anh)
        _ghi("bai_lam", dl["bai_lam"])
        return int(float(bai["id"]))
    moi = {
        "id": _max_id(dl["bai_lam"]) + 1, "dot_id": int(dot_id),
        "hs_id": int(hs_id), "anh": _json(danh_sach_anh),
        "text_doc": "", "text_chot": "", "trac_nghiem": "", "ket_qua": "",
        "tong_goi_y": "", "tong_chot": "", "trang_thai": "moi_tao",
        "ngay_tao": now, "ngay_cham": "",
    }
    dl["bai_lam"].append(moi)
    _ghi("bai_lam", dl["bai_lam"])
    return moi["id"]


def cap_nhat_bai(bai_id: int, **truong) -> None:
    dl = _du_lieu_moi()
    for b in dl["bai_lam"]:
        if int(float(b["id"])) == int(bai_id):
            for k, v in truong.items():
                b[k] = _json(v) if k in {"anh", "text_doc", "text_chot",
                                         "trac_nghiem", "ket_qua"} else v
            break
    _ghi("bai_lam", dl["bai_lam"])

