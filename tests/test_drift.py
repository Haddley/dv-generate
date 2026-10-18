#!/usr/bin/env python3
"""Offline tests for skills/dv-generate/scripts/drift.py using the regen scenarios.

For every scenario, release 1 stands in for dev and release 2 for the regenerated saved XML:
  - identical folders        -> exit 0
  - repo = r2, dev = r1       -> the expected drift is reported (this is what dev looks like after a removal)
  - repo = r1, dev = r2       -> the reverse (this is what dev looks like after someone adds it by hand)
  - --manual on removals      -> the right manual step is named
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

# code -> (expected finding present when repo=r2, dev=r1: "[kind]" , side heading, manual step text or None)
EXPECT = {
    "aa": ("[column]", "In the saved XML, not in dev", None),
    "ab": ("[column]", "In dev, not in the saved XML", "Delete column 'dvgab_amount'"),
    "ac": ("[column label]", "Different between the two", None),
    "ad": ("[option]", "In the saved XML, not in dev", None),
    "ae": ("[option]", "In dev, not in the saved XML", "Remove option"),
    "af": ("[column type]", "Different between the two", None),
    "ag": ("[table]", "In the saved XML, not in dev", None),
    "ah": ("[table]", "In dev, not in the saved XML", "Table 'dvgah_beta'"),
    "ai": ("[app]", "In dev, not in the saved XML", "App 'dvgai_app'"),
    "ak": ("[view]", "In dev, not in the saved XML", "Delete view 'All Alphas ak'"),
    "al": ("[env var]", "In the saved XML, not in dev", None),
    "am": ("[connection reference]", "In dev, not in the saved XML", "Connection reference 'dvgam_cr1'"),
    "an": ("[env var value]", "Different between the two", None),
    "ao": ("[app]", "In dev, not in the saved XML", "App 'dvgao_app'"),
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
        kind, heading, manual = EXPECT[code]
        rc, out = run(r2, r1)
        check(rc == 1, f"{code}: repo=r2 dev=r1 should report drift (exit {rc})")
        check(kind in section(out, heading), f"{code}: expected {kind} under '{heading}'\n{out}")
        rc, out = run(r1, r2)  # reversed: the side flips for add/remove, 'changed' stays
        flip = {"In dev, not in the saved XML": "In the saved XML, not in dev", "In the saved XML, not in dev": "In dev, not in the saved XML"}
        check(kind in section(out, flip.get(heading, heading)), f"{code}: reversed run should report {kind} under '{flip.get(heading, heading)}'\n{out}")
        rc, out = run(r2, r1, "--manual")
        if manual:
            check(manual in out, f"{code}: --manual should mention '{manual}'\n{out}")
        else:
            check("No manual steps" in out, f"{code}: --manual should report no manual steps\n{out}")
        if code == "ah":
            rc, out = run(r2, r1, "--manual")
            check("fails while the app remains" in out, "ah: removing a table while an app remains must warn that the upgrade will fail\n" + out)
            check("ALL ITS ROWS" in out, "ah: removing a table must warn about data loss")
        if code == "ai":
            rc, out = run(r2, r1, "--manual")
            check("fails while the app remains" not in out, "ai: app is removed too, so there must be no app warning\n" + out)
            check("ALL ITS ROWS" in out, "ai: removing a table must warn about data loss")
        if code == "ab":
            rc, out = run(r2, r1, "--manual")
            check("pac solution import" in out and "--publish-changes" in out, "ab: when dev still uses the column on a form, the manual steps must say to re-import with pac first\n" + out)
            check("deletes that column's data" in out or "column's data" in out, "ab: removing a column must warn about data loss")
        print(f"ok   {code}: {desc}")

print("\nALL DRIFT TESTS PASSED" if not fails else f"\n{fails} DRIFT TEST(S) FAILED")
sys.exit(1 if fails else 0)
