#!/usr/bin/env python3
"""Pull the current state of an UNMANAGED solution from the dev environment and compare it with the saved XML.

  pull.py --env <url> --solution <UniqueName> --dir <SolutionDir> [--apply] [--keep <folder>]

  default   export the unmanaged solution, run drift.py, print the report. Changes nothing in <SolutionDir>.
  --apply   afterwards replace solution.xml, customizations.xml, [Content_Types].xml and
            environmentvariabledefinitions/ in <SolutionDir> with the dev export ("adopt dev as the source of truth").
            Review the result with `git diff`; commit first so you can undo.
  --keep    also leave the extracted export in <folder> for inspection.

Requires the Power Platform CLI (pac) authenticated to the dev environment. Managed solutions cannot be exported
as unmanaged, so this only works for solutions that are unmanaged in <env>.
Exit code: 0 no drift, 1 drift found, 2 error.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


def pac(args, timeout):
    try:
        r = subprocess.run(["pac"] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except FileNotFoundError:
        return 127, "pac not found: install the Power Platform CLI"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", required=True, help="dev environment URL, e.g. https://orgxxxx.crm.dynamics.com/")
    ap.add_argument("--solution", required=True, help="solution unique name")
    ap.add_argument("--dir", required=True, help="folder holding solution.xml and customizations.xml")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--keep")
    a = ap.parse_args()

    if not os.path.exists(os.path.join(a.dir, "solution.xml")):
        print(f"{a.dir} does not contain solution.xml")
        return 2
    tmp = tempfile.mkdtemp(prefix="dvpull-")
    try:
        zpath = os.path.join(tmp, "export.zip")
        for attempt in (1, 2, 3):  # exports occasionally hang; retry with a short timeout
            rc, out = pac(["solution", "export", "--name", a.solution, "--path", zpath, "--overwrite", "--environment", a.env], 150)
            if "export succeeded" in out:
                break
            if "Managed solutions cannot be exported" in out:
                print(f"'{a.solution}' is managed in that environment, and managed solutions cannot be exported. Pull needs the unmanaged copy (your dev environment).")
                return 2
            print(f"export attempt {attempt} failed: {out.strip().splitlines()[-1] if out.strip() else rc}")
        else:
            print("Could not export the solution.")
            return 2
        dev = os.path.join(tmp, "dev")
        with zipfile.ZipFile(zpath) as z:
            z.extractall(dev)
        sol = open(os.path.join(dev, "solution.xml"), encoding="utf-8").read()
        if "<Managed>1</Managed>" in sol:
            print("That solution is managed in the environment; pull needs the unmanaged copy.")
            return 2
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "drift.py"), a.dir, dev], capture_output=True, text=True)
        print(r.stdout, end="")
        print(r.stderr, end="")
        if a.keep:
            shutil.rmtree(a.keep, ignore_errors=True)
            shutil.copytree(dev, a.keep)
            print(f"\nExport kept in {a.keep}")
        if a.apply:
            for name in ("solution.xml", "customizations.xml", "[Content_Types].xml"):
                shutil.copy2(os.path.join(dev, name), os.path.join(a.dir, name))
            envd = os.path.join(a.dir, "environmentvariabledefinitions")
            shutil.rmtree(envd, ignore_errors=True)
            if os.path.isdir(os.path.join(dev, "environmentvariabledefinitions")):
                shutil.copytree(os.path.join(dev, "environmentvariabledefinitions"), envd)
            print(f"\nApplied: {a.dir} now matches the dev export. Review with `git diff`.")
        return r.returncode
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


sys.exit(main())
