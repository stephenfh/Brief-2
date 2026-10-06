"""DOC-10 (v3.2, current) and DOC-11 (v2.9, outdated) onboarding standards (text PDFs)."""
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import mm
from .common import PEOPLE, TIMELINE, short, pdf_doc, footer_fn, styles, table, corpus_path

OWNER = PEOPLE["security_lead"]["name"]


def _build(path, version, effective, control_rows, r6, corporate, production):
    ss = styles()
    doc = pdf_doc(path, f"GDTP Onboarding and Access Standard v{version}", OWNER)

    def P(t, st="BodyText"):
        return Paragraph(t, ss[st])

    story = [
        P("GDTP Onboarding and Access Standard", "Title"),
        P(f"Version {version} | Effective {short(effective)} | Owner: {OWNER}, Security Lead", "Heading3"),
        Spacer(1, 6),
        P("1. Purpose and scope", "Heading2"),
        P("This standard sets out what must be in place before a new joiner on the Garda Digital "
          "Transformation Programme (GDTP) is given access to programme systems, and who may approve each "
          "level of access. It applies to employees and contractors starting on the programme."),
        Spacer(1, 4),
        P("2. Onboarding requirements", "Heading2"),
        P("Each requirement has one system of record. Evidence should be taken from that system of record. "
          "The HR master record mirrors vetting, clearance and training status weekly and is not "
          "authoritative for them."),
        Spacer(1, 4),
        table([["#", "Requirement", "System of record", "Acceptable evidence"],
               ["R1", "Contract signed", "E-signature service", "E-signature certificate of completion"],
               ["R2", "Garda Vetting approved", "Garda Vetting Register", "Register entry with status Approved"],
               ["R3", "Security Clearance approved", "National Security Office (NSO)", "NSO clearance letter"],
               ["R4", "Cyber training passed (Cyber Awareness, Data Protection, Acceptable Use)",
                "Cyber Training Tracker", "Tracker entry with Final Status Passed"],
               ["R5", "Device assigned", "IT provisioning ticket",
                "Ticket line item: laptop assigned, asset tag recorded"],
               ["R6", r6[0], "IT provisioning ticket", r6[1]]],
              [10 * mm, 62 * mm, 40 * mm, 58 * mm]),
        Spacer(1, 4),
        P("Summaries, checklists and emails compiled from these systems are derived material and are not "
          "independent evidence."),
        Spacer(1, 4),
        P("3. Access tiers", "Heading2"),
        table([["Tier", "Requirements", "Approved by"],
               ["Induction", "Contract signed (R1)", "Onboarding Coordinator"],
               ["Corporate", corporate, "Onboarding Coordinator"],
               ["Production", production, "Security Lead"]],
              [28 * mm, 112 * mm, 30 * mm]),
        Spacer(1, 4),
        P("4. Handling conflicts between sources", "Heading2"),
        P("The system of record wins for its own fact. When sources disagree, record the discrepancy and "
          "recommend that the owning team updates their record. Do not overwrite another team's record. "
          "Where authority is unclear, or where identity cannot be confirmed, escalate to the Onboarding "
          "Coordinator for a human decision."),
        Spacer(1, 4),
        P("5. Identity matching", "Heading2"),
        P("Match records on stable identifiers (employee ID, vetting reference, clearance reference, email "
          "address) together with date of birth. Never match on name alone."),
        Spacer(1, 4),
        P("6. Document control", "Heading2"),
        table([["Item", "Detail"]] + control_rows, [40 * mm, 130 * mm]),
    ]
    f = footer_fn(f"GDTP Onboarding and Access Standard v{version}")
    doc.build(story, onFirstPage=f, onLaterPages=f)


def generate():
    s = TIMELINE["standards"]
    _build(corpus_path("10_onboarding_standard_v3.2.pdf"), "3.2", s["v3_2_effective"],
           [["Version", "3.2"], ["Effective date", short(s["v3_2_effective"])],
            ["Supersedes", "This version supersedes v2.9 (effective 1 Mar 2025)."],
            ["Owner", f"{OWNER}, Security Lead"],
            ["Change summary", "Account provisioning now includes MFA activation. MFA must be active before "
                               "Production access is granted; there is no post-start grace period for "
                               "Production."]],
           ("Account provisioning complete, including MFA activated",
            "Ticket shows email, VPN and MFA all complete (MFA status Activated)"),
           "Contract (R1), vetting (R2), training (R4), device (R5) and email/VPN account created "
           "(part of R6; MFA is not required at this tier)",
           "All six requirements (R1 to R6), including MFA active and clearance verified")
    _build(corpus_path("11_onboarding_standard_v2.9.pdf"), "2.9", s["v2_9_effective"],
           [["Version", "2.9"], ["Effective date", short(s["v2_9_effective"])],
            ["Owner", f"{OWNER}, Security Lead"],
            ["Change summary", "Annual review; wording updates only."]],
           ("Account provisioning complete. MFA may be completed within 5 working days of start date and "
            "does not block Production access",
            "Ticket shows email and VPN created and MFA token ordered (activation may follow after start)"),
           "Contract (R1), vetting (R2), training (R4), device (R5) and email/VPN account created "
           "(part of R6)",
           "R1 to R5, email and VPN accounts, clearance verified. MFA (R6) may follow within 5 working "
           "days of start date")
