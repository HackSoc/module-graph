from itertools import zip_longest


class Programme:

    def __init__(self, years, required):
        self.years = [frozenset(y) for y in years]
        self.required = frozenset(required)

        self.build_yearmap()

    def __repr__(self):
        return "Programme({}, {})".format(self.years, self.required)

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

    def union(self, others):
        work = self
        for p in others:
            work = Programme([y1 | y2 for (y1, y2) in zip_longest(work.years, p.years, fillvalue=set())],
                             work.required | p.required)
        return work

    def choice(self, others):
        work = self
        for p in others:
            work = Programme([y1 | y2 for (y1, y2) in zip_longest(work.years, p.years, fillvalue=set())],
                             work.required & p.required)
        return work

    @property
    def all(self):
        return {x for y in self.years for x in y}

    def yearof(self, module):
        return self.yearmap[module]
