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
  -r <rankdir>    Rank direction (RL or BT) [default: RL].
  <module>...     List of modules to render, default all in programme(s).
"""

import json
import docopt
from rel import Rel

DEFAULT_MODULE_JSON = "modules.json"
MODULE_YEAR_COLOURS = ["snow", "slategray1", "slategray2", "slategray3"]
LIST_COLOUR = {"pre": "red3",
               "co": "purple3",
               "sug": "steelblue"}
OPT_LIST_COLOUR = {"pre": "pink3",
                   "co": "plum3",
                   "sug": "steelblue2"}
ARROW_HEADS = {"pre": "open",
               "co": "empty",
               "sug": "halfopen"}
EDGE_STYLES = {'pre': 'solid',
               'co': 'bold',
               'sug': 'dashed'}
EDGE_KINDS = {'pre', 'co', 'sug'}

class Programme:

    def __init__(self, name, years, required):
        self.name = name
        self.years = [frozenset(y) for y in years]
        self.required = frozenset(required)
        self.yearmap = {}
        for year, num in zip(years, range(len(years))):
            for mod in year:
                self.yearmap[mod] = num

    def __repr__(self):
        return "Programme({}, {}, {})".format(self.name, self.years, self.required)

    @property
    def all(self):
        return {x for y in self.years for x in y}

    def yearof(self, module):
        return self.yearmap[module]


def load_modules(fname=None):
    # Load json from file
    fname = DEFAULT_MODULE_JSON if fname is None else fname
    with open(fname) as jf:
        parsed = json.load(jf)

    # build dependency relation
    deps = {dt : Rel(set()) for dt in EDGE_KINDS}

    for name, deplist in parsed['modules'].items():
        for dt in EDGE_KINDS:
            if dt in deplist:
                for mod in deplist[dt]:
                    deps[dt] = deps[dt].union({(name, mod)})

    # build programmes
    progs = {}

    for name, details in parsed['programmes'].items():
        progs[name] = Programme(name, details['years'], details['required'])

    return deps, progs


def render_prog(prog, deps, kinds, whitelist, hide_required, hide_orphans):
    out = ''

    deps = {k: deps[k] for k in kinds}

    universe = prog.all

    # if appropriate, remove required modules
    if hide_required:
        universe -= prog.required

    # if we have a module whitelist, calculate modules that it implies
    if whitelist:
        universe &= {x
                     for k in deps
                     for x in deps[k]
                     .transitive_closure
                     .reflexive_closure
                     .dom_restrict(whitelist)
                     .ran}

    # restrict the dependency graph to those modules that are in the programme
    deps = {kind: deps[kind].restrict(universe) for kind in deps}

    # remove redundant dependencies
    if 'pre' in deps:
        deps['pre'] = deps['pre'].transitively_minimal()

    # if appropriate, remove orphan nodes
    if hide_orphans:
        universe &= {x for k in deps for x in deps[k].all}

    # module colours
    for mod in universe:
        ynum = prog.yearof(mod)
        out += "{} [style=filled, fillcolor={}, tooltip=\"{} {} {}\"]\n".format(
            mod, MODULE_YEAR_COLOURS[ynum], prog.name, ynum+1, mod)

    # module ranks
    for year in prog.years:
        out += "{{rank=same {}}}\n".format(" ".join(year & universe))

    # edges
    for kind in deps:
        for x, y in deps[kind].pairs:
            out += "{} -> {} [color={}, arrowhead={}, style={}]\n".format(
                x, y, LIST_COLOUR[kind], ARROW_HEADS[kind], EDGE_STYLES[kind])

    return out


args = docopt.docopt(__doc__)
deps, progs = load_modules(args["<modules-json>"])

kinds = EDGE_KINDS
if args['-P']:
    kinds -= {'pre'}
if args['-C']:
    kinds -= {'co'}
if args['-S']:
    kinds -= {'sug'}

whitelist = None
if args['<module>']:
    whitelist = set(args['<module>'])

print("digraph Modules {")
print("rankdir = {}".format(args["-r"]))
print("ranksep = 1.5")

if args['-p'] is not None:
    print(render_prog(progs[args['-p']], deps, kinds, whitelist, args['-R'], args['-O']))
else:
    for prog in progs.values():
        print(render_prog(prog, deps, kinds, whitelist, args['-R'], args['-O']))

print("}")
