"""DOC-07 IT provisioning ticket export (text PDF)."""
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import mm
from .common import (SUBJECT, PEOPLE, PERSONAS, TIMELINE, EV, short, pdf_doc, footer_fn, styles,
                     table, corpus_path)


def generate():
    ss, s = styles(), SUBJECT
    prog = PERSONAS["programme"]["variants"]["it_ticket"]
    eta = short(TIMELINE["mfa_eta"])
    desk = PEOPLE["service_desk"]["name"]
    doc = pdf_doc(corpus_path("07_it_provisioning_ticket_IT-8821.pdf"),
                  f"IT Service Desk ticket {s['it_ticket']}", "GDTP IT Service Desk (synthetic)")
    W = 170 * mm
    story = [
        Paragraph(f"IT Service Desk - Ticket {s['it_ticket']}", ss["Title"]),
        Paragraph("New starter provisioning request (export)", ss["Heading3"]),
        Spacer(1, 4),
        table([["Ticket", s["it_ticket"]],
               ["Summary", "New starter provisioning - Cyber Security Analyst"],
               ["Opened", short(EV["it_ticket_opened"])],
               ["Requester", PEOPLE["coordinator"]["name"]],
               ["Assignee", desk],
               ["Programme", prog],
               ["Employee", f"{s['name']} ({s['username']})"],
               ["Status", "In Progress"],
               ["Last updated", short(EV["it_ticket_last_updated"])]],
              [40 * mm, W - 40 * mm], header=False),
        Spacer(1, 10),
        Paragraph("Line items", ss["Heading3"]),
        table([["Item", "Status", "Date", "Detail"],
               ["Laptop", "Assigned", short(EV["laptop_assigned"]),
                f"Asset tag {s['laptop_asset_tag']}, imaged and ready for collection"],
               ["Email account", "Created", short(EV["email_created"]), s["email"]],
               ["VPN", "Created", short(EV["vpn_created"]), f"Profile created for {s['username']}"],
               ["Multi-Factor Authentication (MFA)", "Pending", short(EV["mfa_checked_pending"]),
                f"Hardware token in transit, ETA {eta}. Activation requires the user in person at the "
                "Service Desk."]],
              [44 * mm, 22 * mm, 24 * mm, 80 * mm]),
        Spacer(1, 10),
        Paragraph("Activity log", ss["Heading3"]),
        table([["Date", "By", "Entry"],
               [short(EV["it_ticket_opened"]), PEOPLE["coordinator"]["name"],
                "Ticket opened. Laptop, email, VPN and MFA token requested for new starter."],
               ["21 Oct 2026", desk, "Ticket accepted and assigned."],
               [short(EV["laptop_assigned"]), desk, f"Laptop {s['laptop_asset_tag']} assigned to {s['username']}."],
               [short(EV["email_created"]), desk, "Mailbox created. VPN profile created. MFA token ordered."],
               [short(EV["it_ticket_last_updated"]), desk,
                f"MFA still pending: courier reports token in transit, ETA {eta}. User must activate in "
                "person; to be arranged on arrival."]],
              [24 * mm, 30 * mm, 116 * mm]),
        Spacer(1, 10),
        Paragraph("Ticket will remain open until MFA activation is confirmed.", ss["Small"]),
    ]
    f = footer_fn(f"{s['it_ticket']} export")
    doc.build(story, onFirstPage=f, onLaterPages=f)
