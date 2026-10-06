"""DOC-04 Garda Vetting Register (xlsx, append-only history)."""
from .common import (SUBJECT, DECOY, JOINERS, EV, PERSONAS, SYN, corpus_path, new_workbook,
                     style_header, save_workbook)

COLUMNS = ["Entry ID", "Vetting Ref", "Applicant (Surname, Forename)", "DOB", "Programme",
           "Event Date", "Status", "Updated By", "Reviewer comment"]


def generate():
    rows = []
    reg = PERSONAS["programme"]["variants"]["vetting_register"]
    rows.append((EV["vetting_submitted"], SUBJECT["vetting_ref"], "Sour, Julie", SUBJECT["dob"], reg,
                 "Under review", "R. Quinn", "Application received, referee checks started"))
    rows.append((EV["vetting_approved"], SUBJECT["vetting_ref"], "Sour, Julie", SUBJECT["dob"], reg,
                 "Approved", "T. Gallagher", "Approved, no adverse findings"))
    rows.append((DECOY["vetting_date"], DECOY["vetting_ref"], "Sour, Julia", DECOY["dob"],
                 DECOY["programme"], DECOY["vetting_status"], "vetting.system", DECOY["vetting_comment"]))
    for j in JOINERS:
        fore, _, sur = j["name"].rpartition(" ")
        applicant = f"{sur}, {fore}"
        for i, (date, status, by) in enumerate(j["vetting_history"]):
            last = i == len(j["vetting_history"]) - 1
            comment = j["vetting_comment"] if last else "Application received"
            rows.append((date, j["vetting_ref"], applicant, j["dob"], j["programme"], status, by, comment))
    rows.sort(key=lambda r: (r[0], r[1]))

    wb = new_workbook()
    ws = wb.active
    ws.title = "Register"
    ws.append(COLUMNS)
    for n, r in enumerate(rows, start=1):
        ws.append([f"VR-{2600 + n:05d}", r[1], r[2], r[3], r[4], r[0], r[5], r[6], r[7]])
    style_header(ws, len(COLUMNS), [11, 16, 28, 12, 36, 12, 34, 15, 52])
    ws.append([])
    ws.append([f"-- {SYN} --"])

    notes = wb.create_sheet("About this register")
    for ln in ["Garda Vetting Register - append-only history. One row per status event.",
               "This register is the system of record for Garda Vetting outcomes.",
               "Rows are never edited; a new row is appended for each status change.",
               "Handling: OFFICIAL-SENSITIVE (synthetic). Reviewer comments restricted to Security Office.",
               SYN]:
        notes.append([ln])
    notes.column_dimensions["A"].width = 100
    notes.oddFooter.center.text = SYN
    save_workbook(wb, corpus_path("04_garda_vetting_register.xlsx"))
