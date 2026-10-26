# -*- coding: utf-8 -*-
"""Khối chụp nhiều trang bài làm liên tiếp rồi gửi về một lượt.

Thay cho ``st.camera_input``: khung xem của nó nhỏ cố định và mỗi lần chỉ
giữ được một ảnh, chụp trang mới là mất trang cũ. Khối này mở **camera gốc
của điện thoại** (toàn màn hình, có nút Chụp lại / Dùng ảnh) qua ô chọn tệp
có thuộc tính ``capture``; ảnh xếp thành dãy, bấm ✕ để bỏ trang nhầm, cuối
cùng bấm *Lưu … trang vào bài* để gửi tất cả một lần.

Giao diện nằm ở ``components/may_anh/index.html`` (tự viết theo giao thức
component của Streamlit, không cần npm).
"""
import base64
from pathlib import Path

import streamlit.components.v1 as components

_THU_MUC = Path(__file__).parent / "components" / "may_anh"
_o_chup = components.declare_component("may_anh", path=str(_THU_MUC))


def o_chup(ten_hoc_sinh: str, so_trang: int, lan_xoa: int, key: str):
    """Hiện khối chụp ảnh. Trả về None hoặc {"ma", "anh": [{"ten", "data"}]}.

    ``key`` cũng được gửi sang trang để dùng làm khoá giữ tạm ảnh chưa gửi
    (điện thoại khoá màn hình rồi mở lại thì ảnh đang chờ vẫn còn).
    """
    return _o_chup(
        ten_hoc_sinh=ten_hoc_sinh,
        so_trang=int(so_trang),
        lan_xoa=int(lan_xoa),
        khoa_luu=key,
        default=None,
        key=key,
    )


def giai_du_lieu_anh(muc: dict) -> bytes:
    """Chuỗi ``data:image/jpeg;base64,…`` thành bytes; chuỗi hỏng trả về b''."""
    du_lieu = (muc or {}).get("data") or ""
    if not du_lieu:
        return b""
    if du_lieu.startswith("data:") and "," in du_lieu:
        du_lieu = du_lieu.split(",", 1)[1]
    try:
        return base64.b64decode(du_lieu)
    except (ValueError, TypeError):
        return b""
