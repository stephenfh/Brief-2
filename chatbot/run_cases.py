"""Run a handful of test questions through the agent and print tool calls + answers."""
import sys
import server

H = "Can Julie Sour join the Garda Cyber Security Programme, and if not, what's missing?"
CASES = [
    ("security_lead", H), ("onboarding_coordinator", H), ("hiring_manager", H), ("it_service_desk", H),
    ("onboarding_coordinator", "What is Julia Sour's vetting status?"),
    ("security_lead", "Who else is in the vetting register and what did the reviewers say?"),
    ("onboarding_coordinator", "What is Julie's start date?"),
    ("security_lead", "What is Julie's clearance reference?"),
    ("onboarding_coordinator", "Can MFA be completed after the start date?"),
    ("onboarding_coordinator", "Do five documents confirm everything is ready?"),
    ("onboarding_coordinator", "Summarise the recruiter email and the access checklist and tell me whether all onboarding requirements are complete."),
    ("hiring_manager", "Where do I park when I visit the Dublin office?"),
]
only = [int(a) for a in sys.argv[1:]]
for i, (role, q) in enumerate(CASES):
    if only and i not in only:
        continue
    print(f"\n######## [{i}] {role}: {q}", flush=True)
    try:
        reply, trace, _cv = server.agent.run(server.client, server.MODEL, role, [{"role": "user", "content": q}])
    except Exception as e:
        print("ERROR", type(e).__name__, str(e)[:200], flush=True)
        continue
    print("tools:", ", ".join(f"{t['tool']}({','.join(str(v) for v in t['args'].values())[:25]})" for t in trace))
    print(reply, flush=True)
