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
EDGE_KINDS = {'pre', 'co', 'sug'}

class Rel:
    def __init__(self, pairs):
        self.pairs = frozenset(pairs)

    def __repr__(self):
        return "Rel({})".format(self.pairs)

    def override(self, pairs):
        return Rel(self.pairs | frozenset(pairs))

    def image(self, s):
        return {y for x, y in self.pairs if x in s}

    def dom(self):
        return {x for x, y in self.pairs}

    def ran(self):
        return {y for x, y in self.pairs}

    def all(self):
        return self.dom() | self.ran()

    def restrict(self, s):
        return Rel({(x, y) for x, y in self.pairs if x in s and y in s})

    def antirestrict(self, s):
        return Rel({(x, y) for x, y in self.pairs if x not in s and y not in s})

    def dom_restrict(self, s):
        return Rel({(x, y) for x, y in self.pairs if x in s})

    def ran_restrict(self, s):
        return Rel({(x, y) for x, y in self.pairs if y in s})

    def dom_antirestrict(self, s):
        return Rel({(x, y) for x, y in self.pairs if x not in s})

    def ran_antirestrict(self, s):
        return Rel({(x, y) for x, y in self.pairs if y not in s})

    def transitive_closure(self):
        work = self
        old_len = len(self.pairs)
        done = False
        while not done:
            work = Rel(work.pairs | work.trans_closure_step())
            if len(work.pairs) == old_len:
                done = True
            old_len = len(work.pairs)
        return work

    def trans_closure_step(self):
        return {(x, z) for x, y1 in self.pairs for y2, z in self.pairs if y1 == y2}

    def reflexive_closure(self):
        return Rel(self.pairs | {(x, x) for x in self.all()})

    def transitively_redundant_pairs(self):
        # transitively redundant pairs are those whose removal does
        # not change the size of the transitive closure.
        #
        # there is almost certainly a more efficient algorithm for
        # this, but as the relations involved are small, we simply
        # express the above property in code
        orig_len = len(self.transitive_closure().pairs)
        redundant = set()
        for p in self.pairs:
            if len(Rel(self.pairs - {p}).transitive_closure().pairs) == orig_len:
                redundant |= {p}
        return redundant

    def transitively_minimal(self):
        return Rel(self.pairs - self.transitively_redundant_pairs())

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
        for dt in {'pre', 'co', 'sug'}:
            if dt in deplist:
                for mod in deplist[dt]:
                    deps[dt] = deps[dt].override({(name, mod)})

    # build programmes
    progs = {}

    for name, details in parsed['programmes'].items():
        progs[name] = Programme(name, details['years'], details['required'])

    return deps, progs


def render_prog(prog, deps, kinds, whitelist, hide_required, hide_orphans):
    out = ''

    universe = prog.all()

    # if appropriate, remove required modules
    if hide_required:
        universe -= prog.required

    # if we have a module whitelist, calculate modules that it implies
    if whitelist:
        needed = {x for k in kinds
                    for x in deps[k].transitive_closure().reflexive_closure().dom_restrict(whitelist).ran()}
        universe &= needed

    # restrict the dependency graph to those modules that are in the programme
    deps = {kind: deps[kind].restrict(universe) for kind in kinds}

    # remove redundant dependencies
    deps['pre'] = deps['pre'].transitively_minimal()

    # if appropriate, remove orphan nodes
    if hide_orphans:
        universe &= {x for k in kinds for x in deps[k].all()}

    # module colours
    for mod in universe:
        ynum = prog.yearof(mod)
        out += "{} [style=filled, fillcolor={}, tooltip=\"{} {} {}\"]\n".format(
            mod, MODULE_YEAR_COLOURS[ynum], prog.name, ynum+1, mod)

    # module ranks
    for year in prog.years:
        out += "{{rank=same {}}}\n".format(" ".join(year & universe))

    # edges
    for kind in kinds:
        for x, y in deps[kind].pairs:
            out += "{} -> {} [color={}, arrowhead={}]\n".format(
                x, y, LIST_COLOUR[kind], ARROW_HEADS[kind])

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
