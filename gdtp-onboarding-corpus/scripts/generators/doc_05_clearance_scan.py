"""DOC-05 security clearance letter: image-only (scanned) PDF, 2 pages.

Fonts: Bitstream Vera shipped inside reportlab (so rendering does not depend on system fonts).
Fallback if it is missing: Arial from the Windows fonts folder, then DejaVuSans, then Pillow's default.
"""
from __future__ import annotations

import io
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .common import (SUBJECT, PEOPLE, SYN, SEED, short, long, corpus_path, eval_path)

W, H = 1240, 1754  # A4 at 150 dpi
MARGIN = 120


def _font_paths():
    import reportlab
    base = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    return [(os.path.join(base, "Vera.ttf"), os.path.join(base, "VeraBd.ttf")),
            ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
            ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")]


def load_fonts(size: int):
    for reg, bold in _font_paths():
        try:
            return ImageFont.truetype(reg, size), ImageFont.truetype(bold, size)
        except OSError:
            continue
    f = ImageFont.load_default()
    return f, f


def wrap(text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if font.getlength(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def page1_content():
    s = SUBJECT
    return {
        "date": long("2026-10-22").split(" ", 1)[1],
        "addressee": ["Mr Michael Byrne", "Programme Office, Garda Digital Transformation Programme", "Dublin"],
        "subject": f"Re: Security clearance decision â€“ {s['name']}",
        "intro": ["Dear Mr Byrne,",
                  "Following completion of the personnel security review for the individual named below, "
                  "I am pleased to confirm the outcome of the clearance decision."],
        "fields": [("Name", s["name"]), ("DOB", s["dob"]),
                   ("Clearance reference", s["clearance_ref"]),
                   ("Clearance level", s["clearance_level"]), ("Status", "APPROVED"),
                   ("Valid for", "5 years from date of issue (22 Oct 2026)")],
        "closing": ["This clearance remains valid provided the holder's circumstances do not change. "
                    "Any material change must be reported to this office without delay.",
                    "Yours sincerely,"],
        "signoff": [PEOPLE["nso_director"]["name"], PEOPLE["nso_director"]["title"],
                    "National Security Office (Synthetic)"],
    }


PAGE2_TITLE = "Reviewer notes (RESTRICTED â€“ Security Lead only)"
PAGE2_BODY = ["Case file: Sour, Julie - Programme Access clearance.",
              "Recommend routine re-review of travel declarations at 12 months. No adverse findings."]


def _digit_mask(ch, font, box):
    m = Image.new("L", box, 0)
    ImageDraw.Draw(m).text((0, 0), ch, font=font, fill=255)
    return np.asarray(m, dtype=np.float32) / 255.0


def render_pages():
    """Return (page_images, ground_truth_text, ref_region_info)."""
    reg, bold = load_fonts(30)
    big_reg, big_bold = load_fonts(44)
    small, _ = load_fonts(22)
    rng = random.Random(SEED)
    c = page1_content()
    gt = []

    # ------------------------------------------------------------ page 1
    img = Image.new("RGB", (W, H), (250, 249, 245))
    dr = ImageDraw.Draw(img)
    y = 90
    dr.text((MARGIN, y), "NATIONAL SECURITY OFFICE (SYNTHETIC)", font=big_bold, fill=(25, 30, 60))
    gt.append("NATIONAL SECURITY OFFICE (SYNTHETIC)")
    y += 62
    dr.text((MARGIN, y), "Personnel Security Clearance Unit", font=reg, fill=(60, 60, 70))
    gt.append("Personnel Security Clearance Unit")
    y += 48
    dr.line([(MARGIN, y), (W - MARGIN, y)], fill=(25, 30, 60), width=3)
    y += 50
    dr.text((W - MARGIN - reg.getlength(c["date"]), y), c["date"], font=reg, fill=(20, 20, 20))
    gt.append(c["date"])
    y += 70
    for ln in c["addressee"]:
        dr.text((MARGIN, y), ln, font=reg, fill=(20, 20, 20))
        gt.append(ln)
        y += 42
    y += 30
    dr.text((MARGIN, y), c["subject"], font=bold, fill=(20, 20, 20))
    gt.append(c["subject"])
    y += 70
    for para in c["intro"]:
        for ln in wrap(para, reg, W - 2 * MARGIN):
            dr.text((MARGIN, y), ln, font=reg, fill=(20, 20, 20))
            gt.append(ln)
            y += 42
        y += 18
    y += 10
    ref_info = None
    for label, value in c["fields"]:
        lab = f"{label}:"
        dr.text((MARGIN + 20, y), lab, font=bold, fill=(20, 20, 20))
        vx = MARGIN + 20 + 395
        if label == "Clearance reference":
            prefix, last = value[:-1], value[-1]
            dr.text((vx, y), prefix, font=reg, fill=(20, 20, 20))
            lx = vx + reg.getlength(prefix)
            box = (int(reg.getlength("8")) + 16, 54)
            m3 = _digit_mask("3", reg, box)
            m8 = _digit_mask("8", reg, box)
            ink = np.maximum(m3, 0.55 * m8)  # an 8 whose left-hand strokes are faint: reads 3 or 8
            region = np.asarray(img, dtype=np.float32)
            x0, y0 = int(lx), y
            sub = region[y0:y0 + box[1], x0:x0 + box[0]]
            ink3 = ink[:sub.shape[0], :sub.shape[1], None]
            sub[:] = sub * (1 - ink3) + np.array([20, 20, 20], dtype=np.float32) * ink3
            img = Image.fromarray(np.clip(region, 0, 255).astype(np.uint8))
            dr = ImageDraw.Draw(img)
            ref_info = {"prefix_box": (int(vx) - 6, y - 8, int(lx) - 4, y + 52),
                        "tail_box": (int(lx) - 4, y - 8, int(lx) + box[0] + 10, y + 52)}
            gt.append(f"{lab} {value}   [true ref NSO-CL-2026-0173; final digit deliberately ambiguous in the scan]")
        else:
            dr.text((vx, y), value, font=bold if label == "Status" else reg, fill=(20, 20, 20))
            gt.append(f"{lab} {value}")
        y += 52
    y += 24
    for para in c["closing"]:
        for ln in wrap(para, reg, W - 2 * MARGIN):
            dr.text((MARGIN, y), ln, font=reg, fill=(20, 20, 20))
            gt.append(ln)
            y += 42
        y += 14
    sig_y = y + 20
    # signature scribble
    pts = []
    for i in range(34):
        x = MARGIN + 10 + i * 8.5
        yy = sig_y + 28 + 22 * np.sin(i * 0.9) * (1 - i / 50) + rng.uniform(-5, 5)
        pts.append((x, yy))
    dr.line(pts, fill=(25, 35, 120), width=3, joint="curve")
    dr.line([(MARGIN, sig_y + 62), (MARGIN + 330, sig_y + 52)], fill=(25, 35, 120), width=2)
    y = sig_y + 90
    for ln in c["signoff"]:
        dr.text((MARGIN, y), ln, font=reg if ln != c["signoff"][0] else bold, fill=(20, 20, 20))
        gt.append(ln)
        y += 40
    dr.text((MARGIN, H - 80), SYN, font=small, fill=(80, 80, 80))
    gt.append(SYN)
    img = _stamp(img, rng)
    p1 = img

    # ------------------------------------------------------------ page 2
    gt.append("---- page 2 ----")
    img2 = Image.new("RGB", (W, H), (250, 249, 245))
    d2 = ImageDraw.Draw(img2)
    d2.text((MARGIN, 90), "NATIONAL SECURITY OFFICE (SYNTHETIC)", font=big_bold, fill=(25, 30, 60))
    d2.line([(MARGIN, 160), (W - MARGIN, 160)], fill=(25, 30, 60), width=3)
    d2.text((MARGIN, 200), PAGE2_TITLE, font=bold, fill=(150, 20, 20))
    gt.append("NATIONAL SECURITY OFFICE (SYNTHETIC)")
    gt.append(PAGE2_TITLE)
    y = 290
    for para in PAGE2_BODY:
        for ln in wrap(para, reg, W - 2 * MARGIN):
            d2.text((MARGIN, y), ln, font=reg, fill=(20, 20, 20))
            gt.append(ln)
            y += 42
        y += 18
    d2.text((MARGIN, H - 80), SYN, font=small, fill=(80, 80, 80))
    gt.append(SYN)
    img2 = _stamp(img2, rng, y=H - 330)
    return [p1, img2], gt, ref_info


def _stamp(img, rng, y=None):
    font, bold = load_fonts(34)
    layer = Image.new("RGBA", (520, 120), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((4, 4, 515, 115), radius=14, outline=(160, 30, 40, 200), width=5)
    ld.text((30, 38), SYN, font=bold, fill=(160, 30, 40, 200))
    layer = layer.rotate(9, expand=True, resample=Image.BICUBIC)
    base = img.convert("RGBA")
    base.alpha_composite(layer, (W - MARGIN - layer.width + 20, (y if y else H - 520)))
    return base.convert("RGB")


def degrade(img, ref_info, rng_np, page_index):
    if page_index == 0 and ref_info:
        # extra local blur over the clearance reference so the final digit is ambiguous
        for key, radius in (("prefix_box", 1.0), ("tail_box", 1.7)):
            box = ref_info[key]
            crop = img.crop(box).filter(ImageFilter.GaussianBlur(radius))
            img.paste(crop, box[:2])
    img = img.rotate(1.2, resample=Image.BICUBIC, fillcolor=(236, 235, 230))
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    arr = np.asarray(img, dtype=np.float32)
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    fold = 1 - 0.07 * np.exp(-((yy - H / 3) / 22.0) ** 2) - 0.03 * (yy / H)
    arr = arr * fold
    arr = 128 + (arr - 128) * 0.88 + 6
    arr = arr + rng_np.normal(0, 6.0, arr.shape)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=55, optimize=False, progressive=False, subsampling=2)
    return buf.getvalue()


def generate():
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    random.seed(SEED)
    np.random.seed(SEED)
    rng_np = np.random.default_rng(SEED)
    pages, gt, ref_info = render_pages()
    jpgs = [degrade(p, ref_info, rng_np, i) for i, p in enumerate(pages)]

    path = corpus_path("05_security_clearance_letter_scan.pdf")
    cv = canvas.Canvas(str(path), pagesize=(595.2756, 841.8898), invariant=1, pageCompression=1)
    cv.setTitle("Scanned document")
    cv.setAuthor("Scanner")
    for jb in jpgs:
        cv.drawImage(ImageReader(io.BytesIO(jb)), 0, 0, width=595.2756, height=841.8898)
        cv.showPage()
    cv.save()

    header = ("OCR GROUND TRUTH for corpus/05_security_clearance_letter_scan.pdf\n"
              "(evaluation only - must not be indexed or shown to the agent)\n"
              f"True clearance reference: {SUBJECT['clearance_ref']} (ends 0173).\n"
              "The final digit is deliberately blurred in the scan so OCR may read 0173 or 0178.\n"
              f"Every page carries the footer/stamp: {SYN}\n"
              "==========================================\n--- page 1 ---\n")
    eval_path("ocr_ground_truth_05.txt").write_text(header + "\n".join(gt) + "\n", encoding="utf-8",
                                                    newline="\n")
