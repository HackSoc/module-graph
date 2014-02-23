#!/usr/bin/env python3

"""graph.py render a module dependency graph

Usage:
  graph.py [<modules-json>] [-P] [-C] [-S] [-R] [-O] [-p <programme>] [-r <rankdir>] [--] [<module>...]

Options:
  -h --help       Show this text.
  <modules-json>  The modules.json file to use [default: "./modules.json"].
  -P              Don't show prerequisites
  -C              Don't show corequisites
  -S              Don't show suggestions
  -R              Don't show required modules
  -O              Don't show orphaned modules (those which don't contribute to any relationships)
  -p <programme>  Only render the given programme.
  -r <rankdir>    Rank direction (LR or TB) [default: LR].
  <module>...     List of modules to render, default all in programme(s).
"""

import json
import docopt
from itertools import chain

DEFAULT_MODULE_JSON = "modules.json"
MODULE_YEAR_COLOURS = ["snow", "slategray1", "slategray2", "slategray3"]
LIST_COLOUR = {"pre": "red3",
               "co": "purple3",
               "sug": "steelblue"}
OPT_LIST_COLOUR = {"pre": "pink3",
                   "co": "plum3",
                   "sug": "steelblue2"}
ARROW_HEADS = {"pre": "none",
               "co": "empty",
               "sug": "none"}

def trans_prereqs(modules, module_name):
    # base case
    if not modules[module_name]['pre']:
        return set()
    # recursive case
    deps = set()
    for pre in modules[module_name]['pre']:
        deps = deps | trans_prereqs(modules, pre) | set([pre])
    return deps

def indirect_prereqs(modules, module_name):
    return {x for pre in modules[module_name]['pre']
              for x in trans_prereqs(modules, pre)}

def direct_prereqs(modules, module_name):
    return set(modules[module_name]['pre']) - indirect_prereqs(modules, module_name)

def orphans(modules, hidden):
    orphans = set()
    changed = True
    while changed:
        changed = False
        for k in modules.keys():
            if (k not in orphans) and not (modules[k]['related'] - (hidden|orphans)):
                orphans |= set([k])
                changed = True
    return orphans


def load_modules(fname=None):
    # Load json from file
    fname = DEFAULT_MODULE_JSON if fname is None else fname
    with open(fname) as jf:
        parsed = json.load(jf)

    # Populate empty lists
    for module in parsed["modules"].values():
        for lst in ["pre", "co", "sug"]:
            if lst not in module:
                module[lst] = []

    return parsed["programmes"], parsed["modules"]


def render_programme(programmename, programme, modules, allmods, P, C, S, hide_required, hide_orphans):
    out = ""

    years = programme['years']
    hidden = set(modules.keys()) - set([m for year in years for m in year])

    if hide_required:
        hidden |= set(programme['required'])

    if hide_orphans:
        hidden |= orphans(modules, hidden)

    # Get all modules
    if allmods is None:
        allmods = [mod for year in years for mod in year]

    # Filter lists
    years = [list(filter(lambda m: m in allmods, year))
                 for year in years]

    # Emit coloured modules
    for year, yrnum in zip(years, range(0, len(years))):
        for module in year:
            if module in hidden:
                continue
            out += "{} [style=filled, fillcolor={}, tooltip=\"{} {} {}\"]\n".format(
                module, MODULE_YEAR_COLOURS[yrnum], programmename, yrnum + 1, module)
        out += "{{rank=same {}}}\n".format(" ".join(set(year) - hidden))

    # Draw lists
    for year in years:
        for module in year:
            for lst in ["pre", "co", "sug"]:
                if lst == "pre" and P: continue
                if lst == "co" and C: continue
                if lst == "sug" and S: continue

                for mod in modules[module][lst]:
                    if mod in hidden:
                        continue
                    out += "{} -> {} [color={}, arrowhead={}]\n".format(
                        mod, module, LIST_COLOUR[lst], ARROW_HEADS[lst])

    return out

args = docopt.docopt(__doc__)
programmes, modules = load_modules(args["<modules-json>"])

# Calculate allowed modules
if args["<module>"]:
    allmods = args["<module>"]
    changed = True
    while changed:
        changed = False
        for module in allmods:
            for lst in ["pre", "co", "sug"]:
                for mod in modules[module][lst]:
                    if mod not in allmods:
                        allmods.append(mod)
                        changed = True
else:
    if args["-p"] is not None:
        allmods = None
    else:
        allmods = modules.keys()

# remove redundant prerequisites
for k in modules.keys():
    modules[k]['pre'] = list(direct_prereqs(modules, k))

# collect forward-related modules
for k in modules.keys():
    modules[k]['related'] = set([m for r in ['pre', 'co', 'sug'] for m in modules[k][r]])

# propagate reverse relationships
for k in modules.keys():
    rel = modules[k]['related']
    for mod in rel:
        modules[mod]['related'] |= set([k])

print("digraph Modules {")
print("rankdir = {}".format(args["-r"]))
print("ranksep = 1.5")
if args["-p"] is not None:
    print(render_programme(args["-p"], programmes[args["-p"]], modules, allmods, args["-P"], args["-C"], args["-S"], args["-R"], args["-O"]))
else:
    for name, programme in programmes.items():
        print(render_programme(name, programme, modules, allmods, args["-P"], args["-C"], args["-S"], args["-R"], args["-O"]))
print("}")
