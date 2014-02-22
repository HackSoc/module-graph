#!/usr/bin/env python3

import json

def load_modules(fname=""):
    # Load json from file
    fname = "modules.json" if fname == "" else fname
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

print(load_modules())
