#!/usr/bin/env python3
"""Compare a fixture (what dv-generate produced) with an unpacked export of the same solution
(what Dataverse actually stored). Fails if anything we generated did not survive the round trip.

Usage: verify_export.py <fixture_dir> <export_dir> [--allow-duplicate-views]
Exit code 0 = all checks pass; 1 = at least one mismatch (details on stdout).
"""
import os
import sys
import xml.etree.ElementTree as ET


def load(path):
    return ET.parse(path).getroot()


def entities(root):
    out = {}
    for e in root.findall("Entities/Entity"):
        name = e.findtext("Name")
        out[name] = e
    return out


def attrs(entity):
    out = {}
    for a in entity.findall("EntityInfo/entity/attributes/attribute"):
        out[a.findtext("LogicalName") or a.findtext("Name")] = a
    return out


def view_names(entity):
    names = []
    for sq in entity.findall("SavedQueries//savedquery"):
        ln = sq.find("LocalizedNames/LocalizedName")
        if ln is not None:
            names.append(ln.get("description"))
    return names


def view_guids(entity):
    """savedquery id (lowercase, no braces) -> view name"""
    out = {}
    for sq in entity.findall("SavedQueries//savedquery"):
        ln = sq.find("LocalizedNames/LocalizedName")
        gid = (sq.findtext("savedqueryid") or "").strip("{}").lower()
        out.setdefault(gid, []).append(ln.get("description") if ln is not None else None)
    return out


def form_names(entity):
    names = []
    for sf in entity.findall("FormXml//systemform"):
        ln = sf.find("LocalizedNames/LocalizedName")
        if ln is not None:
            names.append(ln.get("description"))
    return names


def options(attr):
    out = {}
    for o in attr.findall("optionset/options/option"):
        lab = o.find("labels/label")
        out[o.get("value")] = lab.get("description") if lab is not None else None
    return out


def envvars(base):
    out = {}
    d = os.path.join(base, "environmentvariabledefinitions")
    if not os.path.isdir(d):
        return out
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n, "environmentvariabledefinition.xml")
        if os.path.exists(p):
            r = load(p)
            out[r.get("schemaname")] = (r.findtext("type"), r.findtext("defaultvalue"))
    return out


def connrefs(root):
    return {c.get("connectionreferencelogicalname"): c.findtext("connectorid")
            for c in root.findall("connectionreferences/connectionreference")}


def appmodules(root):
    return {a.findtext("UniqueName"): sorted(c.get("schemaName") for c in a.findall("AppModuleComponents/AppModuleComponent"))
            for a in root.findall("AppModules/AppModule")}


def main():
    fix, exp = sys.argv[1], sys.argv[2]
    allow_dupes = "--allow-duplicate-views" in sys.argv
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    f, e = load(os.path.join(fix, "customizations.xml")), load(os.path.join(exp, "customizations.xml"))
    fe, ee = entities(f), entities(e)
    for name, fent in fe.items():
        check(name in ee, f"entity {name} missing from export")
        if name not in ee:
            continue
        xent = ee[name]
        fa, xa = attrs(fent), attrs(xent)
        for an, aelem in fa.items():
            check(an in xa, f"{name}.{an}: attribute missing from export")
            if an not in xa:
                continue
            ftype, xtype = aelem.findtext("Type"), xa[an].findtext("Type")
            fformat = aelem.findtext("Format")
            check(xtype is not None, f"{name}.{an}: export has no Type")
            check(ftype == xtype, f"{name}.{an}: type {ftype} exported as {xtype}")
            if fformat:
                check(fformat == xa[an].findtext("Format"), f"{name}.{an}: format {fformat} exported as {xa[an].findtext('Format')}")
            if ftype in ("picklist", "bit"):
                fo, xo = options(aelem), options(xa[an])
                check(fo == xo, f"{name}.{an}: options {fo} != exported {xo}")
        # custom views and forms
        # Views are matched by GUID: each GUID we generated must come back exactly once.
        fg, xg = view_guids(fent), view_guids(xent)
        for gid, names in fg.items():
            n = sum(len(v) for k, v in xg.items() if k == gid)
            check(n >= 1, f"{name}: view '{names[0]}' ({gid}) missing from export (silently dropped on import?)")
            check(n <= 1, f"{name}: view '{names[0]}' ({gid}) appears {n} times")
        ours = {n for v in fg.values() for n in v}
        foreign = [(g_, n_) for g_, v in xg.items() if g_ not in fg for n_ in v if n_ in ours]
        if foreign and not allow_dupes:
            print(f"WARN: {name}: {len(foreign)} view(s) with our names but different GUIDs exist in the environment "
                  f"(left over from earlier imports with other GUIDs; delete the table and re-import to clear)")
        xf = form_names(xent)
        for fn in set(form_names(fent)):
            check(fn in xf, f"{name}: form '{fn}' missing from export")

    # option set / primary name sanity from the export itself
    for name, xent in ee.items():
        if name in fe:
            prim = [a for a in attrs(xent).values() if "PrimaryName" in (a.findtext("DisplayMask") or "")]
            check(len(prim) == 1, f"{name}: expected exactly one primary name attribute, found {len(prim)}")

    fv, xv = envvars(fix), envvars(exp)
    for k, v in fv.items():
        check(k in xv, f"environment variable {k} missing from export")
        if k in xv:
            check(v == xv[k], f"environment variable {k}: {v} != exported {xv[k]}")
    fc, xc = connrefs(f), connrefs(e)
    for k, v in fc.items():
        check(k in xc, f"connection reference {k} missing from export")
        if k in xc:
            check(v == xc[k], f"connection reference {k}: connector {v} != exported {xc[k]}")
    fa_, xa_ = appmodules(f), appmodules(e)
    for k, v in fa_.items():
        check(k in xa_, f"app module {k} missing from export")
        if k in xa_:
            check(all(c in xa_[k] for c in v), f"app module {k}: components {v} not all in export {xa_[k]}")

    sol = load(os.path.join(exp, "solution.xml"))
    check(sol.findtext("SolutionManifest/Managed") == "0", "exported solution is not unmanaged")

    for m in fails:
        print("FAIL:", m)
    if not fails:
        print("round trip OK:", len(fe), "entities,", sum(len(attrs(x)) for x in fe.values()), "attributes,",
              len(fv), "env vars,", len(fc), "connection refs,", len(fa_), "app modules")
    return 1 if fails else 0


sys.exit(main())
