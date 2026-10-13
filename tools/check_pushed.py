#!/usr/bin/env python3
"""Site sources committed and pushed: HEAD == origin/main and no uncommitted changes in site paths. Prints PUSHED."""
import subprocess, sys
g = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
subprocess.run(["git", "fetch", "-q"], check=False)
dirty = g("status", "--porcelain", "--", "actlc-assets", "tools", "index.html", "events", "events-main", "conference", "registration", "wp-content/uploads/elementor/google-fonts/css")
ok = g("rev-parse", "HEAD") == g("rev-parse", "origin/main") and not dirty
print("PUSHED" if ok else f"NOT_PUSHED head={g('rev-parse','--short','HEAD')} origin={g('rev-parse','--short','origin/main')} dirty={dirty!r}")
sys.exit(0 if ok else 1)
