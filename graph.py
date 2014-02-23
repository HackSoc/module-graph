#!/usr/bin/env python3

"""graph.py render a module dependency graph

Usage:
  graph.py [<modules-json>] [-R] [-P] [-C] [-S] [-p <programme>] [-r <rankdir>] [--] [<module>...]

Options:
  -h --help       Show this text.
  <modules-json>  The modules.json file to use [default: "./modules.json"].
  -P              Don't show prerequisites
  -C              Don't show corequisites
  -S              Don't show suggestions
  -R              Don't show required modules
  -p <programme>  Only render the given programme.
  -r <rankdir>    Rank direction (LR or TB) [default: LR].
  <module>...     List of modules to render, default all in programme(s).
"""

import json
import docopt

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


def render_programme(programmename, programme, modules, allmods, P, C, S, hide_required):
    out = ""

    years = programme['years']
    required = set()

    if hide_required:
        required = set(programme['required'])

    # Get all modules
    if allmods is None:
        allmods = [mod for year in years for mod in year]

    # Filter lists
    years = [list(filter(lambda m: m in allmods, year))
                 for year in years]
    for year in years:
        for module in year:
            for lst in ["pre", "co", "sug"]:
                if lst == "pre" and P: continue
                if lst == "co" and C: continue
                if lst == "sug" and S: continue

                new = []
                for mod in modules[module][lst]:
                    if type(mod) is list:
                        mod = list(filter(lambda m: m in allmods, mod))
                        if len(mod) == 1:
                            new.append(mod[0])
                        elif len(mod) > 1:
                            new.append(mod)
                    elif mod in allmods:
                        new.append(mod)
                modules[module][lst] = new

    # Emit coloured modules
    for year, yrnum in zip(years, range(0, len(years))):
        for module in year:
            if module in required:
                continue
            out += "{} [style=filled, fillcolor={}, tooltip=\"{} {} {}\"]\n".format(
                module, MODULE_YEAR_COLOURS[yrnum], programmename, yrnum + 1, module)
        out += "{{rank=same {}}}\n".format(" ".join(set(year) - required))

    # Draw lists
    for year in years:
        for module in year:
            for lst in ["pre", "co", "sug"]:
                if lst == "pre" and P: continue
                if lst == "co" and C: continue
                if lst == "sug" and S: continue

                for mod in modules[module][lst]:
                    if mod in required:
                        continue
                    if type(mod) is list:
                        for choice in mod:
                            out += "{} -> {} [color={}, arrowhead={}]\n".format(
                                choice, module, OPT_LIST_COLOUR[lst], ARROW_HEADS[lst])
                    else:
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

for k in modules.keys():
    modules[k]['pre'] = list(direct_prereqs(modules, k))

print("digraph Modules {")
print("rankdir = {}".format(args["-r"]))
print("ranksep = 1.5")
if args["-p"] is not None:
    print(render_programme(args["-p"], programmes[args["-p"]], modules, allmods, args["-P"], args["-C"], args["-S"], args["-R"]))
else:
    for name, programme in programmes.items():
        print(render_programme(name, programme, modules, allmods, args["-P"], args["-C"], args["-S"], args["-R"]))
print("}")
