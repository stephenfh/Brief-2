"""DOC-13 welcome email from manager."""
from .common import SUBJECT, PEOPLE, START, long, SYN, corpus_path, make_eml


def generate():
    s, mgr = SUBJECT, PEOPLE["manager"]
    body = f"""Hi Julie,

Just a quick note to say we're all looking forward to seeing you on {long(START)} at the Dublin office.

Please bring photo ID (passport or driving licence) - security will need to see it at reception. Come to reception for 9:00 and I'll meet you there and walk you through the first day. We'll start with a team coffee, then the induction session in the afternoon.

If anything comes up before then, just reply to this or give me a shout.

See you next Monday!

Michael

Michael Byrne
Programme Delivery Manager, GDTP

{SYN}
"""
    make_eml(corpus_path("13_welcome_email.eml"),
             sender=f"{mgr['name']} <{mgr['email']}>", to=f"{s['name']} <{s['email']}>",
             subject="Welcome to the team - Monday 2 November",
             date="Mon, 26 Oct 2026 16:05:33 +0000",
             message_id="<welcome-20261026.1605@gdtp.example>", body=body)
