#!/usr/bin/env python3

"""graph.py render a module dependency graph

Usage:
  graph.py [<modules-json>] [-P] [-C] [-S] [-E] [-R] [-O] [-p <programme>] [-r <rankdir>] [--] [<module>...]

Options:
  -h --help       Show this text.
  <modules-json>  The modules.json file to use [default: "./modules.json"].
  -P              Don't show prerequisites
  -C              Don't show corequisites
  -S              Don't show suggestions
  -E              Don't show mutual exclusions
  -R              Don't show required modules
  -O              Don't show orphaned modules (those which don't contribute to any relationships)
  -p <programme>  Only render the given programme.
  -r <rankdir>    Rank direction (RL or BT) [default: RL].
  <module>...     List of modules to render, default all in programme(s).
"""

import json
import docopt
from itertools import zip_longest
from rel import Rel

DEFAULT_MODULE_JSON = "modules.json"
MODULE_YEAR_COLOURS = ["snow", "slategray1", "slategray2", "slategray3"]
LIST_COLOUR = {"pre": "red3",
               "co": "purple3",
               "sug": "steelblue",
               "excl": "red"}
OPT_LIST_COLOUR = {"pre": "pink3",
                   "co": "plum3",
                   "sug": "steelblue2",
                   "excl": "red"}
ARROW_HEADS = {"pre": "open",
               "co": "empty",
               "sug": "halfopen",
               "excl": "none"}
EDGE_STYLES = {'pre': 'solid',
               'co': 'solid',
               'sug': 'dashed',
               'excl': 'bold'}
EDGE_KINDS = {'pre', 'co', 'sug', 'excl'}

class Programme:

    def __init__(self, name, years, required):
        self.name = name
        self.years = [frozenset(y) for y in years]
        self.required = frozenset(required)

        self.build_yearmap()

    def build_yearmap(self):
        self.yearmap = {}
        for year, num in zip(self.years, range(len(self.years))):
            for mod in year:
                self.yearmap[mod] = num

    def include(self, others):
        for p in others:
            self.years = [y1 | y2 for (y1, y2) in zip_longest(self.years, p.years, fillvalue=set())]
            self.required = self.required | p.required

        self.build_yearmap()

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

    # we need to resolve includes in a separate pass because the order
    # in which modules appear in the constructed dict is not defined
    for name, details in parsed['programmes'].items():
        if 'include' in details:
                progs[name].include({progs[p] for p in details['include']})

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

    # avoid duplicating mutual exclusions
    if 'excl' in deps:
        deps['excl'] = deps['excl'].find_antisymmetry()

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

kinds = set(EDGE_KINDS)
if args['-P']:
    kinds -= {'pre'}
if args['-C']:
    kinds -= {'co'}
if args['-S']:
    kinds -= {'sug'}
if args['-E']:
    kinds -= {'excl'}

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
