import io

try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    _DOCX_OK = True
except ImportError:
    _DOCX_OK = False


def _set_cell_bg(cell, hex_color: str):
    """Jadval katakchasi fon rangini o'rnatish"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def _add_section_header(doc, text: str):
    """Ko'k fon bilan bo'lim sarlavhasi"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x1a, 0x56, 0x9e)
    # Pastki chiziq
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '1a569e')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def _add_field(doc, label: str, value: str, number: int = None):
    """Maydon: "N. Savol: Javob" ko'rinishida"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    prefix = f"{number}. " if number else ""
    label_run = p.add_run(f"{prefix}{label}: ")
    label_run.bold = True
    label_run.font.size = Pt(10)
    value_run = p.add_run(value or "—")
    value_run.font.size = Pt(10)
    return p


def _checkbox(checked: bool) -> str:
    return "☑" if checked else "☐"


def _add_checkbox_field(doc, number: int, label: str, value: bool):
    """Ha/Yo'q checkbox ko'rinishida"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    label_run = p.add_run(f"{number}. {label}")
    label_run.bold = True
    label_run.font.size = Pt(10)
    p.add_run("\n    ")
    ha_run = p.add_run(f"{_checkbox(value)} Ha    ")
    ha_run.font.size = Pt(10)
    yoq_run = p.add_run(f"{_checkbox(not value)} Yo'q")
    yoq_run.font.size = Pt(10)
    return p


def generate_ariza_docx(data: dict) -> io.BytesIO:
    """
    Ariza ma'lumotlaridan Word hujjat hosil qiladi.
    data — ArizaStates dan olingan dict.
    """
    if not _DOCX_OK:
        raise ImportError("python-docx o'rnatilmagan. Buyruq: pip install python-docx")

    doc = Document()

    # ─── Sahifa chegaralari ───
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2)

    # ─── Sarlavha ───
    title = doc.add_heading('', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_t = title.add_run("OLIM FONDI")
    run_t.font.size = Pt(16)
    run_t.font.color.rgb = RGBColor(0x1a, 0x56, 0x9e)
    run_t.bold = True

    sub_title = doc.add_paragraph()
    sub_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    st_run = sub_title.add_run("MA'LUMOTNOMA")
    st_run.font.size = Pt(13)
    st_run.bold = True

    year_p = doc.add_paragraph()
    year_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    year_run = year_p.add_run("2026/2027 o'quv yili uchun ariza")
    year_run.font.size = Pt(10)
    year_run.italic = True
    year_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_paragraph()

    # ════════════════════════════════
    # 1-BO'LIM: SHAXSIY MA'LUMOTLAR
    # ════════════════════════════════
    _add_section_header(doc, "Shaxsiy ma'lumotlar")

    _add_field(doc, "Talabaning F.I.SH.", data.get('fish', ''), 1)
    _add_field(doc, "Tug'ilgan sanasi (kun.oy.yil)", data.get('tugilgan_sana', ''), 2)
    _add_field(doc, "Millati", data.get('millat', ''), 3)
    _add_field(doc, "Manzilingiz (doimiy ro'yxatga olingan)", data.get('manzil', ''), 4)
    _add_field(doc, "Telefon raqamingiz", data.get('telefon', ''), 5)
    _add_field(doc, "Email manzilingiz", data.get('email', ''), 6)

    # ════════════════════════════════
    # 2-BO'LIM: TA'LIM
    # ════════════════════════════════
    _add_section_header(doc, "Ta'lim haqida ma'lumot")

    _add_field(doc, "Qaysi oliy ta'lim muassasasida o'qiyapsiz", data.get('otm', ''), 7)

    # 8. Ta'lim shakli — checkbox
    shakl = data.get('talim_shakli', 'Kunduzgi')
    p8 = doc.add_paragraph()
    p8.paragraph_format.space_before = Pt(2)
    p8.paragraph_format.space_after = Pt(2)
    r_label = p8.add_run("8. Ta'lim shaklingiz:")
    r_label.bold = True
    r_label.font.size = Pt(10)
    p8.add_run("\n    ")
    p8.add_run(f"{_checkbox(shakl == 'Kunduzgi')} Kunduzgi    ").font.size = Pt(10)
    p8.add_run(f"{_checkbox(shakl == 'Sirtqi')} Sirtqi    ").font.size = Pt(10)
    p8.add_run(f"{_checkbox(shakl == 'Masofaviy')} Masofaviy").font.size = Pt(10)

    _add_field(doc, "Ta'lim yo'nalishi (mutaxassislik)", data.get('yonalish', ''), 9)
    _add_field(doc, "2026/2027 o'quv yilidagi kurs / bosqich", data.get('kurs', ''), 10)

    _add_checkbox_field(doc, 11, "Ilmiy tadqiqotlar bilan shug'ullanasizmi?", data.get('ilmiy_tadqiqot', False))
    if data.get('ilmiy_tadqiqot') and data.get('tadqiqot_info'):
        p_info = doc.add_paragraph()
        p_info.paragraph_format.left_indent = Cm(1)
        p_info.paragraph_format.space_before = Pt(1)
        r = p_info.add_run(f"Tadqiqot yo'nalishi: {data['tadqiqot_info']}")
        r.font.size = Pt(10)
        r.italic = True

    _add_checkbox_field(doc, 13, "O'tkazilgan ilmiy konferensiya, seminar yoki tanlovlarda ishtirok etganmisiz?",
                        data.get('konferensiya', False))
    _add_checkbox_field(doc, 14, "Sizda ilmiy maqola yoki nashrlar bormi?", data.get('maqola', False))

    # ════════════════════════════════
    # 3-BO'LIM: MOLIYA
    # ════════════════════════════════
    _add_section_header(doc, "Moliya va qo'llab-quvvatlash")

    _add_checkbox_field(doc, 15, "Oldin Olim fondidan yoki boshqa grantlardan foydalanganmisiz?",
                        data.get('oldin_grant', False))
    if data.get('oldin_grant') and data.get('grant_info'):
        p_grant = doc.add_paragraph()
        p_grant.paragraph_format.left_indent = Cm(1)
        p_grant.paragraph_format.space_before = Pt(1)
        r = p_grant.add_run(f"Grant ma'lumoti: {data['grant_info']}")
        r.font.size = Pt(10)
        r.italic = True

    _add_field(doc, "Agar 'Ha', qaysi grant va qachon", data.get('grant_info') or "—", 16)
    _add_field(doc, "Kontrakt summangiz (stipendiyasiz hisoblanganda)", data.get('kontrakt_sum', ''), 17)

    # ════════════════════════════════
    # 4-BO'LIM: OILA
    # ════════════════════════════════
    _add_section_header(doc, "Oila a'zolari haqida to'liq ma'lumot")

    _add_field(doc, "Oilangiz necha kishidan iborat", data.get('oila_soni', ''), 18)
    _add_field(doc, "Otasi haqida ma'lumot (F.I.Sh. | Ish joyi | Lavozim | Tug'ilgan sana)",
               data.get('ota_info', ''), 19)
    _add_field(doc, "Onasi haqida ma'lumot (F.I.Sh. | Ish joyi | Lavozim | Tug'ilgan sana)",
               data.get('ona_info', ''), 20)
    _add_field(doc, "Aka/uka/opa/singil haqida ma'lumot (F.I.Sh. | Ish joyi | Kurs | Shakl | Shartnoma | Tug'ilgan sana)",
               data.get('aka_opa_info', ''), 21)

    # ════════════════════════════════
    # 5-BO'LIM: MOTIVATSION XAT
    # ════════════════════════════════
    _add_section_header(doc, "Motivatsion xat")

    p_prompt = doc.add_paragraph()
    r_prompt = p_prompt.add_run(
        "Motivatsion xat quyidagi savollarga javob berishi kerak: "
        "yaqin kelajak rejalari; oliy ma'lumotning foydasi; fond yordami; "
        "o'zini munosib deb hisoblash sababi; stipendiya g'olibi bo'lish argumentlari."
    )
    r_prompt.font.size = Pt(9)
    r_prompt.italic = True
    r_prompt.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    p_mot = doc.add_paragraph()
    p_mot.paragraph_format.space_before = Pt(4)
    r_mot = p_mot.add_run(data.get('motivatsion_xat', ''))
    r_mot.font.size = Pt(10)

    # ─── Imzo qatori ───
    doc.add_paragraph()
    p_sign = doc.add_paragraph()
    p_sign.paragraph_format.space_before = Pt(12)
    sign_run = p_sign.add_run("Ariza beruvchi: ____________________        Sana: _______________")
    sign_run.font.size = Pt(10)

    # ─── Bufer ───
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
