import modular_core.fundamental as lfu

import modular_core.io.pkl as pkl

import cPickle as pickle
import pdb,os,sys,traceback

if __name__ == 'libs.modular_core.libfiler':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'libfiler of modular_core'

###############################################################################
### utility functions
###############################################################################

# write text to path; ask permission to overwrite if safe
def write_text(path,text,safe = True):
    if safe and os.path.isfile(path):
        msg = 'Are you sure you want\nto overwrite file?:\n'+path
        check = lgd.message_dialog(None,msg,'Overwrite',True)
        if not check: return
    with open(path,'w') as handle:handle.write(text)

def resolve_filename(guess):
    if not os.path.isfile(guess):
        dpath = os.getcwd()
        dfile = guess.split(os.path.sep)[-1]
        guess = os.path.join(dpath,dfile)
    return guess

###############################################################################

# save numpy arrays using hdf5;replace such attributes with hdf5 filenames
# then pkl the rest of the object
def save_mobject(obj,filename):
    pkl.save_pkl_object(obj,filename)

# load object using pkl;check attributes for hdf5 filepaths to reload
def load_mobject(filename):
    filename = resolve_filename(filename)
    mobj = pkl.load_pkl_object(filename)
    return mobj

###############################################################################
###############################################################################










