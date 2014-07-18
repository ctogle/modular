import pstats, cProfile

import comparison as cp

import pdb

cProfile.runctx('cp.trial_11()', globals(), locals(), "Profile.prof")

s = pstats.Stats("Profile.prof")
s.strip_dirs().sort_stats("time").print_stats()

#pdb.set_trace()




