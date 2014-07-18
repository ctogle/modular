import pstats, cProfile

import bindings as bd

import pdb

def wrap_test(cmd):
	cProfile.runctx(cmd, globals(), locals(), "Profile.prof")
	s = pstats.Stats("Profile.prof")
	print '###', cmd, '###'
	s.strip_dirs().sort_stats("time").print_stats()
	print '######'

#tests = ['bd.py_main2()']
tests = ['bd.add_test()', 'bd.add_test2()', 'bd.py_main()', 'bd.py_main2()']

for t in tests: wrap_test(t)

#pdb.set_trace()




