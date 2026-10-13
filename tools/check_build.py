#!/usr/bin/env python3
"""Build twice; generated pages must be byte-identical (idempotent). Prints IDEMPOTENT on success."""
import hashlib, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "events/index.html", "conference/index.html", "registration/index.html",
         "events-main/designing-ai-ready-graduates/index.html", "events-main/teaching-the-learner-not-the-label/index.html",
         "events-main/designing-ai-ready-graduates/event.ics", "events-main/teaching-the-learner-not-the-label/event.ics"]
def digest(): return hashlib.sha256(b"".join(open(os.path.join(ROOT, p), "rb").read() for p in PAGES)).hexdigest()
for _ in range(2): subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_events.py")], check=True, capture_output=True)
a = digest(); subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_events.py")], check=True, capture_output=True)
print("IDEMPOTENT" if digest() == a else "NOT_IDEMPOTENT"); sys.exit(0 if digest() == a else 1)
