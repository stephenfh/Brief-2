"""DOC-01 HR master record (xlsx)."""
from .common import (SUBJECT, DECOY, STUB, JOINERS, EV, START, SYN, corpus_path, new_workbook,
                     style_header, save_workbook)

COLUMNS = ["Employee ID", "Name", "DOB", "Role", "Programme", "Office", "Start Date", "Manager",
           "HR Status", "Vetting Ref", "Garda Vetting", "Security Clearance Ref",
           "Security Clearance", "Training", "Record Created", "Last Synced", "Record Source"]


def _joiner_hr_values(j):
    t = j["training"]["final"]
    training = {"Passed": "Complete", "Failed": "Failed", "In Progress": "In progress",
                "Not started": "Outstanding"}[t]
    vet = {"Approved": "Approved", "Rejected": "Failed"}.get(j["vetting_status"],
          "In Progress" if j["vetting_status"] == "Under review" else "Pending")
    return [j["employee_id"], j["name"], j["dob"], j["role"], j["programme"], j["office"],
            j["start_date"], j["manager"], j["hr_status"], j["vetting_ref"], vet,
            j["clearance_ref"], j["clearance_status"], training, "2026-09-28",
            EV["hr_last_sync"], "HRIS (weekly sync)"]


def generate():
    wb = new_workbook()
    ws = wb.active
    ws.title = "Employees"
    ws.append(COLUMNS)
    h = SUBJECT["hr"]
    ws.append([SUBJECT["employee_id"], SUBJECT["name"], SUBJECT["dob"], SUBJECT["role"],
               SUBJECT["programme"], SUBJECT["office"], START, SUBJECT["manager"], h["hr_status"],
               SUBJECT["vetting_ref"], h["garda_vetting"], SUBJECT["clearance_ref"],
               h["security_clearance"], h["training"], h["record_created"], EV["hr_last_sync"],
               h["record_source"]])
    ws.append([STUB["employee_id"], STUB["name"], STUB["dob"], STUB["role"], STUB["programme"],
               STUB["office"], STUB["start_date"], STUB["manager"], STUB["hr_status"], "", "", "",
               "", "", STUB["record_created"], STUB["last_synced"], STUB["record_source"]])
    dh = DECOY["hr"]
    ws.append([DECOY["employee_id"], DECOY["name"], DECOY["dob"], DECOY["role"], DECOY["programme"],
               DECOY["office"], DECOY["start_date"], DECOY["manager"], dh["hr_status"],
               DECOY["vetting_ref"], dh["garda_vetting"], "", dh["security_clearance"],
               dh["training"], dh["record_created"], EV["hr_last_sync"], dh["record_source"]])
    rows = [_joiner_hr_values(j) for j in JOINERS]
    for r in sorted(rows, key=lambda r: r[0]):
        ws.append(r)
    style_header(ws, len(COLUMNS), [12, 20, 12, 24, 36, 9, 12, 16, 20, 16, 14, 20, 16, 13, 14, 12, 22])
    ws.append([])
    ws.append([f"-- {SYN} --"])

    about = wb.create_sheet("About this export")
    lines = [
        ["HR master record export (HRIS)"],
        [f"Export generated: {EV['hr_last_sync']}"],
        ["Mirrored fields: Garda Vetting, Security Clearance and Training are mirrored from the "
         "source systems (Garda Vetting Register, NSO clearance letters, Cyber Training Tracker) "
         "on a weekly basis."],
        ["HR is NOT the system of record for vetting, clearance or training status. Values here may "
         "lag the source systems by up to a week."],
        ["HR is the system of record for employee master data (name, role, programme, start date)."],
        ["Contact: HR Operations (synthetic)"],
        [SYN],
    ]
    for ln in lines:
        about.append(ln)
    about.column_dimensions["A"].width = 120
    about.oddFooter.center.text = SYN
    save_workbook(wb, corpus_path("01_hr_master_record.xlsx"))
