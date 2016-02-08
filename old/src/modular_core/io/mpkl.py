import modular_core.fundamental as lfu

import cPickle as pickle

__doc__ = '''Provides basic functions for pkl formatted io of python objects'''

if __name__ == 'libs.modular_core.io.mpkl':pass
    #lfu.check_gui_pack()
    #lgm = lfu.gui_pack.lgm
    #lgd = lfu.gui_pack.lgd
    #lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'mpkl of modular_core.io'

def save_pkl_object(obj,filename):
    '''Save object \'obj\' at \'filename.\''''
    output = open(filename,'wb')
    pickle.dump(obj,output)
    output.close()

def load_pkl_object(filename):
    '''Load object at \'filename\' and return it.'''
    pkl_file = open(filename,'rb')
    data = pickle.load(pkl_file)
    pkl_file.close()
    return data










