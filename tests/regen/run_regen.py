#!/usr/bin/env python3
"""Regeneration matrix runner (live: needs two Dataverse dev environments and pac).

For each scenario in scenarios.py:
  SOURCE env (unmanaged development):
    1. import release 1, export it as managed (M1)
    2. import release 2 over it (plain overwrite) and observe what the solution/environment holds
    3. delete the solution wrapper, import release 2 again (so the solution equals the zip), observe,
       export as managed (M2)  [and M3 for three-release scenarios]
  TARGET env (managed deployment):
    4. install M1, observe, then upgrade to M2 (or plain-update, for 'update' scenarios), observe
Results go to tests/regen/results/<code>.json. Nothing is asserted here: this is the observation
layer. Use summarize.py to read the results.

Usage: run_regen.py <source-url> <target-url> [code ...]
Use throwaway dev environments only. Each scenario has its own publisher prefix ('dvg' + code).
"""
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen  # noqa: E402
import scenarios  # noqa: E402

SRC, TGT = sys.argv[1], sys.argv[2]
ONLY = set(sys.argv[3:])
WORK = os.environ.get("REGEN_WORK", os.path.join(HERE, "work"))
RESULTS = os.path.join(HERE, "results")
os.makedirs(WORK, exist_ok=True)
os.makedirs(RESULTS, exist_ok=True)
LOG = open(os.path.join(HERE, "regen.log"), "a", buffering=1)
BANNERS = ("Microsoft PowerPlatform CLI", "Version:", "Online documentation", "Feedback,", "Connected as", "Connected to")


def log(*a):
    line = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(line, flush=True)
    LOG.write(line + "\n")


def pac(args, timeout=420, retries=0):
    for attempt in range(retries + 1):
        try:
            r = subprocess.run(["pac"] + args, capture_output=True, text=True, timeout=timeout)
            return r.returncode, (r.stdout + r.stderr)
        except subprocess.TimeoutExpired:
            log(f"  TIMEOUT ({timeout}s) pac {' '.join(args[:3])} attempt {attempt + 1}")
    return 124, "timeout"


def pack(src_dir, zip_path):
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ("[Content_Types].xml", "solution.xml", "customizations.xml"):
            z.write(os.path.join(src_dir, name), name)
        envd = os.path.join(src_dir, "environmentvariabledefinitions")
        if os.path.isdir(envd):
            for base, _, files in os.walk(envd):
                for f in files:
                    p = os.path.join(base, f)
                    z.write(p, os.path.relpath(p, src_dir).replace(os.sep, "/"))


def import_result(env, path, extra=()):
    rc, out = pac(["solution", "import", "--path", path, "--environment", env, "--publish-changes", *extra], timeout=900)
    ok = "Solution Imported successfully" in out
    err = next((l.strip() for l in out.splitlines() if l.startswith("Error")), None)
    return {"ok": ok, "error": err[:300] if err else None}


def export(env, name, path, managed):
    args = ["solution", "export", "--name", name, "--path", path, "--overwrite", "--environment", env]
    if managed:
        args.append("--managed")
    for attempt in range(3):
        rc, out = pac(args, timeout=150)
        if "export succeeded" in out:
            return True
        log(f"  export retry {attempt + 1} for {name} managed={managed}: {out.strip()[-120:]}")
    return False


# ---------------------------------------------------------------- observation
def observe_dev(zip_path):
    """What the solution actually contains, from an unmanaged export."""
    d = zip_path[:-4]
    shutil.rmtree(d, ignore_errors=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(d)
    c = ET.parse(os.path.join(d, "customizations.xml")).getroot()
    s = ET.parse(os.path.join(d, "solution.xml")).getroot()
    out = {"version": s.findtext("SolutionManifest/Version"), "entities": {}, "roots": [], "envvars": [], "connrefs": [], "apps": {}}
    for r in s.findall("SolutionManifest/RootComponents/RootComponent"):
        out["roots"].append(f"{r.get('type')}:{r.get('schemaName')}")
    for e in c.findall("Entities/Entity"):
        n = e.findtext("Name")
        attrs, opts, labels = {}, {}, {}
        for a in e.findall("EntityInfo/entity/attributes/attribute"):
            ln = a.findtext("LogicalName")
            attrs[ln] = a.findtext("Type")
            dn = a.find("displaynames/displayname")
            labels[ln] = dn.get("description") if dn is not None else None
            vals = sorted(o.get("value") for o in a.findall("optionset/options/option"))
            if vals and attrs[ln] == "picklist":
                opts[ln] = vals
        views = sorted(x.get("description") for x in e.findall("SavedQueries//savedquery/LocalizedNames/LocalizedName"))
        out["entities"][n] = {"attrs": attrs, "options": opts, "labels": labels, "views": views}
    envd = os.path.join(d, "environmentvariabledefinitions")
    if os.path.isdir(envd):
        for n in sorted(os.listdir(envd)):
            r = ET.parse(os.path.join(envd, n, "environmentvariabledefinition.xml")).getroot()
            out["envvars"].append({"name": n, "default": r.findtext("defaultvalue")})
    out["connrefs"] = sorted(x.get("connectionreferencelogicalname") for x in c.findall("connectionreferences/connectionreference"))
    for a in c.findall("AppModules/AppModule"):
        out["apps"][a.findtext("UniqueName")] = sorted(x.get("schemaName") for x in a.findall("AppModuleComponents/AppModuleComponent"))
    return out


def fetch(env, entity, attrs, filt=""):
    xml = f"<fetch><entity name='{entity}'>" + "".join(f"<attribute name='{a}'/>" for a in attrs) + (f"<filter>{filt}</filter>" if filt else "") + "</entity></fetch>"
    rc, out = pac(["org", "fetch", "--environment", env, "--xml", xml], timeout=120, retries=1)
    lines = [l for l in out.splitlines() if l.strip() and not l.startswith(BANNERS)]
    text = " ".join(lines)
    if "was not found" in text or "not found" in text.lower() and "Error" in text:
        return "missing", []
    if "No results returned" in text:
        return "ok", []
    if text.startswith("Error"):
        return "error:" + text[:120], []
    return "ok", [re.sub(r"\s+[0-9a-fA-F]{8}-[0-9a-fA-F-]{27}\s*$", "", l.strip()).strip() for l in lines[1:]]


def observe_target(env, code, union_ents, union_cols):
    pfx = "dvg" + code
    o = {"tables": {}, "columns": {}, "views": [], "envvars": [], "connrefs": [], "app": None}
    for e in union_ents:
        st, rows = fetch(env, f"{pfx}_{e}", [f"{pfx}_{e}id"])
        o["tables"][e] = st if st != "ok" else "exists"
    for e, c in union_cols:
        if o["tables"].get(e) != "exists":
            continue
        st, _ = fetch(env, f"{pfx}_{e}", [f"{pfx}_{c}"])
        o["columns"][f"{e}.{c}"] = "exists" if st == "ok" else st
    st, rows = fetch(env, "savedquery", ["name"], f"<condition attribute='name' operator='like' value='%s {code}'/>")
    o["views"] = sorted(r.strip() for r in rows)
    st, rows = fetch(env, "environmentvariabledefinition", ["schemaname"], f"<condition attribute='schemaname' operator='like' value='{pfx}_%'/>")
    o["envvars"] = sorted(r.strip() for r in rows)
    st, rows = fetch(env, "connectionreference", ["connectionreferencelogicalname"], f"<condition attribute='connectionreferencelogicalname' operator='like' value='{pfx}_%'/>")
    o["connrefs"] = sorted(r.strip() for r in rows)
    st, rows = fetch(env, "appmodule", ["uniquename"], f"<condition attribute='uniquename' operator='eq' value='{pfx}_app'/>")
    o["app"] = "exists" if rows else "absent"
    return o


# ---------------------------------------------------------------- pipeline
def source_stage(code, desc, muts, mode, handoff):
    res = {"code": code, "desc": desc, "mode": mode, "dev": {}}
    name = gen.solution_name(scenarios.base(code))
    rel = scenarios.releases(code, muts)
    wd = os.path.join(WORK, code)
    shutil.rmtree(wd, ignore_errors=True)
    os.makedirs(wd)
    try:
        for ver, spec in rel:
            gen.build(spec, os.path.join(wd, f"src-{ver}"))
            pack(os.path.join(wd, f"src-{ver}"), os.path.join(wd, f"R{ver}.zip"))
        log(f"[{code}] source: import release 1 ({desc})")
        res["dev"]["import_r1"] = import_result(SRC, os.path.join(wd, f"R{rel[0][0]}.zip"))
        if not res["dev"]["import_r1"]["ok"]:
            raise RuntimeError("source import of release 1 failed: " + str(res["dev"]["import_r1"]))
        if not export(SRC, name, os.path.join(wd, "M1.zip"), True):
            raise RuntimeError("managed export of release 1 failed")
        managed = [os.path.join(wd, "M1.zip")]
        for k, (ver, spec) in enumerate(rel[1:], start=2):
            if k == 2:
                log(f"[{code}] source: overwrite import of release {k} (no wrapper reset)")
                res["dev"][f"overwrite_r{k}"] = import_result(SRC, os.path.join(wd, f"R{ver}.zip"))
                if export(SRC, name, os.path.join(wd, f"over{k}.zip"), False):
                    res["dev"][f"observed_after_overwrite_r{k}"] = observe_dev(os.path.join(wd, f"over{k}.zip"))
            log(f"[{code}] source: wrapper reset + import release {k}")
            rc, out = pac(["solution", "delete", "--solution-name", name, "--environment", SRC], timeout=300)
            res["dev"][f"wrapper_delete_r{k}"] = "Solution deleted successfully" in out
            res["dev"][f"reset_import_r{k}"] = import_result(SRC, os.path.join(wd, f"R{ver}.zip"))
            if not res["dev"][f"reset_import_r{k}"]["ok"]:
                raise RuntimeError(f"source reset import of release {k} failed: " + str(res["dev"][f"reset_import_r{k}"]))
            if export(SRC, name, os.path.join(wd, f"unm{k}.zip"), False):
                res["dev"][f"observed_after_reset_r{k}"] = observe_dev(os.path.join(wd, f"unm{k}.zip"))
            if not export(SRC, name, os.path.join(wd, f"M{k}.zip"), True):
                raise RuntimeError(f"managed export of release {k} failed")
            managed.append(os.path.join(wd, f"M{k}.zip"))
        handoff.put((code, desc, muts, mode, name, rel, managed, res))
    except Exception as ex:  # noqa: BLE001
        res["fatal"] = f"source stage: {ex}"
        log(f"[{code}] SOURCE STAGE FAILED: {ex}")
        handoff.put((code, desc, muts, mode, name, rel, None, res))


def target_stage(item):
    code, desc, muts, mode, name, rel, managed, res = item
    res["target"] = {}
    if managed:
        try:
            ents = sorted({e["name"] for _, s in rel for e in s["entities"]})
            cols = sorted({(e["name"], c[1]) for _, s in rel for e in s["entities"] for c in e["cols"]})
            log(f"[{code}] target: install managed release 1")
            res["target"]["install_r1"] = import_result(TGT, managed[0])
            res["target"]["after_install_r1"] = observe_target(TGT, code, ents, cols)
            for k, zpath in enumerate(managed[1:], start=2):
                flags = ["--stage-and-upgrade"] if mode == "upgrade" else []
                log(f"[{code}] target: {'upgrade' if flags else 'plain update'} to release {k}")
                res["target"][f"{mode}_r{k}"] = import_result(TGT, zpath, flags)
                res["target"][f"after_{mode}_r{k}"] = observe_target(TGT, code, ents, cols)
                if not res["target"][f"{mode}_r{k}"]["ok"]:
                    break
        except Exception as ex:  # noqa: BLE001
            res["fatal"] = f"target stage: {ex}"
            log(f"[{code}] TARGET STAGE FAILED: {ex}")
    with open(os.path.join(RESULTS, f"{code}.json"), "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    log(f"[{code}] done -> results/{code}.json")


def main():
    todo = [s for s in scenarios.SCENARIOS if not ONLY or s[0] in ONLY]
    handoff = queue.Queue(maxsize=2)

    def producer():
        try:
            for code, desc, muts, mode in todo:
                source_stage(code, desc, muts, mode, handoff)
        except BaseException as ex:  # noqa: BLE001
            log(f"PRODUCER CRASHED: {ex!r}")
        finally:
            handoff.put(None)

    t = threading.Thread(target=producer, daemon=True)
    t.start()
    while True:
        item = handoff.get()
        if item is None:
            break
        target_stage(item)
    log("ALL SCENARIOS COMPLETE")


main()
