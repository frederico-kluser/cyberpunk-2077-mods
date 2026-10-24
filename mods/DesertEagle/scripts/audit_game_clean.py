"""Audit the game install folder for ANY trace of our mod work.

Owner constraint (permanent): nothing we produced may live in the game folder.
This sweeps:
  1. every file/dir under the game root whose CreationTime is AFTER our first
     session activity (2026-10-23 21:30 local)
  2. known trace names (desert_eagle, DesertEagle, our tool staging)

Usage: python3 audit_game_clean.py <game_root>
"""

import os
import sys
from datetime import datetime, timezone

SINCE = datetime(2026, 10, 23, 21, 30, tzinfo=timezone.utc).timestamp()
TRACES = ("desert_eagle", "deserteagle", "desert-eagle")

root = sys.argv[1]
new_files = []
trace_hits = []
scanned = 0

for dirpath, dirnames, filenames in os.walk(root):
    # skip the heavyweight shader/cache dirs nothing of ours could touch
    for name in filenames:
        scanned += 1
        p = os.path.join(dirpath, name)
        try:
            st = os.stat(p)
        except OSError:
            continue
        low = name.lower()
        if any(t in low for t in TRACES) or any(t in p.lower() for t in TRACES):
            trace_hits.append(p)
        # CreationTime on Windows = st_ctime
        if st.st_ctime > SINCE:
            new_files.append((p, datetime.fromtimestamp(st.st_ctime).isoformat()))

print(f"GAME_AUDIT scanned={scanned} files under {root}")
print(f"trace-name hits: {len(trace_hits)}")
for p in trace_hits[:20]:
    print("  TRACE", p)
print(f"files created after {datetime.fromtimestamp(SINCE).isoformat()}: {len(new_files)}")
for p, t in new_files[:25]:
    print(f"  NEW {t}  {p}")

clean = not trace_hits and not new_files
print("GAME_AUDIT_CLEAN" if clean else "GAME_AUDIT_ATTENTION")
