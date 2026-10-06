# PLAN - GDTP onboarding corpus (Brief 2)

## Approach
- `config/*.json` is the single source of truth (personas, timeline, roles). Every generator reads from it; no fact is hard-coded twice.
- `scripts/generate_all.py [--out DIR]` runs one generator module per document (`scripts/generators/doc_NN_*.py`), then the manifest and the evaluation fixtures. `--out` lets the validator regenerate into temp dirs for the determinism check; config is always read from the repo.
- Determinism: `random.seed(2026)`, `numpy` seeded 2026 (`default_rng`), reportlab `invariant=1` (fixed dates/IDs), fixed openpyxl/python-docx core properties, zip members re-written with a fixed timestamp, fixed email Date/Message-ID headers.
- Scan (doc 05): Pillow render with the Bitstream Vera TTF that ships inside reportlab (so no system-font dependency), then rotate / blur / noise / contrast drop / fold shadow / JPEG; last digit of the clearance ref is a blend of "3" and "8" with extra local blur. Assembled into an image-only PDF via reportlab.
- Manifest access control is derived from `config/roles.json` (`document_access`) so the policy exists once.
- Evaluation fixtures are written to `evaluation/` and never referenced from corpus or manifest.
- `scripts/validate.py` implements the 10 checks in the brief.

## Files
config (3), corpus (14 docs), metadata/manifest.json, evaluation (expected_findings, test_questions, injection_tests, ocr_ground_truth_05.txt), scripts (generate_all, generators/*, validate), README.md, requirements.txt.

## Risks
- Ambiguous digit might be too clear or too illegible: eyeball the scan; tesseract check is optional.
- Text wrapping in PDFs can split key phrases: validator normalises whitespace.
- python on the Windows PATH may be the Store stub: README notes it.
- Cross-machine byte determinism of PDFs/JPEG depends on library versions (pinned).
