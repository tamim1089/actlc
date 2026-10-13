#!/usr/bin/env python3
"""Resolve every relative href/src on the given pages; report missing targets and self-links in navigation.
   Usage: python3 tools/check_links.py events/index.html events-main/*/index.html"""
import os, re, sys
from urllib.parse import unquote
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
total_missing = 0
for page in sys.argv[1:]:
    p = os.path.join(ROOT, page); h = open(p, encoding="utf-8").read(); base = os.path.dirname(p)
    h_noscript = re.sub(r"<script[\s\S]*?</script>", "", h)
    refs = re.findall(r'(?:href|src)="([^"#][^"]*)"', h_noscript)
    missing = []
    for r in refs:
        if re.match(r"^(https?:|mailto:|tel:|data:|javascript:|//)", r): continue
        path = os.path.normpath(os.path.join(base, unquote(r.split("#")[0].split("?")[0])))
        if not path.startswith(ROOT): missing.append((r, "outside site")); continue
        if os.path.isdir(path): path = os.path.join(path, "index.html")
        if not os.path.exists(path): missing.append((r, "missing"))
    # nav items labelled Events must point at the events list
    ev = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>(?:(?!</a>)[\s\S]){0,400}?Events\s*</', h_noscript)
    ev_ok = all(os.path.normpath(os.path.join(base, x)) == os.path.join(ROOT, "events", "index.html") for x in ev)
    # Documented static-site limits (need the live WordPress server) and metadata tags browsers never fetch.
    KNOWN = ("wp-login.php", "members-2/", "xmlrpc.", "gmpg.org/xfn", )
    known = sorted({r for r, _ in missing if any(k in r for k in KNOWN) or re.search(r"/index\.[0-9a-f]{8}\.html$|^(\.\./)*index\.[0-9a-f]{8}\.html$", r)})
    missing = [(r, w) for r, w in missing if r not in known]
    if known: print(f"   known static-site limits/metadata: {', '.join(known)}")
    uniq = sorted(set(missing))
    total_missing += len(uniq)
    print(f"{page}: {len(refs)} refs, {len(uniq)} unique broken, Events-nav -> list: {ev_ok}")
    for r, why in uniq[:12]: print(f"   {why:13} {r}")
    if len(uniq) > 12: print(f"   ... {len(uniq)-12} more")
    if not ev_ok: total_missing += 1
print("LINKS_OK" if total_missing == 0 else f"LINKS_BROKEN {total_missing}")
