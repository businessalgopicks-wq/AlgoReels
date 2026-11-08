#!/usr/bin/env python3
"""Run `hyperframes check` from reel/ and print only what needs a decision.

Run it with ./reel check <reel>.

Uses the HyperFrames version pinned in the reel's package.json. Progress goes to stderr and JSON to stdout, so they are
kept apart. An empty result is reported as a failure of the tool, never as a clean reel.
Exit: 0 pass, 1 errors found, 2 the check itself did not run.
"""
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

pin = re.search(r"hyperframes@[\d.]+", Path("package.json").read_text())
if not pin:
    sys.exit("package.json has no pinned hyperframes@<version> script. Pin one so every render of this reel matches.")
run = subprocess.run(["npx", "--yes", pin.group(0), "check", "--json"], capture_output=True, text=True)
try:
    report = json.loads(run.stdout)
except json.JSONDecodeError:
    print(f"The check did not run (exit {run.returncode}). Last lines from it:", file=sys.stderr)
    print("\n".join(run.stderr.strip().splitlines()[-8:]), file=sys.stderr)
    sys.exit(2)

sections = {k: v for k, v in report.items() if isinstance(v, dict) and "findings" in v}
print("ok:", report.get("ok"), "|", ", ".join(f"{k} {v.get('errorCount', 0)}E {v.get('warningCount', 0)}W" for k, v in sections.items()))

errors = [(k, f) for k, v in sections.items() for f in v["findings"] if f.get("severity") == "error"]
if errors:
    print("\nERRORS, fix all of these")
    for k, f in errors:
        print(f"  {k} {f.get('code')} {f.get('selector', '')} at {f.get('time')}: {str(f.get('message'))[:200]}")
        if f.get("fix") or f.get("fixHint"):
            print(f"    fix: {str(f.get('fix') or f.get('fixHint'))[:200]}")

craft = sections.get("craft", {}).get("findings", [])
if craft:
    print("\nREADING TIME AND TYPE SIZE, decide each one")
    for f in sorted(craft, key=lambda x: x.get("time") or 0):
        print(f"  {f.get('time', 0):6.2f} {str(f.get('selector'))[:34]:34} {str(f.get('message'))[:120]}")

grouped = defaultdict(list)
for k, v in sections.items():
    if k == "craft":
        continue
    for f in v["findings"]:
        if f.get("severity") == "warning":
            grouped[(k, f.get("code"))].append(f)
if grouped:
    print("\nOTHER WARNINGS, weigh each kind")
    for (k, code), fs in grouped.items():
        print(f"  {k} {code} x{len(fs)}: {str(fs[0].get('message'))[:140]}")
sys.exit(0 if report.get("ok") else 1)
