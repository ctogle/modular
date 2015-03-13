import modular_core.fundamental as lfu

import cPickle as pickle
import pdb,sys,traceback

if __name__ == 'libs.modular_core.io.pkl':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'pkl of modular_core'

###############################################################################
### save/load arbitrary python object at filename
###############################################################################

# save obj at filename
def save_pkl_object(obj,filename):
    output = open(filename,'wb')
    pickle.dump(obj,output)
    output.close()

# load obj at filename
def load_pkl_object(filename):
    pkl_file = open(filename,'rb')
    data = pickle.load(pkl_file)
    print 'pkldatatype',type(data)
    pkl_file.close()
    return data

    try:
        pkl_file = open(filename, 'rb')
        data = pickle.load(pkl_file)
    except:
        try:
            pkl_file = open(filename, 'r')
            data = pickle.load(pkl_file)
        except pickle.UnpicklingError:
            print 'something is wrong with your pkl file!'
        except:
            traceback.print_exc(file = sys.stdout)
            return None
    pkl_file.close()
    return data

###############################################################################
###############################################################################










