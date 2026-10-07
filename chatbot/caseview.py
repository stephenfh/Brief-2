"""Structured, role-scoped case view built entirely in code.

The model never writes the table, the conflicts, the contacts or the follow-up email drafts: it only narrates.
Everything here is derived from the same permission-checked tool logic (`Toolbox`) and the manifest, so a role
can only ever see what it is allowed to see. Read-only: nothing here sends email or writes to the corpus.
"""
from __future__ import annotations

import json
import re

import loader
import tools

CONTACTS = json.loads((loader.BASE / "metadata" / "contacts.json").read_text(encoding="utf-8"))
SUBJECT_LABEL = "Julie Sour (EMP-45821)"
LABELS = {"contract": "Contract signed", "vetting": "Garda Vetting approved",
          "clearance": "Security Clearance approved", "training": "Cyber training passed",
          "device": "Device assigned", "accounts": "Email and VPN accounts", "mfa": "MFA activated"}
FACT_LABELS = {"vetting": "Garda Vetting status", "clearance": "Security Clearance status",
               "training": "Cyber training status", "clearance_reference": "Security Clearance reference",
               "start_date": "start date"}
MIRROR_COL = {"vetting": "Garda Vetting", "clearance": "Security Clearance", "training": "Training"}
HR_MIRROR_AUTH = "HR master record (weekly mirror, not authoritative)"


def _clean(v, limit: int = 220) -> str:
    """Only plain, short, code-extracted text goes into the view and the drafts."""
    s = re.sub(r"[\x00-\x1f\x7f]+", " ", str(v if v is not None else ""))
    return re.sub(r"\s+", " ", s).strip()[:limit]


def contact_for(doc_id: str, role: str) -> dict:
    """Contact who owns the system of record for `doc_id` (manifest owner_area), scoped to the role."""
    area = tools._doc(doc_id).get("owner_area")
    c = CONTACTS["areas"].get(area)
    if not c or role not in c["visible_to"]:
        return dict(CONTACTS["fallback"], generic=True)
    return {"name": c["name"], "role": c["role"], "email": c["email"], "area": area}


def _src(doc_id, authority, date, value):
    return {"doc_id": doc_id, "authority": authority, "date": _clean(date), "value": _clean(value)}


def email_draft(contact: dict, fact_label: str, values: list[dict], ask: str, cc: str = "") -> dict:
    """Code template only. Uses extracted values/metadata that are already role-scoped; no document prose."""
    lines = [f"- {v['doc_id']} ({v['authority']}, {v['date']}): {v['value']}" for v in values]
    greeting = f"Hello {contact['name']}," if not contact.get("generic") else "Hello,"
    body = "\n".join([
        greeting, "",
        f"I am following up on a discrepancy in the onboarding case for {SUBJECT_LABEL}.", "",
        f"The {fact_label} differs between sources:", *lines, "",
        ask, "",
        "Thank you,", "[Your name]", "",
        "Drafted by the case-view agent for you to review and send. Nothing has been sent. "
        "SYNTHETIC – DEMO ONLY"])
    return {"to": contact.get("email", ""), "cc": cc,
            "subject": f"{SUBJECT_LABEL}: please confirm {fact_label}", "body": body}


def _conflict(cid, fact, summary, values, resolvable, proposal, doc_for_owner, role, ask, cc_doc=None):
    contact = contact_for(doc_for_owner, role)
    cc = ""
    if cc_doc:
        c2 = contact_for(cc_doc, role)
        cc = c2.get("email", "")
    return {"id": cid, "fact": fact, "summary": _clean(summary, 400), "values": values,
            "proposed_resolution": proposal, "resolvable_by_agent": resolvable, "contact": contact,
            "email_draft": email_draft(contact, FACT_LABELS[fact], values, ask, cc)}


def _auth_value(tb, fact, st):
    if fact == "vetting":
        return st["history"][-1][1]
    if fact == "training":
        m = re.search(r"Final Status (\w+)", st["detail"])
        return m.group(1) if m else st["status"]
    return str(st["ocr"].get("status", "")).title()  # clearance


def _status_conflict(tb, fact):
    """HR mirror vs system of record for vetting / clearance / training. None if no conflict or not permitted."""
    cs = tb.compare_sources(fact)
    if "error" in cs or not cs.get("discrepancy"):
        return None
    st = tb._status(fact)
    doc = tools.REQ_DOC[fact]
    auth_name = {"vetting": "Garda Vetting Register", "clearance": "NSO clearance letter",
                 "training": "Cyber Training Tracker"}[fact]
    auth_val = _auth_value(tb, fact, st)
    values = [_src(doc, f"{auth_name} (system of record)", st["as_of"], auth_val),
              _src("DOC-01", HR_MIRROR_AUTH, cs["hr_last_synced"], cs["hr_value"])]
    for o in cs.get("other_sources", []):
        values.append(_src(o["doc"], "Recruiter email (stale)", o["dated"], o["says"]))
    hr_name = contact_for("DOC-01", tb.role)
    ask = (f"Please confirm that the {auth_name} value above is current. If it is, please ask the HR team"
           + (f" ({hr_name['name']})" if not hr_name.get("generic") else "") +
           " to update the stale HR field. The agent has not changed any record.")
    return _conflict(f"C-{fact}", fact,
                     f"HR shows '{cs['hr_value']}' but the {auth_name} (system of record) shows '{auth_val}'.",
                     values, True,
                     f"Treat the {auth_name} as correct; the HR record should be updated by its owner.",
                     doc, tb.role, ask, cc_doc="DOC-01")


def _reference_conflict(tb):
    if tb.access("DOC-05") != "content":
        return None
    o = tb.ocr()
    if not o.get("uncertain"):
        return None
    hr_ref = o.get("hr_reference")
    if tb.role == "security_lead":
        alts = ", ".join(str(a) for a in (o.get("reference_alternatives") or []))
        scan_val = f"Scan reads {o.get('clearance_reference')}; plausible readings: {alts or 'n/a'}"
    else:  # the letter's content beyond status and date is restricted for this role
        scan_val = "Reference cannot be read with confidence from the scan (details restricted for your role)"
    values = [_src("DOC-05", "NSO clearance letter (scanned, medium confidence)", o.get("decision_date"), scan_val)]
    if hr_ref and tb.access("DOC-01") == "content":
        values.append(_src("DOC-01", HR_MIRROR_AUTH, "2026-10-16", f"Reference held in HR: {hr_ref}"))
    return _conflict("C-clearance-ref", "clearance_reference",
                     "The clearance reference in the scanned letter cannot be confirmed with confidence, so the "
                     "identity match for Production access needs a human decision.",
                     values, False, None, "DOC-05", tb.role,
                     "Please confirm the clearance reference issued for this individual; the scanned copy is not "
                     "legible enough for us to be sure. This needs a human decision.", cc_doc=None)


def _start_conflict(tb):
    cs = tb.compare_sources("start_date")
    if "error" in cs:
        return None
    hr_d = tools._doc("DOC-01")["authored_date"]
    values = [_src("DOC-01", "HR master record (system of record)", hr_d,
                   f"{cs['records'][0]['employee_id']}: {cs['records'][0]['start_date']}")]
    if len(cs["records"]) > 1:
        values.append(_src("DOC-01", "HR master record (duplicate draft record)", hr_d,
                           f"{cs['records'][1]['employee_id']}: {cs['records'][1]['start_date']}"))
    for did, val in cs["supporting_emails"].items():
        values.append(_src(did, "Email (supporting, not authoritative)", tools._doc(did)["authored_date"], val))
    return _conflict("C-start-date", "start_date",
                     "HR holds two records for the same person with different start dates. HR is the system of "
                     "record, so only a human can decide.",
                     values, False, None, "DOC-01", tb.role,
                     "Please confirm the correct start date and merge or retire the duplicate draft record "
                     "(EMP-45902). This needs a human decision.")


def _badge(req, status, detail="", uncertain=False):
    if status == "met":
        return ("uncertain", "Met – needs confirmation") if uncertain else ("met", "Met")
    if req == "mfa" and "Pending" in detail:
        return "pending", "Pending"
    return "not_met", "Not met"


def build_case_view(tb) -> dict:
    role = tb.role
    hr_row = None
    if tb.access("DOC-01") == "content":
        hr_row = next(r for r in tools._rows("DOC-01") if r["Employee ID"] == tools.SUBJECT["employee_id"])

    reqs = []
    for req in tools.REQ_DOC:
        doc = tools.REQ_DOC[req]
        lvl = tb.access(doc)
        if lvl == "none":
            continue  # a requirement this role may not see is omitted; counted in `withheld`
        r = tb.get_requirement_status(req)
        uncertain = bool(r.get("ocr_uncertain"))
        badge, label = _badge(req, r["status"], r.get("detail", ""), uncertain)
        row = {"id": req, "label": LABELS[req], "status": r["status"], "badge": badge, "badge_label": label,
               "value": "", "sources": [], "confidence": None, "conflicts": []}
        if lvl == "content":
            val = r["detail"]
            if req == "clearance" and role == "security_lead":
                val += f"; level {r.get('level')}; reference read as {r.get('reference_read_from_scan')}"
            row["value"] = _clean(val, 300)
            row["confidence"] = r.get("confidence", "high")
            sysname = tools._doc(doc)["source_system"]
            row["sources"].append(_src(doc, f"{sysname} (system of record)", r.get("as_of"), val))
            if req in MIRROR_COL and hr_row:
                row["sources"].append(_src("DOC-01", HR_MIRROR_AUTH, hr_row["Last Synced"], hr_row[MIRROR_COL[req]]))
                c = _status_conflict(tb, req)
                if c:
                    row["conflicts"].append(c)
            if req == "clearance":
                c = _reference_conflict(tb)
                if c:
                    row["conflicts"].append(c)
        reqs.append(row)

    if hr_row:  # start date is HR master data, not one of the seven requirements
        c = _start_conflict(tb)
        stub = next((x for x in tools._rows("DOC-01") if x["Employee ID"] == "EMP-45902"), None)
        srcs = [_src("DOC-01", "HR master record (system of record)", hr_row["Last Synced"],
                     f"{hr_row['Employee ID']}: {hr_row['Start Date']}")]
        if stub:
            srcs.append(_src("DOC-01", "HR master record (duplicate draft record)", stub["Last Synced"],
                             f"{stub['Employee ID']}: {stub['Start Date']}"))
        reqs.append({"id": "start_date", "label": "Start date (HR master data)", "status": "unconfirmed",
                     "badge": "unconfirmed", "badge_label": "Unconfirmed",
                     "value": _clean(f"{hr_row['Start Date']} on {hr_row['Employee ID']}; a suspected duplicate "
                                     f"record shows {stub['Start Date'] if stub else 'n/a'}"),
                     "sources": srcs, "confidence": "medium", "conflicts": [c] if c else []})

    tiers = []
    for name, t in tb.assess_access_tiers()["tiers"].items():
        tiers.append({"name": name.capitalize(), "outcome": t["outcome"], "approver": t.get("approver", ""),
                      "blockers": t.get("blockers") or ([t["reason"]] if t.get("reason") else [])})

    flags, derived = [], []
    for d in loader.MANIFEST["documents"]:
        if d["doc_id"] == "DOC-05" or tb.access(d["doc_id"]) != "content":
            continue
        flags += tb.read_document(d["doc_id"]).get("security_flags", [])
        if d["derived"]:
            derived.append(f"{d['doc_id']} {d['title']}: derived summary, not independent evidence")
    n_withheld = sum(1 for d in loader.MANIFEST["documents"] if tb.access(d["doc_id"]) != "content")
    return {"subject": SUBJECT_LABEL, "role": role, "tiers": tiers, "requirements": reqs,
            "withheld": {"count": n_withheld, "message": f"{n_withheld} sources not accessible to your role"},
            "security_flags": flags, "derived_documents": derived}


def condense(cv: dict) -> dict:
    """What the MODEL sees: facts to narrate, no table, no email drafts, no contact blocks."""
    return {
        "note": "The UI already shows the full table, conflict details, contacts and email drafts from code. "
                "Write only a short narrative (recommendation, why, blockers and owners, uncertainty, named "
                "approver). Do not redraw the table and never contradict these statuses.",
        "subject": cv["subject"], "tiers": cv["tiers"],
        "requirements": [{"id": r["id"], "label": r["label"], "status": r["badge_label"], "value": r["value"],
                          "confidence": r["confidence"],
                          "conflicts": [{"summary": c["summary"], "resolvable_by_agent": c["resolvable_by_agent"],
                                         "proposed_resolution": c["proposed_resolution"],
                                         "follow_up_with": c["contact"]["name"]} for c in r["conflicts"]]}
                         for r in cv["requirements"]],
        "security_flags": cv["security_flags"] or "none", "derived_documents": cv["derived_documents"] or "none",
        "withheld": cv["withheld"]["message"]}
