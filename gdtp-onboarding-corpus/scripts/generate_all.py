"""Run every generator in order. Usage: python scripts/generate_all.py [--out DIR]"""
import argparse
import importlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

MODULES = ["doc_01_hr", "doc_02_offer", "doc_03_esign", "doc_04_vetting", "doc_05_clearance_scan",
           "doc_06_training", "doc_07_ticket", "doc_08_recruiter", "doc_09_checklist",
           "doc_10_11_standards", "doc_12_faq", "doc_13_welcome", "doc_14_office",
           "manifest", "evaluation"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="output root (default: repository root)")
    args = ap.parse_args()
    if args.out:
        os.environ["GDTP_OUT"] = str(Path(args.out).resolve())
    for name in MODULES:
        mod = importlib.import_module(f"generators.{name}")
        mod.generate()
        print(f"generated {name}")


if __name__ == "__main__":
    main()
