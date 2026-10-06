"""DOC-03 e-signature certificate of completion (text PDF)."""
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import mm
from .common import SUBJECT, PEOPLE, pdf_doc, footer_fn, styles, table, corpus_path


def generate():
    ss, s = styles(), SUBJECT
    doc = pdf_doc(corpus_path("03_esign_certificate.pdf"), "Certificate of Completion",
                  "GDTP e-Signature Service (synthetic)")
    W = 170 * mm
    rec = PEOPLE["recruiter"]
    story = [
        Paragraph("Certificate of Completion", ss["Title"]),
        Paragraph("GDTP e-Signature Service", ss["Heading3"]),
        Spacer(1, 6),
        table([["Envelope ID", s["esign_envelope"]],
               ["Document", "Employment Contract – Cyber Security Analyst"],
               ["Status", "Completed"],
               ["Envelope originator", f"{rec['name']} ({rec['email']})"],
               ["Sent", "09 Oct 2026 11:05 UTC"],
               ["Completed", "09 Oct 2026 14:22 UTC"],
               ["Pages", "14"]], [45 * mm, W - 45 * mm], header=False),
        Spacer(1, 10),
        Paragraph("Signer", ss["Heading3"]),
        table([["Name", "Email", "Signed (UTC)", "IP address", "Status"],
               [s["name"], s["email"], "09 Oct 2026 14:22:47", s["esign_ip"], "Completed"]],
              [32 * mm, 52 * mm, 36 * mm, 26 * mm, 24 * mm]),
        Spacer(1, 10),
        Paragraph("Signature method: typed adoption of signature, email-link authentication.", ss["Small"]),
        Spacer(1, 10),
        Paragraph("Audit trail", ss["Heading3"]),
        table([["Timestamp (UTC)", "Event", "Actor / detail"],
               ["09 Oct 2026 11:05:12", "Envelope sent", rec["name"]],
               ["09 Oct 2026 14:19:03", "Envelope viewed", f"{s['name']} - {s['esign_ip']}"],
               ["09 Oct 2026 14:21:30", "Consent to e-sign accepted", s["name"]],
               ["09 Oct 2026 14:22:47", "Document signed", s["name"]],
               ["09 Oct 2026 14:22:49", "Envelope completed", "All parties signed"]],
              [40 * mm, 55 * mm, 75 * mm]),
        Spacer(1, 12),
        Paragraph("Document integrity hash (SHA-256, synthetic): "
                  "9f2c41ab07d3e58b6c1a0e44d7f9b2315e8ac6d07b4413f0a96e2d58c1b7e340", ss["Small"]),
        Spacer(1, 6),
        Paragraph("This certificate records the completion of the electronic signature process for the "
                  "envelope above. It is evidence of execution only and does not reproduce the contract "
                  "terms.", ss["Small"]),
    ]
    f = footer_fn(f"Certificate {s['esign_envelope']}")
    doc.build(story, onFirstPage=f, onLaterPages=f)
