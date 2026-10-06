"""DOC-02 offer acceptance email."""
from .common import SUBJECT, PEOPLE, START, long, short, EV, PERSONAS, SYN, corpus_path, make_eml


def generate():
    s, rec, mgr = SUBJECT, PEOPLE["recruiter"], PEOPLE["manager"]
    v = PERSONAS["programme"]["variants"]
    body = f"""Hi Sinead,

Thanks for your call earlier in the week and for sending the contract over. I'm delighted to formally accept the offer of {s['role_offer_email']} on the {v['offer_email']}, based in Dublin.

I'm happy with the start date of {long(START)} and I've e-signed the contract today, so you should have the completed copy on your side. Let me know if there's anything else you need from me before then (I think the vetting form is already with you).

Michael, great to be joining the team - looking forward to meeting you.

Kind regards,
Julie Sour

--
{SYN}
"""
    make_eml(corpus_path("02_offer_acceptance.eml"),
             sender=f"{s['name']} <{s['email']}>",
             to=f"{rec['name']} <{rec['email']}>", cc=f"{mgr['name']} <{mgr['email']}>",
             subject="Offer acceptance - Security Analyst, GDTP",
             date="Fri, 09 Oct 2026 15:41:12 +0100",
             message_id="<offer-accept-20261009.1541@gdtp.example>", body=body)
