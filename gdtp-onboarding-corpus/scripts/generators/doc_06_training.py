"""DOC-06 Cyber training tracker (xlsx), keyed on email."""
from .common import SUBJECT, DECOY, JOINERS, SYN, short, corpus_path, new_workbook, style_header, save_workbook

COLUMNS = ["Email", "Name", "Cyber Awareness (date/score)", "Data Protection (date/score)",
           "Acceptable Use Policy (date/attested)", "Final Status", "Last Updated"]


def generate():
    t = SUBJECT["training"]
    rows = [[SUBJECT["email"], SUBJECT["name"],
             f"{short(t['cyber_awareness']['date'])} / {t['cyber_awareness']['score']}",
             f"{short(t['data_protection']['date'])} / {t['data_protection']['score']}",
             f"{short(t['aup']['date'])} / attested", t["final"], t["updated"]],
            [DECOY["email"], DECOY["name"], "Not started", "Not started", "Not started",
             DECOY["training_status"], "2026-10-05"]]
    for j in JOINERS:
        tr = j["training"]
        rows.append([j["email"], j["name"], tr["ca"], tr["dp"], tr["aup"], tr["final"], tr["updated"]])
    wb = new_workbook()
    ws = wb.active
    ws.title = "Tracker"
    ws.append(COLUMNS)
    for r in sorted(rows, key=lambda r: r[0]):
        ws.append(r)
    style_header(ws, len(COLUMNS), [34, 22, 24, 24, 30, 14, 14])
    ws.append([])
    ws.append([f"-- {SYN} --"])
    about = wb.create_sheet("About")
    for ln in ["Cyber Training Tracker (LMS export). Keyed on work email address, not employee ID.",
               "System of record for mandatory onboarding training: Cyber Awareness, Data Protection, "
               "Acceptable Use Policy.", SYN]:
        about.append([ln])
    about.column_dimensions["A"].width = 100
    about.oddFooter.center.text = SYN
    save_workbook(wb, corpus_path("06_cyber_training_tracker.xlsx"))
