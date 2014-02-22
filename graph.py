#!/usr/bin/env python3

"""graph.py render a module dependency graph

Usage:
  graph.py [<modules-json>] [-P] [-C] [-S] [-p <programme>] [-r <rankdir>] [--] [<module>...]

Options:
  -h --help       Show this text.
  <modules-json>  The modules.json file to use [default: "./modules.json"].
  -P              Don't show prerequisites
  -C              Don't show corequisites
  -S              Don't show suggestions
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


def render_programme(programmename, programme, modules, allmods, P, C, S):
    out = ""

    # Get all modules
    if allmods is None:
        allmods = [mod for year in programme for mod in year]

    # Filter lists
    programme = [list(filter(lambda m: m in allmods, year))
                 for year in programme]
    for year in programme:
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
    for year, yrnum in zip(programme, range(0, len(programme))):
        for module in year:
            out += "{} [style=filled, fillcolor={}, tooltip=\"{} {} {}\"]\n".format(
                module, MODULE_YEAR_COLOURS[yrnum], programmename, yrnum + 1, module)
        out += "{{rank=same {}}}\n".format(" ".join(year))

    # Draw lists
    for year in programme:
        for module in year:
            for lst in ["pre", "co", "sug"]:
                if lst == "pre" and P: continue
                if lst == "co" and C: continue
                if lst == "sug" and S: continue

                for mod in modules[module][lst]:
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

print("digraph Modules {")
print("rankdir = {}".format(args["-r"]))
print("ranksep = 1.5")
if args["-p"] is not None:
    print(render_programme(args["-p"], programmes[args["-p"]], modules, allmods, args["-P"], args["-C"], args["-S"]))
else:
    for name, programme in programmes.items():
        print(render_programme(name, programme, modules, allmods, args["-P"], args["-C"], args["-S"]))
print("}")
