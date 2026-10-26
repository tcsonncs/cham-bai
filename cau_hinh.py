# -*- coding: utf-8 -*-
"""Cấu hình chung: khoá API, mô hình, thư mục dữ liệu, gọi Gemini."""
import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENV_FILE = BASE / ".env"
DATA_DIR = BASE / "du_lieu"
ANH_DIR = DATA_DIR / "anh"
DB_FILE = DATA_DIR / "cham_bai.db"

MODELS = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"]


def doc_khoa() -> str:
    """Đọc khoá API: ưu tiên secrets của Streamlit Cloud, rồi biến môi trường, rồi .env."""
    try:
        import streamlit as st

        if "GEMINI_API_KEY" in st.secrets:
            return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:  # noqa: BLE001
        pass
    khoa = os.environ.get("GEMINI_API_KEY", "").strip()
    if not khoa and ENV_FILE.exists():
        for dong in ENV_FILE.read_text(encoding="utf-8").splitlines():
            dong = dong.strip()
            if not dong or dong.startswith("#") or "=" not in dong:
                continue
            ten, gia_tri = dong.split("=", 1)
            if ten.strip() == "GEMINI_API_KEY":
                khoa = gia_tri.strip().strip('"').strip("'")
                break
    return khoa


def lay_client():
    """Tạo client Gemini. Ném lỗi rõ ràng nếu thiếu khoá."""
    from google import genai

    khoa = doc_khoa()
    if not khoa:
        raise RuntimeError(
            "Chưa có GEMINI_API_KEY. Đặt trong .env hoặc secrets của Streamlit."
        )
    return genai.Client(api_key=khoa)


def parse_json(text: str) -> dict:
    """Bóc JSON khỏi phản hồi, chịu được khối ```json ... ```."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    dau, cuoi = text.find("{"), text.rfind("}")
    if dau == -1 or cuoi == -1:
        raise ValueError("Phản hồi không có JSON")
    return json.loads(text[dau : cuoi + 1])


def goi_gemini(parts, nhiet_do: float = 0.1, so_lan: int = 3) -> str:
    """Gọi Gemini, tự đổi mô hình nếu mô hình đầu không dùng được."""
    from google.genai import types

    client = lay_client()
    cau_hinh = types.GenerateContentConfig(temperature=nhiet_do)
    loi_cuoi = None
    for ten_mo_hinh in MODELS:
        for lan in range(so_lan):
            try:
                resp = client.models.generate_content(
                    model=ten_mo_hinh, contents=parts, config=cau_hinh
                )
                return resp.text
            except Exception as exc:  # noqa: BLE001
                loi_cuoi = exc
                thong_bao = str(exc).lower()
                if "404" in thong_bao or "not found" in thong_bao:
                    break  # mô hình không tồn tại, thử mô hình sau
                if lan < so_lan - 1:
                    time.sleep(5 * (lan + 1))
    raise RuntimeError(f"Không gọi được Gemini: {loi_cuoi}")


def chuan_bi_thu_muc() -> None:
    ANH_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print("Có khoá API:", bool(doc_khoa()))
    print("Thư mục dữ liệu:", DATA_DIR)
    sys.exit(0)
