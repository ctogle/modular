import libs.modular_core.libfundamental as lfu

import pdb

def test_test(*args, **kwargs):
	print 'run test_test!'
	return 'pass'

_tests_ = {'t1':test_test}

if __name__ == '__main__':
	print 'This is a library!'

if __name__ == 'libs.modular_core.libtests':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb


