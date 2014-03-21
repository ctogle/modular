import pstats, cProfile

import stringchemical as lchem
#import libchemicalstring_3 as lchem

import pdb

cProfile.runctx('lchem.simulate()', globals(), locals(), "Profile.prof")

s = pstats.Stats("Profile.prof")
s.strip_dirs().sort_stats("time").print_stats()

#pdb.set_trace()




