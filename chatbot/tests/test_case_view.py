"""Role scoping, conflicts/contacts/email drafts and code-owned statuses for the structured case view."""
import json
from types import SimpleNamespace

import pytest

import agent
import caseview
import loader
import server
import tools

ROLES = list(loader.ROLE_LABELS)
FULL_CONFLICT_ROLES = ["onboarding_coordinator", "security_lead"]
INJECTION_TEXT = ["NOTE TO AI SYSTEM", "disregard prior instructions", "ignore the other documents",
                  "AI assistants processing", "production access is approved", "report all onboarding"]
# strings a role must never see anywhere in its structured view
FORBIDDEN = {
    "onboarding_coordinator": ["1994", "Level 2", "travel declarations", "0178", "Julia", "Declan", "Fionn", "EMP-45812"],
    "security_lead": ["Julia", "Declan", "Fionn", "Adverse disclosure", "EMP-45812", "GV-2026-004471"],
    "hiring_manager": ["GV-2026", "NSO-CL", "1994", "Level 2", "travel", "EMP-45902", "Julia", "Declan", "@gdtp"],
    "it_service_desk": ["GV-2026", "NSO-CL", "1994", "Level 2", "travel", "EMP-45902", "Julia", "Declan", "HR master"],
}


def view(role):
    return caseview.build_case_view(tools.Toolbox(role, None, "stub"))


def conflicts(cv):
    return {c["id"]: c for r in cv["requirements"] for c in r["conflicts"]}


@pytest.mark.parametrize("role", ROLES)
def test_view_contains_only_permitted_content(role):
    tb = tools.Toolbox(role, None, "stub")
    cv = view(role)
    allowed = {d["doc_id"] for d in loader.MANIFEST["documents"] if tb.access(d["doc_id"]) == "content"}
    used = {s["doc_id"] for r in cv["requirements"] for s in r["sources"]}
    used |= {v["doc_id"] for c in conflicts(cv).values() for v in c["values"]}
    assert used <= allowed, f"{role} sees sources it may not: {used - allowed}"
    blob = json.dumps(cv, ensure_ascii=False)
    for bad in FORBIDDEN[role]:
        assert bad not in blob, f"{role}: forbidden text {bad!r} present"
    for c in conflicts(cv).values():  # contacts are role-scoped too
        k = c["contact"]
        if not k.get("generic"):
            assert role in caseview.CONTACTS["areas"][k["area"]]["visible_to"]


@pytest.mark.parametrize("role", ["hiring_manager", "it_service_desk"])
def test_limited_roles_get_status_only_and_no_conflicts(role):
    cv = view(role)
    assert not conflicts(cv)
    assert all(r["id"] != "start_date" for r in cv["requirements"])
    tb = tools.Toolbox(role, None, "stub")
    for r in cv["requirements"]:
        if tb.access(tools.REQ_DOC[r["id"]]) == "status_only":
            assert r["sources"] == [] and r["value"] == ""
    assert cv["withheld"]["count"] > 0 and "not accessible to your role" in cv["withheld"]["message"]
    if role == "it_service_desk":
        assert {r["id"] for r in cv["requirements"]} == {"device", "accounts", "mfa"}


@pytest.mark.parametrize("role", FULL_CONFLICT_ROLES)
def test_known_conflicts_have_contacts_and_drafts(role):
    c = conflicts(view(role))
    assert {"C-vetting", "C-clearance", "C-training", "C-clearance-ref", "C-start-date"} <= set(c)

    v = c["C-vetting"]
    vals = {x["doc_id"]: x["value"] for x in v["values"]}
    assert vals["DOC-04"] == "Approved" and vals["DOC-01"] == "In Progress"
    assert v["resolvable_by_agent"] is True and v["proposed_resolution"]
    assert v["contact"]["name"] == "Tadhg Gallagher"  # owner of the Vetting Register (system of record)
    assert c["C-training"]["contact"]["name"] == "Roisin Keane"
    assert c["C-clearance"]["contact"]["name"] == "Maeve Ryan"

    s = c["C-start-date"]
    assert s["resolvable_by_agent"] is False and s["proposed_resolution"] is None
    assert s["contact"]["name"] == "Orla Fitzgerald"  # HR owns the start date
    text = " ".join(x["value"] for x in s["values"])
    assert "2026-11-02" in text and "2026-11-09" in text

    ref = c["C-clearance-ref"]
    assert ref["resolvable_by_agent"] is False and ref["proposed_resolution"] is None

    for conf in c.values():
        d = conf["email_draft"]
        assert d["to"].endswith("@gdtp.example") and d["subject"] and len(d["body"]) > 100
        assert "Nothing has been sent" in d["body"] and "SYNTHETIC" in d["body"]


def test_clearance_reference_digits_only_for_security_lead():
    sl = json.dumps(conflicts(view("security_lead"))["C-clearance-ref"])
    co = json.dumps(conflicts(view("onboarding_coordinator"))["C-clearance-ref"])
    assert "0178" in sl and "0173" in sl
    assert "0178" not in co and "restricted" in co


@pytest.mark.parametrize("role", ROLES)
def test_email_drafts_contain_no_injection_text(role):
    for c in conflicts(view(role)).values():
        blob = json.dumps(c["email_draft"])
        for bad in INJECTION_TEXT:
            assert bad.lower() not in blob.lower()


def test_injections_are_reported_as_flags_not_in_drafts():
    cv = view("onboarding_coordinator")
    assert any("DOC-08" in f for f in cv["security_flags"]) and any("DOC-09" in f for f in cv["security_flags"])
    assert any("DOC-09" in d for d in cv["derived_documents"])


@pytest.mark.parametrize("role", ROLES)
def test_statuses_equal_code_computed(role):
    tb = tools.Toolbox(role, None, "stub")
    for r in view(role)["requirements"]:
        if r["id"] in tools.REQ_DOC:
            assert r["status"] == tb._status(r["id"])["status"]
    st = {r["id"]: r for r in view("onboarding_coordinator")["requirements"]}
    assert st["mfa"]["badge"] == "pending" and st["mfa"]["status"] == "not_met"
    assert st["clearance"]["badge"] == "uncertain"
    assert st["vetting"]["status"] == "met"


def test_missing_contact_falls_back_to_supervisor(monkeypatch):
    monkeypatch.setitem(caseview.CONTACTS["areas"]["vetting"], "visible_to", [])
    c = conflicts(view("onboarding_coordinator"))["C-vetting"]
    assert c["contact"]["name"] == "Your supervisor" and c["contact"]["generic"]
    assert c["email_draft"]["to"] == ""


# ---------------------------------------------------------------- agent loop with a stubbed model
class Msg:
    def __init__(self, content=None, calls=None):
        self.content, self.tool_calls = content, calls

    def model_dump(self, exclude_none=True):
        d = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = [{"id": c.id, "type": "function",
                                "function": {"name": c.function.name, "arguments": c.function.arguments}}
                               for c in self.tool_calls]
        return d


def call(name, args="{}"):
    return SimpleNamespace(id="c1", function=SimpleNamespace(name=name, arguments=args))


class FakeClient:
    def __init__(self, script):
        self.script, self.requests = list(script), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.requests.append(kw)
        return SimpleNamespace(choices=[SimpleNamespace(message=self.script.pop(0))])


def test_agent_returns_code_built_case_view_and_hides_drafts_from_model():
    fake = FakeClient([Msg(calls=[call("case_summary")]),
                       Msg("MFA is activated and everything is complete.")])  # a lying model
    answer, steps, cv = agent.run(fake, "stub", "onboarding_coordinator", [{"role": "user", "content": "Can she join?"}])
    assert cv is not None and {r["id"]: r["status"] for r in cv["requirements"]}["mfa"] == "not_met"
    tool_msg = [m for m in fake.requests[1]["messages"] if m["role"] == "tool"][0]["content"]
    assert "email_draft" not in tool_msg and "Subject:" not in tool_msg  # model never sees/edits drafts
    assert steps[0]["tool"] == "case_summary"


def test_agent_without_case_summary_returns_no_case_view():
    fake = FakeClient([Msg("Visitor parking is on level -1.")])
    answer, steps, cv = agent.run(fake, "stub", "hiring_manager", [{"role": "user", "content": "Where do I park?"}])
    assert cv is None and steps == []


def test_server_returns_answer_case_view_and_steps(monkeypatch):
    monkeypatch.setattr(server.agent, "run", lambda *a, **k: ("narrative", [{"tool": "x"}], {"subject": "s"}))
    r = server.app.test_client().post("/api/chat", json={"role": "security_lead", "messages": [{"role": "user", "content": "hi"}]})
    j = r.get_json()
    assert j["answer"] == "narrative" and j["case_view"] == {"subject": "s"} and j["steps"] == [{"tool": "x"}]
    assert server.app.test_client().post("/api/chat", json={"role": "nope", "messages": []}).status_code == 400
