# -*- coding: utf-8 -*-
"""Chấm bài: trắc nghiệm chấm bằng quy tắc, tự luận chấm bằng Gemini."""
import json
import re

from cau_hinh import goi_gemini, parse_json

PROMPT_RUBRIC = """Dưới đây là đề kiểm tra môn Toán và phần đáp án/biểu điểm của giáo viên
(có thể là văn bản bóc từ file Word, trình bày chưa đẹp).

Hãy chuyển thành rubric JSON để máy chấm bài. Quy ước:
- "trac_nghiem": câu chọn một trong A, B, C, D. Ghi "dap_an" là một chữ cái.
- "dung_sai": câu chọn Đúng/Sai cho từng ý a, b, c, d. Ghi "dap_an" là một
  đối tượng {"a": "Đ", "b": "S", ...} và "quy_tac" là cách tính điểm theo số ý
  đúng, ví dụ [{"so_y_dung": 4, "diem": 1.0}, ...] đúng như biểu điểm.
- "tra_loi_ngan": câu trả lời ngắn. Ghi "dap_an" là chuỗi đáp án đúng.
- "tu_luan": câu tự luận. Chia thành các "buoc", mỗi bước có "mo_ta" và "diem".
  Tổng điểm các bước phải bằng điểm của câu.
  Viết "mo_ta" thành KẾT QUẢ cần đạt ("Tính đúng độ dài AH"), không khoá vào
  một cách làm ("Dùng sin tính AH"); không đòi bước trung gian mà đề không
  hỏi. Mỗi bước chỉ nêu MỘT kết quả: nếu đáp án gộp hai việc bằng chữ "và"
  (ví dụ "tính góc B và tính AH") thì tách thành hai bước, hoặc chỉ ghi kết
  quả mà đề bài thực sự hỏi. Không tự thêm việc mà đề không yêu cầu.
- Điểm mỗi câu đặt ở "diem". Tổng các câu ghi ở "tong_diem".
- "so_cau" là số thứ tự câu trên đề (1, 2, 3, ...), dùng để khớp với dấu bút
  học sinh đánh trên tờ đề. Câu tự luận không cần "so_cau".

Chỉ trả về JSON đúng định dạng sau, không thêm chữ nào ngoài JSON:
{"tong_diem": 10.0, "ghi_chu": "",
 "cau": [
   {"ma": "I.1", "so_cau": 1, "ten": "Câu 1", "loai": "trac_nghiem",
    "diem": 0.25, "dap_an": "A"},
   {"ma": "II.11", "so_cau": 11, "ten": "Câu 11", "loai": "dung_sai",
    "diem": 1.0, "dap_an": {"a": "Đ", "b": "S", "c": "S", "d": "Đ"},
    "quy_tac": [{"so_y_dung": 4, "diem": 1.0}, {"so_y_dung": 3, "diem": 0.5},
                {"so_y_dung": 2, "diem": 0.25}, {"so_y_dung": 1, "diem": 0.1}]},
   {"ma": "III.12", "so_cau": 12, "ten": "Câu 12", "loai": "tra_loi_ngan",
    "diem": 0.5, "dap_an": "8"},
   {"ma": "TL1a", "ten": "Tự luận 1a", "loai": "tu_luan", "diem": 1.0,
    "buoc": [{"mo_ta": "Đưa về phương trình tích", "diem": 0.5},
             {"mo_ta": "Tìm đúng nghiệm", "diem": 0.5}]}
 ]}

ĐỀ VÀ BIỂU ĐIỂM:
<<NOI_DUNG>>
"""

PROMPT_CHAM = """Bạn chấm phần tự luận bài kiểm tra môn Toán của học sinh Việt Nam.

RUBRIC (chỉ gồm câu tự luận):
<<RUBRIC>>

BÀI LÀM CỦA HỌC SINH (bóc từ ảnh chụp, có thể có lỗi đọc):
<<BAI_LAM>>

NHỮNG CHỖ ĐỌC KHÔNG CHẮC CHẮN:
<<CHO_KHONG_RO>>

Quy tắc chấm:
- Chấm từng bước theo đúng rubric. Điểm mỗi bước phải là bội số của 0,25 và
  không vượt quá điểm tối đa của bước đó.
- Học sinh làm cách khác đáp án nhưng vẫn đúng toán thì cho điểm bình thường.
- Chấm theo KẾT QUẢ của bước, không chấm theo cách làm. Học sinh đạt kết quả
  bằng bất kỳ cách đúng nào (tỉ số lượng giác, định lí Pythagore, hệ thức
  lượng trong tam giác vuông, diện tích tam giác, tam giác đồng dạng…) đều
  được điểm. Không trừ vì thiếu một bước trung gian có trong đáp án mà đề
  không bắt buộc, và không trừ vì học sinh không làm một việc mà đề không hỏi.
- Nếu "mo_ta" của bước gộp hai việc bằng chữ "và": cho điểm khi học sinh làm
  đúng và ra kết quả; chỉ trừ khi đề bắt buộc cả hai việc. Ghi rõ trong
  "nhan_xet" lý do trừ để giáo viên kiểm tra lại.
- Nếu không thấy bài làm của một câu: cho 0 điểm và đặt "nghi_van": true.
- Đặt "nghi_van": true khi: chữ đọc không chắc ảnh hưởng đến điểm; học sinh ra
  kết quả khác đáp án nhưng cách làm gần đúng; hoặc không chắc có nên cho điểm.
- "nhan_xet" viết ngắn, cụ thể, chỉ rõ đúng chỗ nào, sai chỗ nào, bằng tiếng Việt.
- "do_tin_cay" từ 0 đến 1.

Chỉ trả về JSON đúng định dạng sau, không thêm chữ nào ngoài JSON:
{"cau": [{"ma": "TL1a", "buoc": [{"mo_ta": "", "diem_toi_da": 0.5,
  "diem": 0.5, "nhan_xet": ""}], "diem": 1.0, "nhan_xet": "",
  "do_tin_cay": 0.9, "nghi_van": false, "ly_do_nghi_van": ""}],
 "nhan_xet_chung": ""}
"""


def _lam_tron(diem: float) -> float:
    """Làm tròn về bội số 0,25 gần nhất."""
    return round(round(float(diem) / 0.25) * 0.25, 2)


def tao_rubric(noi_dung_de: str) -> dict:
    """Nhờ AI chuyển đề + biểu điểm thành rubric JSON."""
    return parse_json(goi_gemini(PROMPT_RUBRIC.replace("<<NOI_DUNG>>", noi_dung_de)))


SO = re.compile(r"-?\d+(?:[.,]\d+)?")


def so_khop(tra_loi: str, dap_an: str) -> bool:
    """So câu trả lời ngắn với đáp án.

    Đáp án là số thì so các con số xuất hiện trong câu trả lời, chịu được kiểu
    viết "Có 8 số" hay "x = 8". Đáp án là chữ thì so chuỗi đã chuẩn hoá.
    """
    tra_loi = (tra_loi or "").strip()
    dap_an = (dap_an or "").strip()
    if not tra_loi or not dap_an:
        return False

    def chuan(s):
        return re.sub(r"\s+", "", s).replace(",", ".").lower()

    so_dap_an = SO.findall(dap_an)
    if so_dap_an and re.fullmatch(r"-?\d+(?:[.,]\d+)?", chuan(dap_an)):
        so_tra_loi = [x.replace(",", ".") for x in SO.findall(tra_loi)]
        mong_doi = {x.replace(",", ".") for x in so_dap_an}
        if not mong_doi:
            return False
        if mong_doi == set(so_tra_loi):
            return True
        # Chấp nhận khi học sinh viết đáp án trước rồi giải thích thêm:
        # "8 (vì 0;1;...;7)" — số đầu tiên trùng đáp án.
        return (len(mong_doi) == 1 and bool(so_tra_loi)
                and so_tra_loi[0] in mong_doi)
    return chuan(dap_an) in chuan(tra_loi)


def _tim_dau_but(marks: dict, so_cau) -> dict:
    for item in marks.get("trac_nghiem") or []:
        if str(item.get("cau")) == str(so_cau):
            return item
    return {}


def cham_trac_nghiem(rubric: dict, marks: dict) -> list:
    """Chấm phần chọn A/B/C/D bằng quy tắc, không gọi AI."""
    ket_qua = []
    for cau in rubric.get("cau") or []:
        if cau.get("loai") != "trac_nghiem":
            continue
        so_cau = cau.get("so_cau")
        dap_an = str(cau.get("dap_an") or "").strip().upper()
        dau = _tim_dau_but(marks, so_cau)
        chon = [str(x).strip().upper() for x in (dau.get("chon") or [])]
        toi_da = float(cau.get("diem") or 0)

        nghi_van = False
        ly_do = ""
        if not chon:
            diem = 0.0
            nghi_van = True
            ly_do = "Không thấy dấu chọn đáp án"
        elif len(chon) > 1:
            diem = 0.0
            nghi_van = True
            ly_do = f"Có {len(chon)} dấu chọn: {', '.join(chon)}"
        else:
            diem = toi_da if chon[0] == dap_an else 0.0
        if not dau.get("chac", True):
            nghi_van = True
            ly_do = (ly_do + " " if ly_do else "") + "AI không chắc khi đọc dấu bút"
        # Có dấu gạch bỏ thì việc chọn đáp án nào là của Thầy, máy không tự quyết.
        dau_hieu = str(dau.get("dau_hieu") or "").lower()
        if any(tu in dau_hieu for tu in ("gạch", "xoá", "xóa", "bỏ", "tẩy")):
            nghi_van = True
            ly_do = ((ly_do + " ") if ly_do else "") + (
                "Có dấu gạch bỏ trên đề; kiểm tra lại học sinh chọn đáp án nào")

        ket_qua.append({
            "ma": cau.get("ma"), "loai": "trac_nghiem", "ten": cau.get("ten"),
            "diem_toi_da": toi_da, "diem_goi_y": diem, "diem_chot": diem,
            "chon": chon, "dap_an": dap_an,
            "nhan_xet": "", "nghi_van": nghi_van, "ly_do_nghi_van": ly_do,
            "buoc": [],
        })
    return ket_qua


def cham_dung_sai(rubric: dict, marks: dict) -> list:
    """Chấm câu đúng/sai nhiều ý theo bảng quy tắc của biểu điểm."""
    ket_qua = []
    for cau in rubric.get("cau") or []:
        if cau.get("loai") != "dung_sai":
            continue
        dap_an = cau.get("dap_an") or {}
        so_cau = cau.get("so_cau")
        cua_cau = [x for x in marks.get("dung_sai") or []
                   if x.get("cau") is None or str(x.get("cau")) == str(so_cau)]
        da_chon = {str(x.get("y")): str(x.get("chon") or "").strip().upper()
                   for x in cua_cau}
        so_dung = 0
        chi_tiet = []
        for y, dung in dap_an.items():
            chon = da_chon.get(str(y), "")
            ok = chon[:1] == str(dung).strip().upper()[:1]
            so_dung += 1 if ok else 0
            chi_tiet.append({"y": y, "chon": chon, "dap_an": dung, "dung": ok})

        quy_tac = cau.get("quy_tac") or []
        diem = 0.0
        for muc in quy_tac:
            if int(muc.get("so_y_dung", -1)) == so_dung:
                diem = float(muc.get("diem") or 0)
                break
        toi_da = float(cau.get("diem") or 0)
        thieu = any(not ct["chon"] for ct in chi_tiet)
        ket_qua.append({
            "ma": cau.get("ma"), "loai": "dung_sai", "ten": cau.get("ten"),
            "diem_toi_da": toi_da, "diem_goi_y": min(diem, toi_da),
            "diem_chot": min(diem, toi_da),
            "so_y_dung": so_dung, "chi_tiet": chi_tiet,
            "nhan_xet": "", "nghi_van": thieu,
            "ly_do_nghi_van": "Không đọc được một số ý" if thieu else "",
            "buoc": [],
        })
    return ket_qua


def cham_tra_loi_ngan(rubric: dict, marks: dict) -> list:
    """Chấm câu trả lời ngắn bằng so khớp chuỗi đã chuẩn hoá."""
    ket_qua = []
    nguon = marks.get("tra_loi_ngan") or []
    if isinstance(nguon, dict):  # dữ liệu cũ lưu theo dạng từ điển
        nguon = [{"cau": k, "tra_loi": v} for k, v in nguon.items()]
    for cau in rubric.get("cau") or []:
        if cau.get("loai") != "tra_loi_ngan":
            continue
        so_cau = cau.get("so_cau")
        tra_loi = ""
        for muc in nguon:
            if str(muc.get("cau")) == str(so_cau):
                tra_loi = str(muc.get("tra_loi") or "")
                break
        dap_an = str(cau.get("dap_an") or "")
        ok = so_khop(tra_loi, dap_an)
        toi_da = float(cau.get("diem") or 0)
        ket_qua.append({
            "ma": cau.get("ma"), "loai": "tra_loi_ngan", "ten": cau.get("ten"),
            "diem_toi_da": toi_da, "diem_goi_y": toi_da if ok else 0.0,
            "diem_chot": toi_da if ok else 0.0,
            "tra_loi": tra_loi, "dap_an": dap_an,
            "nhan_xet": "", "nghi_van": not tra_loi,
            "ly_do_nghi_van": "Không thấy câu trả lời" if not tra_loi else "",
            "buoc": [],
        })
    return ket_qua


def cham_tu_luan(rubric: dict, bai_lam: str, cho_khong_ro) -> dict:
    """Gọi Gemini chấm các câu tự luận."""
    cau_tu_luan = [c for c in (rubric.get("cau") or [])
                   if c.get("loai") == "tu_luan"]
    if not cau_tu_luan:
        return {"cau": [], "nhan_xet_chung": ""}
    prompt = (PROMPT_CHAM
              .replace("<<RUBRIC>>", json.dumps({"cau": cau_tu_luan},
                                                ensure_ascii=False, indent=1))
              .replace("<<BAI_LAM>>", bai_lam or "")
              .replace("<<CHO_KHONG_RO>>",
                       json.dumps(cho_khong_ro or [], ensure_ascii=False)))
    ket_qua = parse_json(goi_gemini(prompt, nhiet_do=0.2))
    _kiem_tra_diem(ket_qua, cau_tu_luan)
    return ket_qua


def _kiem_tra_diem(ket_qua: dict, cau_tu_luan: list) -> None:
    """Chặn điểm lẻ ngoài bội số 0,25 và điểm vượt trần; gắn cờ khi phải sửa."""
    toi_da_theo_ma = {c.get("ma"): float(c.get("diem") or 0) for c in cau_tu_luan}
    for cau in ket_qua.get("cau") or []:
        toi_da = toi_da_theo_ma.get(cau.get("ma"), 0.0)
        tong_buoc = 0.0
        for buoc in cau.get("buoc") or []:
            goc = float(buoc.get("diem") or 0)
            chuan = min(_lam_tron(goc), float(buoc.get("diem_toi_da") or toi_da))
            if abs(chuan - goc) > 1e-9:
                cau["nghi_van"] = True
                cau["ly_do_nghi_van"] = (
                    (cau.get("ly_do_nghi_van") or "")
                    + f" Điểm bước '{buoc.get('mo_ta', '')[:40]}' đã làm tròn từ {goc}."
                ).strip()
            buoc["diem"] = chuan
            tong_buoc += chuan
        diem = _lam_tron(cau.get("diem") if cau.get("diem") is not None
                         else tong_buoc)
        if abs(diem - tong_buoc) > 1e-9:
            cau["nghi_van"] = True
            cau["ly_do_nghi_van"] = (
                (cau.get("ly_do_nghi_van") or "")
                + f" Tổng điểm các bước là {tong_buoc}, lệch với điểm câu."
            ).strip()
            diem = tong_buoc
        if diem > toi_da:
            cau["nghi_van"] = True
            cau["ly_do_nghi_van"] = (
                (cau.get("ly_do_nghi_van") or "")
                + f" Điểm {diem} vượt quá điểm tối đa {toi_da}."
            ).strip()
            diem = toi_da
        cau["diem"] = diem
        cau["diem_goi_y"] = diem
        cau["diem_chot"] = diem
        cau["diem_toi_da"] = toi_da
        cau.setdefault("loai", "tu_luan")


def cham_ca_bai(rubric: dict, ket_qua_doc: dict) -> dict:
    """Ghép bốn phần chấm thành kết quả một bài."""
    marks = {
        "trac_nghiem": ket_qua_doc.get("trac_nghiem") or [],
        "dung_sai": ket_qua_doc.get("dung_sai") or [],
        "tra_loi_ngan": ket_qua_doc.get("tra_loi_ngan") or {},
    }
    bai_lam = ket_qua_doc.get("text_chot")
    if not bai_lam:
        bai_lam = "\n\n".join(
            f"--- Trang {i} ---\n{(trang.get('noi_dung') or '').strip()}"
            for i, trang in enumerate(ket_qua_doc.get("trang") or [], 1)
        )
    cho_khong_ro = []
    for trang in ket_qua_doc.get("trang") or []:
        cho_khong_ro.extend(trang.get("cho_khong_ro") or [])

    cau = (cham_trac_nghiem(rubric, marks)
           + cham_dung_sai(rubric, marks)
           + cham_tra_loi_ngan(rubric, marks))
    tu_luan = cham_tu_luan(rubric, bai_lam, cho_khong_ro)
    cau.extend(tu_luan.get("cau") or [])

    thu_tu = {c.get("ma"): i for i, c in enumerate(rubric.get("cau") or [])}
    cau.sort(key=lambda c: thu_tu.get(c.get("ma"), 999))
    return {
        "cau": cau,
        "nhan_xet_chung": tu_luan.get("nhan_xet_chung", ""),
        "tong_goi_y": round(sum(float(c.get("diem_goi_y") or 0) for c in cau), 2),
        "tong_chot": round(sum(float(c.get("diem_chot") or 0) for c in cau), 2),
    }
