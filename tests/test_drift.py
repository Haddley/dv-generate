#!/usr/bin/env python3
"""Offline tests for skills/dv-generate/scripts/drift.py using the regen scenarios.

For every scenario, release 1 stands in for dev and release 2 for the regenerated saved XML:
  - identical folders        -> exit 0
  - repo = r2, dev = r1       -> the expected drift is reported (this is what dev looks like after a removal)
  - repo = r1, dev = r2       -> the reverse (this is what dev looks like after someone adds it by hand)
  - a removed column          -> the form and view that still use it are reported too
Usage: test_drift.py
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests", "regen"))
import gen  # noqa: E402
import scenarios  # noqa: E402

DRIFT = os.path.join(ROOT, "skills", "dv-generate", "scripts", "drift.py")

# code -> (expected finding present when repo=r2, dev=r1: "[kind]", side heading)
EXPECT = {
    "aa": ("[column]", "In the saved XML, not in dev"),
    "ab": ("[column]", "In dev, not in the saved XML"),
    "ac": ("[column label]", "Different between the two"),
    "ad": ("[option]", "In the saved XML, not in dev"),
    "ae": ("[option]", "In dev, not in the saved XML"),
    "af": ("[column type]", "Different between the two"),
    "ag": ("[table]", "In the saved XML, not in dev"),
    "ah": ("[table]", "In dev, not in the saved XML"),
    "ai": ("[app]", "In dev, not in the saved XML"),
    "ak": ("[view]", "In dev, not in the saved XML"),
    "al": ("[env var]", "In the saved XML, not in dev"),
    "am": ("[connection reference]", "In dev, not in the saved XML"),
    "an": ("[env var value]", "Different between the two"),
    "ao": ("[app]", "In dev, not in the saved XML"),
}


def run(*args):
    r = subprocess.run([sys.executable, "-I", DRIFT, *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def section(out, heading):
    """text of one heading's block"""
    if heading not in out:
        return ""
    rest = out.split(heading + ":", 1)[1]
    for h in ("In dev, not in the saved XML:", "In the saved XML, not in dev:", "Different between the two:"):
        if h in rest:
            rest = rest.split(h, 1)[0]
    return rest


fails = 0


def check(cond, msg):
    global fails
    if not cond:
        fails += 1
        print("FAIL:", msg)


with tempfile.TemporaryDirectory() as tmp:
    for code, desc, muts, mode in scenarios.SCENARIOS:
        rel = scenarios.releases(code, muts)
        r1, r2 = os.path.join(tmp, code, "r1"), os.path.join(tmp, code, "r2")
        gen.build(rel[0][1], r1)
        gen.build(rel[1][1], r2)
        rc, out = run(r1, r1)
        check(rc == 0 and "No drift" in out, f"{code}: identical folders should report no drift\n{out}")
        if code not in EXPECT:
            continue
        kind, heading = EXPECT[code]
        rc, out = run(r2, r1)
        check(rc == 1, f"{code}: repo=r2 dev=r1 should report drift (exit {rc})")
        check(kind in section(out, heading), f"{code}: expected {kind} under '{heading}'\n{out}")
        rc, out = run(r1, r2)  # reversed: the side flips for add/remove, 'changed' stays
        flip = {"In dev, not in the saved XML": "In the saved XML, not in dev", "In the saved XML, not in dev": "In dev, not in the saved XML"}
        check(kind in section(out, flip.get(heading, heading)), f"{code}: reversed run should report {kind} under '{flip.get(heading, heading)}'\n{out}")
        if code == "ab":
            rc, out = run(r2, r1)
            check("[form fields]" in out and "dvgab_amount" in out, "ab: a form that still uses the removed column must be reported\n" + out)
            check("[view columns]" in out, "ab: a view that still uses the removed column must be reported\n" + out)
        print(f"ok   {code}: {desc}")

print("\nALL DRIFT TESTS PASSED" if not fails else f"\n{fails} DRIFT TEST(S) FAILED")
sys.exit(1 if fails else 0)
