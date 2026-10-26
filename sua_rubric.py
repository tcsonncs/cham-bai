# -*- coding: utf-8 -*-
"""Rà soát và sửa rubric trên app: từng câu, từng bước, không phải sửa JSON.

Lý do có màn này: rubric do AI lập từ biểu điểm có thể tự thêm việc mà đề
không hỏi (ví dụ ghi "tính góc B" trong khi đề chỉ hỏi AH). Thầy cần đọc lại
và sửa từng bước trước khi chấm cả lớp.
"""
import copy
import json
import re
import uuid

import streamlit as st

LOAI = {"trac_nghiem": "Trắc nghiệm", "dung_sai": "Đúng/Sai",
        "tra_loi_ngan": "Trả lời ngắn", "tu_luan": "Tự luận"}

# Cụm từ cho thấy bước bị khoá vào một cách làm
CACH_LAM = ("sử dụng", "dùng", "áp dụng", "vận dụng", "theo tỉ số", "nhờ")

# "… và kết luận", "… và trả lời" là cách nói tự nhiên, không phải gộp hai việc
DUOI_KET = ("kết luận", "trả lời", "ghi kết quả", "nêu đáp số", "so sánh",
            "đối chiếu", "kết thúc", "trình bày")


def _gop_hai_viec(mo_ta: str) -> bool:
    """Bước có gộp hai việc thật không (bỏ qua 'và kết luận')."""
    for phan in re.split(r"\bvà\b", mo_ta, flags=re.I)[1:]:
        duoi = phan.strip().lower()
        if duoi and not duoi.startswith(DUOI_KET):
            return True
    return False


def _id() -> str:
    return uuid.uuid4().hex[:8]


def kiem_tra(rubric: dict) -> list:
    """Soi rubric tìm chỗ dễ chấm sai; trả về danh sách lời nhắc."""
    nhac = []
    tong_bai = 0.0
    for cau in rubric.get("cau") or []:
        ma = cau.get("ma") or "?"
        diem_cau = float(cau.get("diem") or 0)
        tong_bai += diem_cau
        if cau.get("loai") != "tu_luan":
            continue
        buoc = cau.get("buoc") or []
        tong_buoc = sum(float(b.get("diem") or 0) for b in buoc)
        if abs(tong_buoc - diem_cau) > 1e-9:
            nhac.append(f"**{ma}**: cộng các bước được {tong_buoc:g} điểm, "
                        f"khác điểm của câu ({diem_cau:g}).")
        for b in buoc:
            mo_ta = (b.get("mo_ta") or "").strip()
            if not mo_ta:
                nhac.append(f"**{ma}**: có bước chưa ghi nội dung.")
            if _gop_hai_viec(mo_ta):
                nhac.append(f"**{ma}** — bước “{mo_ta}” gộp hai việc bằng chữ "
                            "“và”; nên tách thành hai bước hoặc chỉ ghi kết quả "
                            "mà đề hỏi.")
            if mo_ta.lower().startswith(CACH_LAM):
                nhac.append(f"**{ma}** — bước “{mo_ta}” khoá vào một cách làm; "
                            "nên viết thành kết quả cần đạt, ví dụ “Tính đúng "
                            "…” để học sinh làm cách khác vẫn được điểm.")
    tong = rubric.get("tong_diem")
    if tong is not None and abs(float(tong) - tong_bai) > 1e-9:
        nhac.append(f"**Toàn bài**: cộng điểm các câu là {tong_bai:g}, khác "
                    f"tổng ghi trong rubric ({float(tong):g}).")
    return nhac


def _chuan_bi(ban: dict) -> dict:
    """Gắn mã tạm cho từng câu/bước để thanh sửa không lẫn khi thêm bớt."""
    ban = copy.deepcopy(ban)
    for cau in ban.get("cau") or []:
        cau.setdefault("_id", _id())
        for b in cau.get("buoc") or []:
            b.setdefault("_id", _id())
    return ban


def _sach(ban: dict) -> dict:
    """Bỏ mã tạm trước khi lưu."""
    ban = copy.deepcopy(ban)
    for cau in ban.get("cau") or []:
        cau.pop("_id", None)
        for b in cau.get("buoc") or []:
            b.pop("_id", None)
    return ban


def _bang_cau(ban: dict) -> None:
    dong = []
    for cau in ban.get("cau") or []:
        dong.append(f"| {cau.get('ma')} | {cau.get('ten') or ''} | "
                    f"{LOAI.get(cau.get('loai'), cau.get('loai'))} | "
                    f"{cau.get('diem')} |")
    st.markdown("| Mã | Tên | Loại | Điểm |\n|---|---|---|---|\n" + "\n".join(dong))


def giao_dien(rubric: dict, khoa: str, nhan_nut: str = "💾 Lưu rubric"):
    """Hiện rubric cho rà soát và sửa. Trả về rubric mới nếu bấm nút lưu."""
    # Bản đang sửa chỉ dựng lại khi rubric bên ngoài đổi (lập lại bằng AI,
    # hoặc vừa lưu xong) — không dựng lại sau mỗi lần bấm nút.
    van_tay = json.dumps(rubric, ensure_ascii=False, sort_keys=True)
    if st.session_state.get(khoa + "_goc") != van_tay or khoa not in st.session_state:
        st.session_state[khoa] = _chuan_bi(rubric)
        st.session_state[khoa + "_goc"] = van_tay
    ban = st.session_state[khoa]

    tong = sum(float(c.get("diem") or 0) for c in ban.get("cau") or [])
    st.caption(f"{len(ban.get('cau') or [])} câu — tổng {tong:g} điểm")
    _bang_cau(ban)

    for i, cau in enumerate(ban.get("cau") or []):
        loai = LOAI.get(cau.get("loai"), cau.get("loai") or "")
        tieu_de = f"{cau.get('ma')} — {cau.get('ten') or ''} ({loai}, " \
                  f"{cau.get('diem')} điểm)"
        with st.expander(tieu_de):
            cau["diem"] = st.number_input(
                "Điểm của câu", min_value=0.0, step=0.25,
                value=float(cau.get("diem") or 0.0),
                key=f"{khoa}|{cau['_id']}|diem")

            if cau.get("loai") == "trac_nghiem":
                cau["dap_an"] = st.text_input(
                    "Đáp án đúng (A, B, C hoặc D)",
                    value=str(cau.get("dap_an") or ""),
                    key=f"{khoa}|{cau['_id']}|da")

            elif cau.get("loai") == "tra_loi_ngan":
                cau["dap_an"] = st.text_input(
                    "Đáp án đúng", value=str(cau.get("dap_an") or ""),
                    key=f"{khoa}|{cau['_id']}|da")

            elif cau.get("loai") == "dung_sai":
                dap_an = dict(cau.get("dap_an") or {})
                for y in ("a", "b", "c", "d"):
                    dap_an[y] = st.selectbox(
                        f"Ý {y}", ["Đ", "S"],
                        index=0 if str(dap_an.get(y, "Đ")).upper().startswith("Đ")
                        else 1,
                        key=f"{khoa}|{cau['_id']}|y{y}")
                cau["dap_an"] = dap_an
                st.caption("Cách tính điểm từng ý: "
                           + json.dumps(cau.get("quy_tac") or [],
                                        ensure_ascii=False))

            if cau.get("loai") == "tu_luan":
                buoc = cau.setdefault("buoc", [])
                st.write("**Các bước chấm** — mỗi bước nên là một kết quả.")
                for j, b in enumerate(buoc):
                    cot1, cot2, cot3 = st.columns([6, 2, 1])
                    b["mo_ta"] = cot1.text_input(
                        f"Bước {j + 1}", value=b.get("mo_ta") or "",
                        key=f"{khoa}|{b['_id']}|mo_ta",
                        label_visibility="collapsed")
                    b["diem"] = cot2.number_input(
                        f"Điểm bước {j + 1}", min_value=0.0, step=0.25,
                        value=float(b.get("diem") or 0.0),
                        key=f"{khoa}|{b['_id']}|diem",
                        label_visibility="collapsed")
                    if cot3.button("🗑", key=f"{khoa}|{b['_id']}|xoa",
                                   help="Bỏ bước này"):
                        buoc.pop(j)
                        st.rerun()
                cot_a, cot_b = st.columns(2)
                if cot_a.button("➕ Thêm bước", key=f"{khoa}|{cau['_id']}|them"):
                    buoc.append({"mo_ta": "", "diem": 0.25, "_id": _id()})
                    st.rerun()
                tong_buoc = sum(float(b.get("diem") or 0) for b in buoc)
                cot_b.caption(f"Cộng {tong_buoc:g} / {cau['diem']:g} điểm câu")

    # Soi lại sau khi đã áp các thay đổi vừa nhập
    nhac = kiem_tra(ban)
    if nhac:
        with st.expander(f"⚠️ {len(nhac)} chỗ nên xem lại", expanded=True):
            for n in nhac:
                st.write("• " + n)
    else:
        st.success("Không thấy chỗ nào đáng ngờ trong rubric.")

    if st.button(nhan_nut, type="primary"):
        moi = _sach(ban)
        st.session_state[khoa + "_goc"] = json.dumps(moi, ensure_ascii=False,
                                                     sort_keys=True)
        return moi
    with st.expander("Xem JSON (dành cho việc khác)"):
        st.code(json.dumps(_sach(ban), ensure_ascii=False, indent=1),
                language="json")
    return None
