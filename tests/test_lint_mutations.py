#!/usr/bin/env python3
"""Mutation tests for lint.py: break a known-good fixture one gotcha at a time and require lint to fail.

Usage: test_lint_mutations.py <good_solution_dir>   (use fixtures/DvgenFull/DvgenFull)
"""
import os
import shutil
import subprocess
import sys
import tempfile

SRC = sys.argv[1]
LINT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint.py")

# (name, file, old, new)  -- every mutation must make lint exit non-zero
MUTATIONS = [
    ("managed solution", "solution.xml", "<Managed>0</Managed>", "<Managed>1</Managed>"),
    ("prefix 'new'", "solution.xml", "<CustomizationPrefix>dvgen</CustomizationPrefix>", "<CustomizationPrefix>new</CustomizationPrefix>"),
    ("prefix with digit", "solution.xml", "<CustomizationPrefix>dvgen</CustomizationPrefix>", "<CustomizationPrefix>dv1gen</CustomizationPrefix>"),
    ("missing SolutionPackageVersion", "solution.xml", 'SolutionPackageVersion="9.2"', ""),
    ("entity not a root component", "solution.xml", '<RootComponent type="1" schemaName="dvgen_task" behavior="0" />', ""),
    ("root component behavior=1", "solution.xml", '<RootComponent type="1" schemaName="dvgen_task" behavior="0" />', '<RootComponent type="1" schemaName="dvgen_task" behavior="1" />'),
    ("memo type", "customizations.xml", "<Type>nvarchar</Type><Name>dvgen_description</Name>", "<Type>memo</Type><Name>dvgen_description</Name>"),
    ("system attribute declared", "customizations.xml", '<attribute PhysicalName="dvgen_hours">', '<attribute PhysicalName="statecode"><Type>state</Type><Name>statecode</Name><LogicalName>statecode</LogicalName></attribute><attribute PhysicalName="dvgen_hours">'),
    ("ImeMode integer", "customizations.xml", "<ImeMode>inactive</ImeMode>", "<ImeMode>1</ImeMode>"),
    ("compound IsCustomizable", "customizations.xml", "<IsRenameable>1</IsRenameable>", "<IsRenameable><Value>1</Value><CanModify>1</CanModify></IsRenameable>"),
    ("LocalizedNames on attribute", "customizations.xml", "<displaynames><displayname description=\"Hours\"", "<LocalizedNames/><displaynames><displayname description=\"Hours\""),
    ("boolean DefaultValue", "customizations.xml", "<AppDefaultValue>0</AppDefaultValue>", "<DefaultValue>0</DefaultValue>"),
    ("boolean OptionSetType bool", "customizations.xml", "<OptionSetType>bit</OptionSetType>", "<OptionSetType>bool</OptionSetType>"),
    ("boolean unqualified optionset", "customizations.xml", '<optionset Name="dvgen_task_done">', '<optionset Name="dvgen_done">'),
    ("boolean control without disabled=false", "customizations.xml", ' disabled="false"', ""),
    ("views not wrapped", "customizations.xml", "<savedqueries>", ""),
    ("view has columnsetxml", "customizations.xml", "<querytype>0</querytype>", "<querytype>0</querytype><columnsetxml><columnset/></columnsetxml>"),
    ("numeric returnedtypecode", "customizations.xml", "<querytype>4</querytype>", "<querytype>4</querytype><returnedtypecode>10001</returnedtypecode>"),
    ("quick find without isquickfindfields", "customizations.xml", ' isquickfindfields="1"', ""),
    ("no quick find view", "customizations.xml", "<querytype>4</querytype>", "<querytype>2</querytype>"),
    ("attributes after entity props", "customizations.xml", "<EntitySetName>dvgen_tasks</EntitySetName>", "</attributes><EntitySetName>dvgen_tasks</EntitySetName><attributes>"),
    ("app ClientType wrong", "customizations.xml", "<ClientType>4</ClientType>", "<ClientType>2</ClientType>"),
    ("app missing appsettings", "customizations.xml", '<appsettings><appsetting settingdefinitionid.uniquename="AppChannel"><iscustomizable>1</iscustomizable><value>1</value></appsetting></appsettings>', ""),
    ("SubArea has Titles", "customizations.xml", 'PassParams="false" Sku="All,OnPremise,Live,SPLA" />', 'PassParams="false" Sku="All,OnPremise,Live,SPLA"><Titles/></SubArea>'),
    ("malformed xml", "customizations.xml", "</Entities>", ""),
]


def run(path):
    return subprocess.run([sys.executable, "-I", LINT, path], capture_output=True, text=True)


base = run(SRC)
if base.returncode != 0:
    print("baseline fixture does not pass lint:\n" + base.stdout)
    sys.exit(2)

escaped = []
for name, fname, old, new in MUTATIONS:
    tmp = tempfile.mkdtemp()
    try:
        dst = os.path.join(tmp, "s")
        shutil.copytree(SRC, dst)
        p = os.path.join(dst, fname)
        text = open(p, encoding="utf-8").read()
        if old not in text:
            print(f"SKIP  {name}: pattern not found in {fname} (update the mutation)")
            escaped.append(name)
            continue
        open(p, "w", encoding="utf-8").write(text.replace(old, new, 1))
        r = run(dst)
        if r.returncode == 0:
            print(f"ESCAPED  {name}: lint passed a broken solution")
            escaped.append(name)
        else:
            print(f"caught   {name}")
    finally:
        shutil.rmtree(tmp)

print(f"\n{len(MUTATIONS) - len(escaped)}/{len(MUTATIONS)} mutations caught")
sys.exit(1 if escaped else 0)
