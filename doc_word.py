# -*- coding: utf-8 -*-
"""Bóc chữ từ file Word, giữ lại công thức toán.

Thư viện `python-docx` chỉ lấy chữ, nên công thức soạn bằng Equation (OMML)
bị bỏ trắng: đề đọc ra thành "A.    B.    C." mất hết biểu thức. Ở đây duyệt
thẳng XML của đoạn văn theo đúng thứ tự, gặp `m:oMath` thì chuyển sang LaTeX
và bọc trong $...$ để vừa đọc được vừa hiện đúng khi xem trên app.
"""
import re
from io import BytesIO

from docx import Document
from docx.oxml.ns import qn

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"

# Ký hiệu Unicode trong công thức → LaTeX
KY_HIEU = {
    "−": "-", "·": r"\cdot ", "⋅": r"\cdot ",
    "×": r"\times ", "÷": r"\div ",
    "≤": r"\le ", "≥": r"\ge ", "≠": r"\ne ", "≈": r"\approx ",
    "∈": r"\in ", "∉": r"\notin ", "⊂": r"\subset ",
    "∪": r"\cup ", "∩": r"\cap ", "∅": r"\varnothing ",
    "∞": r"\infty ", "π": r"\pi ", "α": r"\alpha ",
    "β": r"\beta ", "γ": r"\gamma ", "θ": r"\theta ",
    "Δ": r"\Delta ", "∆": r"\Delta ",
    "°": r"^{\circ}", "∘": r"\circ ", "±": r"\pm ",
    "∓": r"\mp ",
    "→": r"\to ", "⇒": r"\Rightarrow ", "⇔": r"\Leftrightarrow ",
    "∀": r"\forall ", "∃": r"\exists ", "⊥": r"\perp ",
    "∥": r"\parallel ", "∠": r"\angle ", "△": r"\triangle ",
    "⋆": "*", "…": r"\ldots ", "∑": r"\sum ", "∫": r"\int ",
    "¬": r"\neg ", "∧": r"\land ", "∨": r"\lor ",
    "²": "^{2}", "³": "^{3}", "¹": "^{1}",
}
for _i, _c in enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹"):
    KY_HIEU[_c] = "^{%d}" % _i
for _i, _c in enumerate("₀₁₂₃₄₅₆₇₈₉"):
    KY_HIEU[_c] = "_{%d}" % _i

DAU_ACC = {"̂": r"\hat", "̃": r"\tilde", "̄": r"\bar",
           "⃗": r"\vec", "̇": r"\dot", "̈": r"\ddot"}


def _ten(el) -> str:
    """Tên thẻ không kèm namespace ('r', 'oMath', ...)."""
    return el.tag.split("}")[-1] if isinstance(el.tag, str) else ""


def _chu(text: str) -> str:
    """Đổi ký hiệu Unicode trong công thức sang LaTeX."""
    return "".join(KY_HIEU.get(c, c) for c in text)


def _con(el, ten: str):
    for c in el:
        if _ten(c) == ten:
            return c
    return None


def _con_truc_tiep(el, ten: str):
    return [c for c in el if _ten(c) == ten]


NGOAC_LATEX = {"{": r"\{", "}": r"\}", "|": r"|", "‖": r"\|",
               "⟨": r"\langle", "⟩": r"\rangle", "〈": r"\langle",
               "〉": r"\rangle", "[": "[", "]": "]", "(": "(", ")": ")",
               "": "."}


def _dau_ngoac(ch: str) -> str:
    """Dấu ngoặc của OMML thành lệnh LaTeX (rỗng thì thành dấu chấm)."""
    return NGOAC_LATEX.get(ch, ch)


def _boc(s: str) -> str:
    """Bọc ngoặc nhọn nếu cần."""
    s = (s or "").strip()
    if not s:
        return "{}"
    if len(s) == 1:
        return s
    if s.startswith("{") and s.endswith("}"):
        return s
    return "{" + s + "}"


def _chu_trong(el) -> str:
    """Chữ của một m:r (gồm nhiều m:t)."""
    return "".join(t.text or "" for t in el.iter() if _ten(t) == "t")


def _la_thang(el) -> bool:
    """m:r có kiểu chữ đứng (m:sty val='p') — thường là số, chữ La Mã, đơn vị."""
    for rpr in el:
        if _ten(rpr) != "rPr":
            continue
        for c in rpr:
            if _ten(c) == "sty" and (c.get(qn("m:val")) or "") == "p":
                return True
    return False


def to_latex(el) -> str:
    """Chuyển một phần tử OMML sang LaTeX (đệ quy)."""
    ten = _ten(el)

    if ten == "r":
        s = _chu(_chu_trong(el))
        # Kiểu chữ đứng chỉ áp cho chữ/số; dấu như = - ( ) để nguyên
        if _la_thang(el) and re.fullmatch(r"[A-Za-z0-9 ]+", s.strip() or " "):
            return r"\mathrm{%s}" % s.strip()
        return s

    if ten in ("oMath", "oMathPara", "e", "num", "den", "sub", "sup", "deg",
               "fName", "lim", "box", "borderBox", "phant", "groupChr", "ins"):
        return "".join(to_latex(c) for c in el)

    if ten == "t":
        return _chu(el.text or "")

    if ten == "sSup":
        return (_boc(to_latex(_con(el, "e") or el))
                + "^{" + (to_latex(_con(el, "sup") or el) or "").strip() + "}")

    if ten == "sSub":
        return (_boc(to_latex(_con(el, "e") or el))
                + "_{" + (to_latex(_con(el, "sub") or el) or "").strip() + "}")

    if ten == "sSubSup":
        return (_boc(to_latex(_con(el, "e") or el))
                + "_{" + (to_latex(_con(el, "sub") or el) or "").strip() + "}"
                + "^{" + (to_latex(_con(el, "sup") or el) or "").strip() + "}")

    if ten == "sPre":
        return ("{}_{" + (to_latex(_con(el, "sub") or el) or "").strip() + "}"
                + "^{" + (to_latex(_con(el, "sup") or el) or "").strip() + "}"
                + to_latex(_con(el, "e") or el))

    if ten == "f":
        kieu = ""
        fpr = _con(el, "fPr")
        if fpr is not None:
            for c in fpr:
                if _ten(c) == "type":
                    kieu = c.get(qn("m:val")) or ""
        tu = (to_latex(_con(el, "num") or el) or "").strip()
        mau = (to_latex(_con(el, "den") or el) or "").strip()
        if kieu == "lin":
            return "{" + tu + "}/{" + mau + "}"
        if kieu == "noBar":
            return r"\genfrac{}{}{0pt}{}{%s}{%s}" % (tu, mau)
        return r"\dfrac{%s}{%s}" % (tu, mau)

    if ten == "rad":
        deg = _con(el, "deg")
        bac = (to_latex(deg) if deg is not None else "").strip()
        than = (to_latex(_con(el, "e") or el) or "").strip()
        if bac:
            return r"\sqrt[%s]{%s}" % (bac, than)
        return r"\sqrt{%s}" % than

    if ten == "d":
        dau_mo, dau_dong, phan_cach = "(", ")", ","
        dpr = _con(el, "dPr")
        if dpr is not None:
            for c in dpr:
                if _ten(c) == "begChr":
                    dau_mo = c.get(qn("m:val")) or ""
                elif _ten(c) == "endChr":
                    dau_dong = c.get(qn("m:val")) or ""
                elif _ten(c) == "sepChr":
                    phan_cach = c.get(qn("m:val")) or ""
        phans = [(to_latex(c) or "").strip() for c in _con_truc_tiep(el, "e")]
        if phan_cach:
            tach = ", " if phan_cach == "," else " " + phan_cach + " "
            trong = tach.join(phans)
        else:
            trong = "".join(phans)
        return (r"\left" + _dau_ngoac(dau_mo) + trong
                + r"\right" + _dau_ngoac(dau_dong))

    if ten == "m":
        hang = []
        for mr in _con_truc_tiep(el, "mr"):
            o = " & ".join((to_latex(c) or "").strip()
                           for c in _con_truc_tiep(mr, "e"))
            hang.append(o)
        return r"\begin{matrix}" + r" \\ ".join(hang) + r"\end{matrix}"

    if ten == "nary":
        chr_ = "∫"
        npr = _con(el, "naryPr")
        if npr is not None:
            for c in npr:
                if _ten(c) == "chr" and c.get(qn("m:val")):
                    chr_ = c.get(qn("m:val"))
        ky = {"∑": r"\sum", "∏": r"\prod", "∫": r"\int",
              "∬": r"\iint", "∮": r"\oint"}.get(chr_, *_ky_tu(chr_))
        duoi = (to_latex(_con(el, "sub") or el) or "").strip()
        tren = (to_latex(_con(el, "sup") or el) or "").strip()
        than = (to_latex(_con(el, "e") or el) or "").strip()
        s = ky
        if duoi:
            s += "_{" + duoi + "}"
        if tren:
            s += "^{" + tren + "}"
        return s + " " + than

    if ten == "func":
        return ((to_latex(_con(el, "fName") or el) or "").strip()
                + _boc(to_latex(_con(el, "e") or el)))

    if ten in ("limLow", "limUpp"):
        than = (to_latex(_con(el, "e") or el) or "").strip()
        phu = (to_latex(_con(el, "lim") or el) or "").strip()
        dau = "_" if ten == "limLow" else "^"
        return than + dau + "{" + phu + "}"

    if ten == "bar":
        return r"\overline{%s}" % (to_latex(_con(el, "e") or el) or "").strip()

    if ten == "acc":
        dau = r"\hat"
        apr = _con(el, "accPr")
        if apr is not None:
            for c in apr:
                if _ten(c) == "chr":
                    dau = DAU_ACC.get(c.get(qn("m:val")) or "", r"\hat")
        return dau + "{" + (to_latex(_con(el, "e") or el) or "").strip() + "}"

    if ten == "eqArr":
        return r" \\ ".join((to_latex(c) or "").strip()
                            for c in _con_truc_tiep(el, "e"))

    # Phần tử lạ: bỏ qua phần định dạng, lấy chữ bên trong
    if ten in ("rPr", "ctrlPr", "fPr", "dPr", "naryPr", "radPr", "accPr",
               "barPr", "dPr", "sSupPr", "sSubPr", "sSubSupPr", "funcPr",
               "limLowPr", "limUppPr", "boxPr", "borderBoxPr", "phantPr",
               "groupChrPr", "eqArrPr", "argPr", "oMathParaPr", "sPrePr"):
        return ""
    return "".join(to_latex(c) for c in el)


def _ky_tu(ch: str):
    """Ký hiệu toán đứng riêng thành lệnh LaTeX (dùng cho nary)."""
    ten = KY_HIEU.get(ch)
    if ten and ten.startswith("\\"):
        return (ten.strip(),)
    return (ch,)


def _doan(p) -> str:
    """Một đoạn văn: chữ và công thức xen kẽ, giữ đúng thứ tự."""
    phan = []
    for con in p:
        ten = _ten(con)
        if ten == "r":
            for c in con:
                t = _ten(c)
                if t == "t":
                    phan.append(c.text or "")
                elif t == "tab":
                    phan.append("  ")
                elif t == "br":
                    phan.append("\n")
        elif ten in ("hyperlink", "smartTag", "ins", "sdt", "sdtContent"):
            # lấy chữ trong các w:r nằm bên trong
            for r in con:
                for c in r:
                    if _ten(c) == "t":
                        phan.append(c.text or "")
        elif ten in ("oMath", "oMathPara"):
            latex = (to_latex(con) or "").strip()
            if latex:
                boc = "$$" if ten == "oMathPara" else "$"
                phan.append(boc + latex + boc)
    return "".join(phan)


def docx_sang_van_ban(du_lieu: bytes) -> str:
    """Bóc toàn bộ đoạn văn và bảng của file .docx, giữ công thức dạng LaTeX."""
    tai_lieu = Document(BytesIO(du_lieu))
    dong = []

    def them_bang(bang):
        for hang in bang.rows:
            o = []
            for o_cot in hang.cells:
                o.append(" ".join(_doan(p._p).strip()
                                  for p in o_cot.paragraphs).strip())
            dong.append(" | ".join(o))

    def duyet(khoi):
        for el in khoi.element.body.iterchildren():
            ten = _ten(el)
            if ten == "p":
                dong.append(_doan(el).rstrip())
            elif ten == "tbl":
                from docx.table import Table

                them_bang(Table(el, khoi))

    duyet(tai_lieu)
    van_ban = "\n".join(dong)
    # Gộp dòng trống liên tiếp
    while "\n\n\n" in van_ban:
        van_ban = van_ban.replace("\n\n\n", "\n\n")
    return van_ban.strip()
