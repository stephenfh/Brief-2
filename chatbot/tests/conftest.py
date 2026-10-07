import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")  # server.py builds a client at import time

import pytest  # noqa: E402
import tools  # noqa: E402

# Stand-in for the vision transcription of the scanned letter (what the model returns), so tests need no API.
FAKE_OCR = {"status": "APPROVED", "decision_date": "22 October 2026", "clearance_level": "Level 2 - Programme Access",
            "clearance_reference": "NSO-CL-2026-0178", "reference_confidence": "medium",
            "reference_alternatives": ["NSO-CL-2026-0173"], "hr_reference": "NSO-CL-2026-0173", "uncertain": True,
            "page2_text": "Recommend routine re-review of travel declarations at 12 months. No adverse findings."}


@pytest.fixture(autouse=True)
def stub_ocr():
    tools._OCR_CACHE[:] = [dict(FAKE_OCR)]
    yield
    tools._OCR_CACHE.clear()
