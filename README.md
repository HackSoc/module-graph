module-graph
============

Produce a pretty and colourful graph of module dependencies,
optionally restricted to a given program.

Format of modules.json
----------------------

Outline:

 + List of programmes
 + Programme contains list of years
 + Year contains list of modules in the form {"name": <name>, <lists>}
 + Omitted lists are assumed empty

Module lists:

 + **pre** - prerequisite
 + **co**  - corequisite (prereq in same year)
 + **sug** - suggested, but not required
