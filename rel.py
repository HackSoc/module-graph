
class Rel:
    def __init__(self, pairs):
        self.pairs = frozenset(pairs)

    def __repr__(self):
        return "Rel({})".format(self.pairs)

    @property
    def dom(self):
        return {x for x, y in self.pairs}

    @property
    def ran(self):
        return {y for x, y in self.pairs}

    @property
    def all(self):
        return self.dom | self.ran

    def union(self, pairs):
        return Rel(self.pairs | frozenset(pairs))

    def image(self, s):
        return {y for x, y in self.pairs if x in s}

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

    @property
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

    @property
    def reflexive_closure(self):
        return Rel(self.pairs | {(x, x) for x in self.all})

    def transitively_redundant_pairs(self):
        # transitively redundant pairs are those whose removal does
        # not change the size of the transitive closure.
        #
        # there is almost certainly a more efficient algorithm for
        # this, but as the relations involved are small, we simply
        # express the above property in code
        orig_len = len(self.transitive_closure.pairs)
        redundant = set()
        for p in self.pairs:
            if len(Rel(self.pairs - {p}).transitive_closure.pairs) == orig_len:
                redundant |= {p}
        return redundant

    def transitively_minimal(self):
        return Rel(self.pairs - self.transitively_redundant_pairs())
