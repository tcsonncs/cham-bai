# -*- coding: utf-8 -*-
"""Xuất kết quả ra Excel."""
import io

import pandas as pd

import luu_tru


def tao_file_excel(dot: dict, hoc_sinh: list) -> bytes:
    """Bảng điểm cả đợt và chi tiết từng câu, dạng .xlsx."""
    dong_tong = []
    dong_cau = []
    for hs in hoc_sinh:
        bai = luu_tru.lay_bai(dot["id"], hs["id"])
        if not bai:
            continue
        bai = luu_tru.doc_bai_day_du(bai)
        ket_qua = bai.get("ket_qua") or {}
        dong_tong.append({
            "Mã HS": hs.get("ma_hs") or "",
            "Họ tên": hs["ho_ten"],
            "Điểm máy gợi ý": ket_qua.get("tong_goi_y"),
            "Điểm chốt": ket_qua.get("tong_chot", bai.get("tong_chot")),
            "Số câu nghi vấn": sum(1 for c in ket_qua.get("cau", [])
                                   if c.get("nghi_van")),
            "Trạng thái": bai.get("trang_thai"),
            "Ngày chấm": bai.get("ngay_cham"),
        })
        for cau in ket_qua.get("cau", []):
            dong_cau.append({
                "Họ tên": hs["ho_ten"],
                "Câu": cau.get("ma") or cau.get("ten"),
                "Điểm tối đa": cau.get("diem_toi_da"),
                "Điểm gợi ý": cau.get("diem_goi_y"),
                "Điểm chốt": cau.get("diem_chot"),
                "Nghi vấn": "Có" if cau.get("nghi_van") else "",
                "Lý do": cau.get("ly_do_nghi_van", ""),
                "Nhận xét": cau.get("nhan_xet", ""),
            })

    bo_dem = io.BytesIO()
    with pd.ExcelWriter(bo_dem, engine="openpyxl") as ghi:
        pd.DataFrame(dong_tong).to_excel(ghi, sheet_name="Tổng hợp", index=False)
        pd.DataFrame(dong_cau).to_excel(ghi, sheet_name="Chi tiết câu", index=False)
    return bo_dem.getvalue()
