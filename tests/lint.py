#!/usr/bin/env python3
"""Static checks on a generated solution directory, derived from the gotchas in SKILL.md.
No Dataverse environment needed.

Usage: lint.py <solution_dir>      (the folder containing solution.xml and customizations.xml)
Exit code 0 = clean; 1 = at least one violation.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

SYSTEM_ATTRS = {"statecode", "statuscode", "createdon", "modifiedon", "createdby", "modifiedby", "ownerid",
                "owninguser", "owningbusinessunit", "owningteam", "versionnumber", "importsequencenumber",
                "overriddencreatedon", "timezoneruleversionnumber", "utcconversiontimezonecode"}
ENVVAR_TYPES = {"100000000", "100000001", "100000002", "100000003", "100000004", "100000005"}
GUID = re.compile(r"^\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}$")

d = sys.argv[1]
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def read(name):
    with open(os.path.join(d, name), encoding="utf-8") as f:
        return f.read()


# --- layout and well-formedness
for n in ("[Content_Types].xml", "solution.xml", "customizations.xml"):
    check(os.path.exists(os.path.join(d, n)), f"missing {n}")
xml_files = []
for base, _, files in os.walk(d):
    for fn in files:
        if fn.endswith(".xml"):
            xml_files.append(os.path.join(base, fn))
for p in xml_files:
    try:
        ET.parse(p)
    except ET.ParseError as ex:
        check(False, f"{os.path.relpath(p, d)} is not well-formed: {ex}")
if fails:
    for m in fails:
        print("FAIL:", m)
    sys.exit(1)

sol, cust = read("solution.xml"), read("customizations.xml")
sroot, croot = ET.fromstring(sol), ET.fromstring(cust)

# --- solution.xml (gotcha 1, unmanaged-only, prefix)
for a in ("version", "SolutionPackageVersion", "OrganizationVersion", "OrganizationSchemaType", "CRMServerServiceabilityVersion"):
    check(sroot.get(a) is not None, f"solution.xml root is missing attribute {a}")
check(sroot.findtext("SolutionManifest/Managed") == "0", "solution must be unmanaged (<Managed>0</Managed>)")
prefix = sroot.findtext("SolutionManifest/Publisher/CustomizationPrefix") or ""
check(re.fullmatch(r"[a-z]{2,8}", prefix) is not None, f"publisher prefix '{prefix}' must be 2-8 lowercase letters")
check(prefix != "new", "publisher prefix must not be 'new'")
check(sroot.findtext("SolutionManifest/Publisher/CustomizationOptionValuePrefix") not in (None, ""), "missing CustomizationOptionValuePrefix")
for a in ("OrganizationVersion", "OrganizationSchemaType", "CRMServerServiceabilityVersion"):
    check(croot.get(a) is not None, f"customizations.xml root is missing attribute {a}")

# --- entities (gotchas 3, 4, 5, 6, 7, 10, 11, 12)
entity_names = []
for ent in croot.findall("Entities/Entity"):
    name = ent.findtext("Name")
    entity_names.append(name)
    check(name.startswith(prefix + "_"), f"entity {name} does not start with prefix {prefix}_")
    e = ent.find("EntityInfo/entity")
    kids = [c.tag for c in e]
    check("attributes" in kids and "EntitySetName" in kids and kids.index("attributes") < kids.index("EntitySetName"),
          f"{name}: <attributes> must come before <EntitySetName>")
    prim = 0
    for a in e.findall("attributes/attribute"):
        ln = a.findtext("LogicalName")
        t = a.findtext("Type")
        check(ln not in SYSTEM_ATTRS, f"{name}.{ln}: system attributes must not be declared")
        check(t != "memo", f"{name}.{ln}: Type memo is not recognised; use nvarchar + Format textarea")
        check(a.findtext("ImeMode") in ("auto", "inactive", "disabled"), f"{name}.{ln}: ImeMode must be auto/inactive/disabled")
        check(a.find("displaynames/displayname") is not None, f"{name}.{ln}: labels must use <displaynames>/<displayname>")
        check(a.find("LocalizedNames") is None, f"{name}.{ln}: must not use <LocalizedNames> on attributes")
        for flag in ("IsCustomizable", "IsRenameable", "IsAuditEnabled", "IsSecured"):
            el = a.find(flag)
            check(el is None or len(el) == 0, f"{name}.{ln}: {flag} must be a simple integer, not a compound block")
        if "PrimaryName" in (a.findtext("DisplayMask") or ""):
            prim += 1
        for o in a.findall("optionset/options/option"):
            check(o.find("labels/label") is not None, f"{name}.{ln}: option labels must be lowercase <labels>/<label>")
        if t == "picklist":
            check(a.find("optionset/OptionSetType").text == "picklist", f"{name}.{ln}: picklist OptionSetType")
        if t == "bit":
            check(a.find("AppDefaultValue") is not None, f"{name}.{ln}: boolean needs <AppDefaultValue>")
            check(a.find("DefaultValue") is None, f"{name}.{ln}: boolean must not use <DefaultValue>")
            os_ = a.find("optionset")
            check(os_.get("Name") == f"{name}_{ln[len(prefix)+1:]}", f"{name}.{ln}: boolean optionset name must be entity-qualified, got {os_.get('Name')}")
            check(os_.findtext("OptionSetType") == "bit", f"{name}.{ln}: boolean OptionSetType must be bit")
            check({o.get("value") for o in os_.findall("options/option")} == {"0", "1"}, f"{name}.{ln}: boolean options must be values 0 and 1")
            check(os_.find("TrueOption") is None and os_.find("FalseOption") is None, f"{name}.{ln}: boolean must not use TrueOption/FalseOption")
    check(prim == 1, f"{name}: expected exactly one PrimaryName attribute, found {prim}")

    # --- views (View Templates section, gotchas 8, 9)
    sq = ent.find("SavedQueries")
    if sq is not None and len(sq):
        check(sq.find("savedqueries") is not None, f"{name}: <savedquery> elements must be wrapped in <savedqueries>")
        types = [x.findtext("querytype") for x in sq.iter("savedquery")]
        check("0" in types and "4" in types, f"{name}: needs a list view (querytype 0) and a Quick Find view (querytype 4)")
        for v in sq.iter("savedquery"):
            check(v.find("columnsetxml") is None, f"{name}: views must not contain <columnsetxml>")
            r = v.findtext("returnedtypecode")
            check(r is None or not r.isdigit(), f"{name}: returnedtypecode must be an entity name, not a number")
            check(GUID.match(v.findtext("savedqueryid") or "") is not None, f"{name}: bad savedqueryid")
            if v.findtext("querytype") == "4":
                check(v.find("fetchxml//filter[@isquickfindfields='1']") is not None, f"{name}: Quick Find view needs a filter with isquickfindfields='1'")

    # --- forms
    for ctl in ent.iter("control"):
        if ctl.get("classid", "").upper() == "{67FAC785-CD58-4F9F-ABB3-4B7DDC6ED5ED}":
            check(ctl.get("disabled") == "false", f"{name}.{ctl.get('id')}: boolean control needs disabled=\"false\"")

# --- root components: every entity is a type-1 root component
roots = {(r.get("type"), r.get("schemaName")): r.get("behavior") for r in sroot.findall("SolutionManifest/RootComponents/RootComponent")}
for n in entity_names:
    check(("1", n) in roots, f"entity {n} is not listed as a RootComponent type=1")
    check(roots.get(("1", n)) == "0", f"entity {n}: RootComponent behavior must be 0")

# --- app module
for app in croot.findall("AppModules/AppModule"):
    u = app.findtext("UniqueName")
    check(app.findtext("ClientType") == "4", f"{u}: ClientType must be 4")
    check(app.findtext("WebResourceId") == "953b9fac-1e5e-e611-80d6-00155ded156f", f"{u}: unexpected WebResourceId")
    check(app.find("appsettings/appsetting/value") is not None, f"{u}: AppChannel appsetting is required")
    check(app.find("AppModuleComponents") is not None and app.find("AppModuleRoleMaps") is not None, f"{u}: AppModuleComponents/AppModuleRoleMaps must be child elements")
    check(("62", u) in roots and ("80", u) in roots, f"{u}: needs RootComponent type 62 and 80")
    check(sroot.find("SolutionManifest/MissingDependencies/MissingDependency") is not None, f"{u}: needs MissingDependencies for the app framework")
for sa in croot.iter("SubArea"):
    check(sa.find("Titles") is None, f"SubArea {sa.get('Id')}: must be self-closing (no Titles)")
    check(sa.get("Icon") == "/_imgs/imagestrips/transparent_spacer.gif", f"SubArea {sa.get('Id')}: wrong Icon")
order = [c.tag for c in croot]
if "AppModules" in order:
    check(order.index("Languages") < order.index("AppModuleSiteMaps") < order.index("AppModules"), "AppModuleSiteMaps/AppModules must come after Languages")

# --- environment variables and connection references
envdir = os.path.join(d, "environmentvariabledefinitions")
if os.path.isdir(envdir):
    for n in os.listdir(envdir):
        p = os.path.join(envdir, n, "environmentvariabledefinition.xml")
        check(os.path.exists(p), f"environmentvariabledefinitions/{n}: missing environmentvariabledefinition.xml")
        if os.path.exists(p):
            r = ET.parse(p).getroot()
            check(r.get("schemaname") == n, f"environment variable folder {n} != schemaname {r.get('schemaname')}")
            check(n.startswith(prefix + "_"), f"environment variable {n} does not start with prefix")
            t = r.findtext("type")
            check(t in ENVVAR_TYPES, f"environment variable {n}: unknown type {t}")
            if t == "100000005":
                check(r.find("defaultvalue") is None, f"environment variable {n}: Secret must not have a defaultvalue")
            if t == "100000002" and r.findtext("defaultvalue") is not None:
                check(r.findtext("defaultvalue") in ("yes", "no"), f"environment variable {n}: Boolean default must be yes/no")
for cr in croot.findall("connectionreferences/connectionreference"):
    n = cr.get("connectionreferencelogicalname")
    check(n.startswith(prefix + "_"), f"connection reference {n} does not start with prefix")
    check((cr.findtext("connectorid") or "").startswith("/providers/Microsoft.PowerApps/apis/"), f"connection reference {n}: bad connectorid")
    check(order.index("connectionreferences") > order.index("EntityDataProviders") and order.index("connectionreferences") < order.index("Languages"),
          "connectionreferences must sit between EntityDataProviders and Languages")

# --- GUID uniqueness across all form/view ids
ids = re.findall(r'(?:<savedqueryid>|<formid>|\bid=")(\{[0-9A-Fa-f-]{36}\})', cust)
dupes = {i for i in ids if ids.count(i) > 1}
check(not dupes, f"duplicate GUIDs: {sorted(dupes)[:3]}")

for m in fails:
    print("FAIL:", m)
if not fails:
    print("lint OK:", os.path.basename(os.path.abspath(d)))
sys.exit(1 if fails else 0)
