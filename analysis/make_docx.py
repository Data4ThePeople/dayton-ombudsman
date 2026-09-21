"""Build the review Word document straight from POST.md, so the two cannot drift.

Run:  .venv/bin/python analysis/make_docx.py
Out:  posts/<slug>/dayton-ombudsman-child-care-REVIEW.docx
"""
import os
import re

import docx
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.join(HERE, "..", "posts", "dayton-ombudsman-child-care")
OUT = os.path.join(POST, "dayton-ombudsman-child-care-REVIEW.docx")

INK = RGBColor(0x14, 0x18, 0x1C)
MUTED = RGBColor(0x5A, 0x64, 0x6C)
LINK = "1F5D96"
FLAG = RGBColor(0x8A, 0x55, 0x10)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

ASKS = [
    ("The founding.", "We say the office opened in 1971 and was one of the first cities in "
     "the country to do it. We took out an earlier line calling it the second oldest behind "
     "Seattle, because Jamestown, New York and Seattle both appear to predate it. If your "
     "office has a specific claim it stands behind, tell us and we will use it."),
    ("What the child care calls are about.", "We describe them as people trying to work out "
     "how to qualify for state subsidies, not complaints about a provider. That came from "
     "what you told us."),
    ("The description of Job and Family Services.", "We say the county agency was likely "
     "overwhelmed with calls and that your office absorbs the overflow. That is Eric's "
     "reconstruction, and it is labeled as such, but we do not want to put words in your mouth."),
    ("The numbers in the chart.", "Child care is 18.2 percent of the cases your office "
     "investigated in the first half of 2026, up from 1.9 percent in 2020. We used your "
     "published monthly totals as the denominator and treated any withheld count as unknown "
     "rather than zero."),
]


def hyperlink(par, url, text):
    r_id = par.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    col = OxmlElement("w:color"); col.set(qn("w:val"), LINK); rPr.append(col)
    und = OxmlElement("w:u"); und.set(qn("w:val"), "single"); rPr.append(und)
    run.append(rPr)
    t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve")
    run.append(t)
    link.append(run)
    par._p.append(link)


def rich(par, text, size=11, color=INK, italic=False, bold=False):
    """Write text into a paragraph, turning [label](url) into real hyperlinks."""
    pos = 0
    for m in LINK_RE.finditer(text):
        if m.start() > pos:
            r = par.add_run(text[pos:m.start()])
            r.font.size, r.font.color.rgb, r.italic, r.bold = Pt(size), color, italic, bold
        hyperlink(par, m.group(2), m.group(1))
        pos = m.end()
    if pos < len(text):
        r = par.add_run(text[pos:])
        r.font.size, r.font.color.rgb, r.italic, r.bold = Pt(size), color, italic, bold


def rule(doc, color="C3CCD2", space_after=14):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    pPr = p._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", color)):
        bottom.set(qn(k), v)
    borders.append(bottom)
    pPr.append(borders)
    return p


def body_paragraph(doc, text, size=11.5, color=INK, italic=False, after=10, before=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.line_spacing = 1.22
    rich(p, text, size=size, color=color, italic=italic)
    return p


def load_post():
    raw = open(os.path.join(POST, "POST.md"), encoding="utf-8").read()
    _, fm, body = raw.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body.strip()


def main():
    meta, body = load_post()
    doc = Document()

    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for m in ("left_margin", "right_margin"):
        setattr(sec, m, Inches(1))
    sec.top_margin, sec.bottom_margin = Inches(0.9), Inches(0.9)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)

    # ---- review cover ----
    p = doc.add_paragraph()
    r = p.add_run("DRAFT FOR REVIEW  ·  NOT PUBLISHED")
    r.bold, r.font.size, r.font.color.rgb = True, Pt(9.5), FLAG
    p.paragraph_format.space_after = Pt(4)

    p = doc.add_paragraph()
    r = p.add_run("A draft about your office, sent for your review before anything goes live")
    r.bold, r.font.size, r.font.color.rgb = True, Pt(15), INK
    p.paragraph_format.space_after = Pt(8)

    body_paragraph(doc, "Nothing here has been published. It will go to our site as a private "
                        "draft, and it stays private until you have had your say. If something "
                        "is wrong, or reads unfairly, say so and it changes.",
                   size=11, color=MUTED, after=14)
    rule(doc)

    for label, value in [
        ("Written by", "Eric Pachman, Data 4 The People"),
        ("About", "The Dayton and Montgomery County Ombudsman Office, and what its records "
                  "show about child care"),
        ("Data used", "Your office's own records, January 1997 through June 2026, shared "
                      "with permission"),
        ("Status", "Text and chart are final pending your review. Search wording and the "
                   "publish date are still being set."),
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(label + ": ")
        r.bold, r.font.size, r.font.color.rgb = True, Pt(10), INK
        r = p.add_run(value)
        r.font.size, r.font.color.rgb = Pt(10), MUTED

    rule(doc, space_after=12)
    p = doc.add_paragraph()
    r = p.add_run("Four things we would most like you to check")
    r.bold, r.font.size, r.font.color.rgb = True, Pt(11), INK
    p.paragraph_format.space_after = Pt(8)

    for i, (head, text) in enumerate(ASKS, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.28)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.18
        r = p.add_run(f"{i}. {head} ")
        r.bold, r.font.size, r.font.color.rgb = True, Pt(10.5), INK
        r = p.add_run(text)
        r.font.size, r.font.color.rgb = Pt(10.5), MUTED

    body_paragraph(doc, "You can mark up this document directly, or reply to Eric however you "
                        "normally would.", size=10, color=MUTED, after=0, before=8)

    doc.add_paragraph().add_run().add_break(docx.enum.text.WD_BREAK.PAGE)

    # ---- the article ----
    doc.add_picture(os.path.join(POST, meta["hero"]), width=Inches(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    r = p.add_run(meta["title"])
    r.bold, r.font.size, r.font.color.rgb = True, Pt(22), INK
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(14), Pt(6)

    body_paragraph(doc, meta["subtitle"], size=12.5, color=MUTED, after=6)
    p = doc.add_paragraph()
    r = p.add_run("Eric Pachman  ·  Data 4 Thought")
    r.font.size, r.font.color.rgb, r.bold = Pt(9), MUTED, True
    rule(doc, space_after=12)

    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("# "):
            i += 1
            continue
        if line.startswith("::: divider"):
            rule(doc, space_after=16)
        elif line.startswith("!["):
            m = re.match(r"!\[(.*)\]\((.+)\)", line)
            doc.add_picture(os.path.join(POST, m.group(2)), width=Inches(6.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.paragraphs[-1].paragraph_format.space_before = Pt(10)
        elif line.startswith("*") and line.endswith("*") and not line.startswith("**"):
            body_paragraph(doc, line.strip("*"), size=9.5, color=MUTED, italic=True, after=14)
        elif line.startswith("## "):
            p = doc.add_paragraph()
            r = p.add_run(line[3:])
            r.bold, r.font.size, r.font.color.rgb = True, Pt(15), INK
            p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(6), Pt(8)
        elif line.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.line_spacing = 1.15
            rich(p, line[2:], size=10.5, color=INK)
        else:
            body_paragraph(doc, line)
        i += 1

    rule(doc, space_after=6)
    body_paragraph(doc, "Draft for review, not published. The hero is a Journal Herald cartoon "
                        "photographed in the Ombudsman Office, used with permission.",
                   size=9, color=MUTED, after=0)

    doc.save(OUT)
    print("wrote", os.path.relpath(OUT, os.path.join(HERE, "..")))
    print(f"  {len(doc.paragraphs)} paragraphs, {len(doc.inline_shapes)} images")


if __name__ == "__main__":
    main()
