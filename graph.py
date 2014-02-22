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

def load_modules(fname=None):
    # Load json from file
    fname = "modules.json" if fname is None else fname
    with open(fname) as jf:
        parsed = json.load(jf)

    # Populate empty lists
    for programme in parsed.values():
        for year in programme:
            for module in year:
                if "pre" not in module:
                    module["pre"] = []
                if "co" not in module:
                    module["co"] = []
                if "sug" not in module:
                    module["sug"] = []

    return parsed

print(load_modules(arguments["<modules-json>"]))
