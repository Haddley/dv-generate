#!/usr/bin/env python3
"""Print a readable summary of tests/regen/results/*.json.

For every scenario it compares what release 2 SHOULD contain (from the spec) with what each path actually
produced:
  dev overwrite : plain unmanaged import of release 2 over release 1 (no wrapper reset)
  dev reset     : solution wrapper deleted, release 2 imported (solution == zip)
  target        : managed upgrade (or update) in the second environment
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scenarios  # noqa: E402


def expected(code, muts):
    rel = scenarios.releases(code, muts)
    return rel[-1][1], rel


def spec_sets(spec):
    pfx = "dvg" + spec["code"]
    ents = {f"{pfx}_{e['name']}" for e in spec["entities"]}
    cols = {f"{pfx}_{e['name']}.{pfx}_{c[1]}" for e in spec["entities"] for c in e["cols"]}
    types = {f"{pfx}_{e['name']}.{pfx}_{c[1]}": {"text": "nvarchar", "decimal": "decimal", "int": "int", "picklist": "picklist", "bool": "bit"}[c[0]]
             for e in spec["entities"] for c in e["cols"]}
    opts = {f"{pfx}_{e['name']}.{pfx}_{c[1]}": len(c[3]) for e in spec["entities"] for c in e["cols"] if c[0] == "picklist"}
    views = {f"{'All ' if k == 'all' else 'Quick Find '}{e['display']}s {spec['code']}" for e in spec["entities"] for k in e.get("views", [])}
    env = {f"{pfx}_{n}" for n, _, _ in spec.get("envvars", [])}
    cr = {f"{pfx}_{n}" for n in spec.get("connrefs", [])}
    return ents, cols, types, opts, views, env, cr, bool(spec.get("app"))


def diff_dev(obs, spec):
    if not obs:
        return ["no observation"]
    ents, cols, types, opts, views, env, cr, app = spec_sets(spec)
    pfx = "dvg" + spec["code"]
    have_e = set(obs["entities"])
    have_c = {f"{e}.{a}" for e, v in obs["entities"].items() for a in v["attrs"] if a.startswith(pfx + "_") and a != e + "id"}
    have_v = {v for e in obs["entities"].values() for v in e["views"]}
    have_env = {e["name"] for e in obs["envvars"]}
    out = []
    for lbl, want, got in (("tables", ents, have_e), ("columns", cols, have_c), ("views", views, have_v), ("env vars", env, have_env), ("conn refs", cr, set(obs["connrefs"]))):
        if want - got:
            out.append(f"missing {lbl}: {sorted(want - got)}")
        if got - want:
            out.append(f"extra {lbl} still present: {sorted(got - want)}")
    if app != bool(obs["apps"]):
        out.append(f"app {'missing' if app else 'still present'}")
    for k, t in types.items():
        e, a = k.split(".")
        if e in obs["entities"] and a in obs["entities"][e]["attrs"] and obs["entities"][e]["attrs"][a] != t:
            out.append(f"type of {k} is {obs['entities'][e]['attrs'][a]}, spec says {t}")
    for e in spec["entities"]:
        for c in e["cols"]:
            en, an = f"{pfx}_{e['name']}", f"{pfx}_{c[1]}"
            got = obs["entities"].get(en, {}).get("labels", {}).get(an)
            if got is not None and got != c[2]:
                out.append(f"label of {en}.{an} is '{got}', spec says '{c[2]}'")
    for k, n in opts.items():
        e, a = k.split(".")
        if e in obs["entities"] and len(obs["entities"][e]["options"].get(a, [])) != n:
            out.append(f"{k} has {len(obs['entities'][e]['options'].get(a, []))} options, spec says {n}")
    return out or ["matches the regenerated spec"]


def diff_target(obs, spec, rel_specs):
    if not obs:
        return ["no observation"]
    ents, cols, types, opts, views, env, cr, app = spec_sets(spec)
    pfx = "dvg" + spec["code"]
    out = []
    have_e = {f"{pfx}_{e}" for e, s in obs["tables"].items() if s == "exists"}
    have_c = {f"{pfx}_{k.split('.')[0]}.{pfx}_{k.split('.')[1]}" for k, s in obs["columns"].items() if s == "exists"}
    first = lambda x: re.sub(r"\s+[0-9a-fA-F]{8}-[0-9a-fA-F-]{27}\s*$", "", x.strip()).strip()
    have_v = {first(v) for v in obs["views"]}
    have_env = {first(x) for x in obs["envvars"]}
    have_cr = {first(x) for x in obs["connrefs"]}
    for lbl, want, got in (("tables", ents, have_e), ("columns", cols, have_c), ("views", views, have_v), ("env vars", env, have_env), ("conn refs", cr, have_cr)):
        if want - got:
            out.append(f"missing {lbl}: {sorted(want - got)}")
        if got - want:
            out.append(f"extra {lbl} still present: {sorted(got - want)}")
    if app != (obs["app"] == "exists"):
        out.append(f"app {'missing' if app else 'still present'}")
    return out or ["matches the regenerated spec"]


def main():
    files = sorted(glob.glob(os.path.join(HERE, "results", "*.json")))
    if not files:
        print("no results yet")
        return
    codes = {s[0]: s for s in scenarios.SCENARIOS}
    for f in files:
        r = json.load(open(f))
        code = r["code"]
        _, desc, muts, mode = codes[code]
        spec, rel = expected(code, muts)
        print(f"\n=== {code}: {desc}  [{mode}]")
        if r.get("fatal"):
            print("  FATAL:", r["fatal"])
        d = r.get("dev", {})
        for k in sorted(k for k in d if k.startswith(("overwrite_", "reset_import_"))):
            v = d[k]
            print(f"  dev {k}: {'ok' if v['ok'] else 'FAILED ' + str(v['error'])}")
        for k in sorted(k for k in d if k.startswith("observed_after_")):
            label = k.replace("observed_after_", "dev after ")
            print(f"  {label}: {'; '.join(diff_dev(d[k], spec))}")
        t = r.get("target", {})
        for k in sorted(t):
            if k.startswith(("install_", "upgrade_", "update_")):
                v = t[k]
                print(f"  target {k}: {'ok' if v['ok'] else 'FAILED ' + str(v['error'])}")
            elif k.startswith("after_") and k != "after_install_r1":
                n = int(k.rsplit("_r", 1)[1])
                print(f"  target {k.replace('_', ' ')}: {'; '.join(diff_target(t[k], rel[n - 1][1], rel))}")


main()
