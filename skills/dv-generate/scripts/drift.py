#!/usr/bin/env python3
"""Compare a saved (source-controlled) solution folder with an unmanaged export from the dev environment.

  drift.py <repo_dir> <dev_dir>              what differs, and on which side
  drift.py <repo_dir> <dev_dir> --manual     only the manual steps still needed in dev before exporting managed

<repo_dir> and <dev_dir> are folders containing solution.xml and customizations.xml (the root of the zip).
Exit code 0 = identical on everything compared; 1 = differences found.

Only components dv-generate manages are compared: custom tables, their custom columns (publisher prefix),
option values, views, forms, environment variables, connection references and app modules. Platform-created
system columns and system views are ignored.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

SYSTEM_VIEW = re.compile(r"^(Active|Inactive|My) .+|.+ (Advanced Find View|Associated View|Lookup View)$|^Quick Find Active .+")


def _guid(s):
    return (s or "").strip("{} ").lower()


def load(d):
    s = ET.parse(os.path.join(d, "solution.xml")).getroot()
    c = ET.parse(os.path.join(d, "customizations.xml")).getroot()
    prefix = s.findtext("SolutionManifest/Publisher/CustomizationPrefix") or ""
    out = {"prefix": prefix, "version": s.findtext("SolutionManifest/Version"), "tables": {}, "envvars": {}, "connrefs": {}, "apps": {}}
    for e in c.findall("Entities/Entity"):
        name = e.findtext("Name")
        t = {"attrs": {}, "views": {}, "forms": {}}
        for a in e.findall("EntityInfo/entity/attributes/attribute"):
            ln = a.findtext("LogicalName")
            if not ln.startswith(prefix + "_") or ln == name + "id":
                continue
            dn = a.find("displaynames/displayname")
            opts = {o.get("value"): (o.find("labels/label").get("description") if o.find("labels/label") is not None else "")
                    for o in a.findall("optionset/options/option")} if a.findtext("Type") == "picklist" else {}
            t["attrs"][ln] = {"type": a.findtext("Type"), "label": dn.get("description") if dn is not None else None, "options": opts}
        for v in e.findall("SavedQueries//savedquery"):
            ln = v.find("LocalizedNames/LocalizedName")
            vname = ln.get("description") if ln is not None else ""
            if SYSTEM_VIEW.match(vname):
                continue
            refs = {x.get("name") for x in v.iter("cell")} | {x.get("name") for x in v.iter("attribute")} | {x.get("attribute") for x in v.iter("condition")}
            t["views"][_guid(v.findtext("savedqueryid"))] = vname
            t.setdefault("viewrefs", {})[_guid(v.findtext("savedqueryid"))] = {r for r in refs if r}
        for f in e.findall("FormXml//systemform"):
            ln = f.find("LocalizedNames/LocalizedName")
            t["forms"][_guid(f.findtext("formid"))] = {
                "name": ln.get("description") if ln is not None else "",
                "controls": {x.get("id") for x in f.iter("control") if x.get("id")}}
        out["tables"][name] = t
    envd = os.path.join(d, "environmentvariabledefinitions")
    if os.path.isdir(envd):
        for n in sorted(os.listdir(envd)):
            p = os.path.join(envd, n, "environmentvariabledefinition.xml")
            if os.path.exists(p):
                r = ET.parse(p).getroot()
                out["envvars"][r.get("schemaname")] = {"type": r.findtext("type"), "default": r.findtext("defaultvalue")}
    for x in c.findall("connectionreferences/connectionreference"):
        out["connrefs"][x.get("connectionreferencelogicalname")] = x.findtext("connectorid")
    for a in c.findall("AppModules/AppModule"):
        out["apps"][a.findtext("UniqueName")] = sorted(y.get("schemaName") for y in a.findall("AppModuleComponents/AppModuleComponent") if y.get("type") == "1")
    return out


def compare(repo, dev):
    """List of (kind, side, text). side: 'dev_only' | 'repo_only' | 'changed'."""
    f = []

    def sets(kind, r, d, fmt=lambda x: x):
        for k in sorted(set(d) - set(r)):
            f.append((kind, "dev_only", fmt(k)))
        for k in sorted(set(r) - set(d)):
            f.append((kind, "repo_only", fmt(k)))

    sets("table", repo["tables"], dev["tables"])
    for tn in sorted(set(repo["tables"]) & set(dev["tables"])):
        r, d = repo["tables"][tn], dev["tables"][tn]
        sets("column", r["attrs"], d["attrs"], lambda k, tn=tn: f"{tn}.{k}")
        for k in sorted(set(r["attrs"]) & set(d["attrs"])):
            ra, da = r["attrs"][k], d["attrs"][k]
            if ra["type"] != da["type"]:
                f.append(("column type", "changed", f"{tn}.{k}: repo {ra['type']}, dev {da['type']}"))
            if ra["label"] != da["label"]:
                f.append(("column label", "changed", f"{tn}.{k}: repo '{ra['label']}', dev '{da['label']}'"))
            for v in sorted(set(da["options"]) - set(ra["options"])):
                f.append(("option", "dev_only", f"{tn}.{k}: {v} ('{da['options'][v]}')"))
            for v in sorted(set(ra["options"]) - set(da["options"])):
                f.append(("option", "repo_only", f"{tn}.{k}: {v} ('{ra['options'][v]}')"))
            for v in sorted(set(ra["options"]) & set(da["options"])):
                if ra["options"][v] != da["options"][v]:
                    f.append(("option label", "changed", f"{tn}.{k}: {v} repo '{ra['options'][v]}', dev '{da['options'][v]}'"))
        for g in sorted(set(d["views"]) - set(r["views"])):
            f.append(("view", "dev_only", f"{tn}: '{d['views'][g]}'"))
        for g in sorted(set(r["views"]) - set(d["views"])):
            f.append(("view", "repo_only", f"{tn}: '{r['views'][g]}'"))
        for g in sorted(set(r["views"]) & set(d["views"])):
            if r["views"][g] != d["views"][g]:
                f.append(("view name", "changed", f"{tn}: repo '{r['views'][g]}', dev '{d['views'][g]}'"))
        for g in sorted(set(r["views"]) & set(d["views"])):
            rr, dr = r.get("viewrefs", {}).get(g, set()), d.get("viewrefs", {}).get(g, set())
            if rr != dr:
                f.append(("view columns", "changed", f"{tn} view '{r['views'][g]}': dev also uses {sorted(dr - rr)}, dev lacks {sorted(rr - dr)}"))
        for g in sorted(set(d["forms"]) - set(r["forms"])):
            f.append(("form", "dev_only", f"{tn}: '{d['forms'][g]['name']}'"))
        for g in sorted(set(r["forms"]) - set(d["forms"])):
            f.append(("form", "repo_only", f"{tn}: '{r['forms'][g]['name']}'"))
        for g in sorted(set(r["forms"]) & set(d["forms"])):
            rc, dc = r["forms"][g]["controls"], d["forms"][g]["controls"]
            if rc != dc:
                f.append(("form fields", "changed", f"{tn} form '{r['forms'][g]['name']}': dev adds {sorted(dc - rc)}, dev lacks {sorted(rc - dc)}"))
    sets("env var", repo["envvars"], dev["envvars"])
    for k in sorted(set(repo["envvars"]) & set(dev["envvars"])):
        if repo["envvars"][k] != dev["envvars"][k]:
            f.append(("env var value", "changed", f"{k}: repo {repo['envvars'][k]}, dev {dev['envvars'][k]}"))
    sets("connection reference", repo["connrefs"], dev["connrefs"])
    sets("app", repo["apps"], dev["apps"])
    for k in sorted(set(repo["apps"]) & set(dev["apps"])):
        if repo["apps"][k] != dev["apps"][k]:
            f.append(("app tables", "changed", f"{k}: repo {repo['apps'][k]}, dev {dev['apps'][k]}"))
    return f


MANUAL = {
    "column": "make.powerapps.com > Tables > {t} > Columns > {c} > Delete from this environment (deletes that column's data in dev)",
    "view": "make.powerapps.com > Tables > {t} > Views > {c} > Delete",
    "form": "make.powerapps.com > Tables > {t} > Forms > {c} > Delete",
    "option": "make.powerapps.com > Tables > {t} > Columns > {col} > edit the choices and remove option {c}",
}


def warnings_for(findings, repo):
    """Risks of the managed upgrade that follows, from what the matrix tests showed."""
    w = []
    tables = [t for k, s, t in findings if k == "table" and s == "dev_only"]
    cols = [t for k, s, t in findings if k == "column" and s == "dev_only"]
    if tables and repo["apps"]:
        w.append(f"Table(s) {', '.join(tables)} are being removed but the saved XML still contains an app ({', '.join(repo['apps'])}). "
                 "A managed upgrade fails while the app remains ('component cannot be deleted because it is referenced by 1 other components'). "
                 "Remove the app in the same release (it can be added back in the next one).")
    if tables:
        w.append("Removing a table in a managed upgrade deletes the table and ALL ITS ROWS in the target environment. Back up the data first.")
    if cols:
        w.append("After you delete a column in dev, a managed upgrade removes it from the target, and is expected to delete that column's data (data effect not tested). A plain update (not an upgrade) removes nothing.")
    return w


def manual_steps(findings):
    """What the user must still do in dev because the saved XML no longer has it. Returns (required, handled)."""
    required, handled = [], []
    cols = [t.split(".", 1)[1] for k, s, t in findings if k == "column" and s == "dev_only"]
    used = sorted({c for c in cols for k, s, t in findings if k in ("form fields", "view columns") and c in t})
    if used:
        required.append(
            f"Dev still has {', '.join(used)} on a form or view that the saved XML no longer uses, and Dataverse blocks deleting a column while a form or view uses it "
            "('Object dependencies exist'). Re-import the new zip into dev first: `pac solution import --path <zip> --environment <dev> --publish-changes`, "
            "then run pull.py again and check the form and view differences are gone.")
    for kind, side, text in findings:
        if side != "dev_only":
            continue
        if kind == "column":
            t, c = text.split(".", 1)
            required.append(f"Delete column '{c}' on table '{t}'. " + MANUAL["column"].format(t=t, c=c))
        elif kind == "view":
            t, c = text.split(": ", 1)
            required.append(f"Delete view {c} on table '{t}'. " + MANUAL["view"].format(t=t, c=c))
        elif kind == "form":
            t, c = text.split(": ", 1)
            required.append(f"Delete form {c} on table '{t}'. " + MANUAL["form"].format(t=t, c=c))
        elif kind == "option":
            tc, v = text.split(": ", 1)
            t, col = tc.split(".", 1)
            required.append(f"Remove option {v} from '{col}' on table '{t}'. " + MANUAL["option"].format(t=t, col=col, c=v.split(' ')[0]))
        elif kind == "table":
            handled.append(f"Table '{text}' is not in the saved XML: re-import after deleting the solution wrapper (unmanaged solutions only) to drop it from the solution. The table and its data stay in dev until you delete it.")
        elif kind in ("env var", "connection reference", "app"):
            handled.append(f"{kind.capitalize()} '{text}' is not in the saved XML: re-importing after deleting the solution wrapper drops it from the solution.")
    return required, handled


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    repo, dev = load(args[0]), load(args[1])
    findings = compare(repo, dev)
    if "--manual" in sys.argv:
        required, handled = manual_steps(findings)
        warns = warnings_for(findings, repo)
        if not required and not handled and not warns:
            print("No manual steps needed in dev.")
            return 0
        if required:
            print("Manual steps needed in dev BEFORE you export as managed (otherwise these stay in the solution):")
            for i, r in enumerate(required, 1):
                print(f"  {i}. {r}")
        if handled:
            print("Handled by re-importing after deleting the unmanaged solution wrapper:")
            for h in handled:
                print("  - " + h)
        if warns:
            print("Warnings for the managed upgrade:")
            for w in warns:
                print("  ! " + w)
        return 1 if (required or warns) else 0
    if not findings:
        print("No drift: the saved XML and the dev export agree on tables, columns, options, views, forms, env vars, connection references and apps.")
        return 0
    labels = {"dev_only": "In dev, not in the saved XML", "repo_only": "In the saved XML, not in dev", "changed": "Different between the two"}
    for side in ("dev_only", "repo_only", "changed"):
        rows = [(k, t) for k, s, t in findings if s == side]
        if rows:
            print(f"\n{labels[side]}:")
            for k, t in rows:
                print(f"  [{k}] {t}")
    return 1


sys.exit(main())
