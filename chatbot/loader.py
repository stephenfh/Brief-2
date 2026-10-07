"""Build the permitted context for a role from corpus/ + metadata/manifest.json.

Permission filtering happens HERE, in code, before anything reaches the model.
Never reads evaluation/.
"""
from __future__ import annotations

import base64
import email
import email.policy
import io
import json
from pathlib import Path

import docx
import openpyxl
from pypdf import PdfReader

BASE = Path(__file__).resolve().parents[1] / "gdtp-onboarding-corpus"
MANIFEST = json.loads((BASE / "metadata" / "manifest.json").read_text(encoding="utf-8"))

# Rows belonging to the case subject (or the suspected duplicate stub) - never the decoy or other joiners.
SUBJECT_KEYS = {"EMP-45821", "EMP-45902", "julie.sour@gdtp.example", "GV-2026-004417",
                "Sour, Julie", "J. Sour"}

ROLE_LABELS = {
    "onboarding_coordinator": "Onboarding Coordinator",
    "security_lead": "Security Lead",
    "hiring_manager": "Hiring Manager",
    "it_service_desk": "IT Service Desk",
}


def _pdf_text(p: Path) -> str:
    return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)


def _docx_text(p: Path) -> str:
    d = docx.Document(p)
    out = [x.text for x in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            out.append(" | ".join(c.text for c in row.cells))
    return "\n".join(out)


def _eml_text(p: Path) -> str:
    m = email.message_from_bytes(p.read_bytes(), policy=email.policy.default)
    hdr = "\n".join(f"{k}: {v}" for k, v in m.items() if k.lower() in ("from", "to", "cc", "subject", "date"))
    body = m.get_body(preferencelist=("plain",))
    return hdr + "\n\n" + (body.get_content() if body else "")


def _xlsx_text(p: Path, masked: list[str]) -> str:
    """Only the case subject's rows, with masked columns removed."""
    ws = openpyxl.load_workbook(p).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    header = list(rows[0])
    keep_cols = [i for i, h in enumerate(header) if h not in masked]
    out = [" | ".join(str(header[i]) for i in keep_cols)]
    for r in rows[1:]:
        if r and any(str(c) in SUBJECT_KEYS for c in r if c is not None):
            out.append(" | ".join("" if r[i] is None else str(r[i]) for i in keep_cols))
    return "\n".join(out)


def _scan_images(p: Path) -> list[str]:
    imgs = []
    for pg in PdfReader(str(p)).pages:
        for im in pg.images:
            imgs.append(base64.b64encode(im.data).decode())
    return imgs


def build_context(role: str):
    """Return (text_blocks, image_b64_list, notes) for this role."""
    blocks, images, notes = [], [], []
    for d in MANIFEST["documents"]:
        did = d["doc_id"]
        path = BASE / d["path"]
        if role in d.get("status_only_roles", []):
            notes.append(f"{did} ({d['title']}): not shown to this role (met / not met status only).")
            continue
        if role not in d["allowed_roles"]:
            continue
        masked = sorted({f for s in d["sections"] for f in s.get("fields_masked_for", {}).get(role, [])})
        acc = {"masked_fields": masked}
        if did == "DOC-05":
            if role == "security_lead":
                images = _scan_images(path)
                text = "[Scanned letter - 2 page images attached separately; read them as OCR.]"
            else:
                notes.append(f"{did} ({d['title']}): this role may see clearance status and decision date only, "
                             "and the letter itself is not provided.")
                continue
        elif path.suffix == ".xlsx":
            text = _xlsx_text(path, acc.get("masked_fields", []))
        elif path.suffix == ".pdf":
            text = _pdf_text(path)
        elif path.suffix == ".docx":
            text = _docx_text(path)
        elif path.suffix == ".eml":
            text = _eml_text(path)
        else:
            text = path.read_text(encoding="utf-8")
        header = (f"=== {did} | {d['title']} | status: {d['status']} | derived: {d['derived']} | "
                  f"authoritative_for: {d['authoritative_for'] or 'nothing'} | dated {d['authored_date']}"
                  f"{' | supersedes ' + d['supersedes'] if d['supersedes'] else ''}"
                  f"{' | superseded_by ' + d['superseded_by'] if d['superseded_by'] else ''} ===")
        if acc.get("masked_fields"):
            header += f"\n(masked for this role: {', '.join(acc['masked_fields'])})"
        blocks.append(f"{header}\n<untrusted_document>\n{text}\n</untrusted_document>")
    return blocks, images, notes
