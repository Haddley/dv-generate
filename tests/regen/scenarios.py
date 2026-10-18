"""Regeneration scenarios: a base spec (release 1) and a mutation per scenario (release 2, and 3 where needed).

Each scenario gets its own two-letter code, so its publisher prefix ('dvg' + code), solution name and
components can never collide with another scenario. That removes the need to reset the environments
between scenarios.
"""
import copy


def base(code):
    return {
        "code": code,
        "version": "1.0.0.0",
        "entities": [
            {"name": "alpha", "display": "Alpha", "views": ["all", "qf"], "cols": [
                ("text", "name", "Name"),
                ("decimal", "amount", "Amount"),
                ("picklist", "status", "Status", ["a", "b", "c"]),
                ("bool", "flag", "Flag"),
            ]},
            {"name": "beta", "display": "Beta", "views": ["all", "qf"], "cols": [
                ("text", "name", "Name"),
                ("int", "qty", "Quantity"),
            ]},
        ],
        "app": True,
        "envvars": [("ev1", 100000000, "x"), ("ev2", 100000002, "yes")],
        "connrefs": ["cr1"],
    }


def alpha(spec):
    return spec["entities"][0]


def drop_entity(spec, name):
    spec["entities"] = [e for e in spec["entities"] if e["name"] != name]


# Each scenario: (code, description, [mutation functions applied to produce release 2, release 3, ...],
#                 upgrade_mode) where upgrade_mode is 'upgrade' (default) or 'update'.
def add_column(s):
    alpha(s)["cols"].append(("text", "extra", "Extra"))


def remove_column(s):
    alpha(s)["cols"] = [c for c in alpha(s)["cols"] if c[1] != "amount"]


def change_label(s):
    alpha(s)["cols"][1] = ("decimal", "amount", "Amount renamed")


def add_option(s):
    c = alpha(s)["cols"][2]
    alpha(s)["cols"][2] = (c[0], c[1], c[2], c[3] + ["d"])


def remove_option(s):
    c = alpha(s)["cols"][2]
    alpha(s)["cols"][2] = (c[0], c[1], c[2], [x for x in c[3] if x != "c"])


def change_type(s):
    alpha(s)["cols"][1] = ("int", "amount", "Amount")


def add_table(s):
    s["entities"].append({"name": "gamma", "display": "Gamma", "views": ["all", "qf"], "cols": [("text", "name", "Name")]})


def remove_table_keep_app(s):
    drop_entity(s, "beta")


def remove_table_and_app(s):
    drop_entity(s, "beta")
    s["app"] = False


def readd_app(s):
    s["app"] = True


def remove_view(s):
    alpha(s)["views"] = ["qf"]


def add_envvar_connref(s):
    s["envvars"].append(("ev3", 100000001, "5"))
    s["connrefs"].append("cr2")


def remove_envvar_connref(s):
    s["envvars"] = [e for e in s["envvars"] if e[0] != "ev2"]
    s["connrefs"] = []


def remove_app_only(s):
    s["app"] = False


def change_envvar_default(s):
    s["envvars"][0] = ("ev1", 100000000, "changed")


SCENARIOS = [
    ("aa", "add a column", [add_column], "upgrade"),
    ("ab", "remove a column", [remove_column], "upgrade"),
    ("ac", "change a column label", [change_label], "upgrade"),
    ("ad", "add a picklist option", [add_option], "upgrade"),
    ("ae", "remove a picklist option", [remove_option], "upgrade"),
    ("af", "change a column type (decimal -> int)", [change_type], "upgrade"),
    ("ag", "add a table", [add_table], "upgrade"),
    ("ah", "remove a table, keep the app", [remove_table_keep_app], "upgrade"),
    ("ai", "remove a table and the app together", [remove_table_and_app], "upgrade"),
    ("aj", "remove table and app, then re-add the app", [remove_table_and_app, readd_app], "upgrade"),
    ("ak", "remove a view", [remove_view], "upgrade"),
    ("al", "add an env var and a connection reference", [add_envvar_connref], "upgrade"),
    ("am", "remove an env var and a connection reference", [remove_envvar_connref], "upgrade"),
    ("an", "change an env var default", [change_envvar_default], "upgrade"),
    ("ao", "remove only the app", [remove_app_only], "upgrade"),
    ("ap", "remove table and app: plain UPDATE instead of upgrade", [remove_table_and_app], "update"),
]


def releases(code, mutations):
    """[(version, spec)] for release 1..n of a scenario."""
    out = []
    spec = base(code)
    out.append((spec["version"], copy.deepcopy(spec)))
    for i, m in enumerate(mutations, start=1):
        spec = copy.deepcopy(spec)
        m(spec)
        spec["version"] = f"1.0.0.{i}"
        out.append((spec["version"], copy.deepcopy(spec)))
    return out
