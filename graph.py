#!/usr/bin/env python3

"""graph.py render a module dependency graph

Usage:
  graph.py [<modules-json>] [-p <programme>]

Options:
  -h --help       Show this text.
  <modules-json>  The modules.json file to use [default: "./modules.json"].
  -p <programme>  Only render the given programme.
"""

import json
import docopt
import copy

DEFAULT_MODULE_JSON = "modules.json"
MODULE_YEAR_COLOURS = ["snow", "slategray1", "slategray2", "slategray3"]
LIST_COLOUR = {"pre": "red3",
               "co": "purple3",
               "sug": "steelblue"}
OPT_LIST_COLOUR = {"pre": "pink3",
                   "co": "plum3",
                   "sug": "steelblue2"}


def load_modules(fname=None):
    # Load json from file
    fname = DEFAULT_MODULE_JSON if fname is None else fname
    with open(fname) as jf:
        parsed = json.load(jf)

    # Populate empty lists
    for programme in parsed.values():
        for year in programme:
            for module in year:
                for lst in ["pre", "co", "sug"]:
                    if lst not in module:
                        module[lst] = []

    return parsed


def render_programme(programme, allmods=None):
    out = ""

    # Get all modules
    if allmods is None:
        allmods = [mod["name"] for year in programme for mod in year]

    # Filter lists
    for year in programme:
        for module in year:
            for lst in ["pre", "co", "sug"]:
                new = []
                for mod in module[lst]:
                    if type(mod) is list:
                        mod = list(filter(lambda m: m in allmods, mod))
                        if len(mod) == 1:
                            new.append(mod[0])
                        elif len(mod) > 1:
                            new.append(mod)
                    elif mod in allmods:
                        new.append(mod)
                module[lst] = new

    # Get module names by year
    modules = [[mod["name"] for mod in year]
               for year in programme]

    # Emit coloured modules
    for mods, yrnum in zip(modules, range(0, len(modules))):
        for mod in mods:
            out += "{} [style=filled, fillcolor={}]\n".format(
                mod, MODULE_YEAR_COLOURS[yrnum])
        out += "{{rank=same {}}}\n".format(" ".join(mods))

    # Draw lists
    for year in programme:
        for module in year:
            for lst in ["pre", "co", "sug"]:
                for mod in module[lst]:
                    if type(mod) is list:
                        for choice in mod:
                            out += "{} -> {} [color={}]\n".format(
                                choice, module["name"], OPT_LIST_COLOUR[lst])
                    else:
                        out += "{} -> {} [color={}]\n".format(
                            mod, module["name"], LIST_COLOUR[lst])

    return out

args = docopt.docopt(__doc__)
data = load_modules(args["<modules-json>"])

print("digraph Modules {")
print("rankdir = LR")
if args["-p"] is not None:
    print(render_programme(data[args["-p"]]))
else:
    for programme in data.values():
        print(render_programme(copy.deepcopy(programme)))
print("}")
