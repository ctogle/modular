import modular_core.libfundamental as lfu

import cPickle as pickle
import pdb,os,sys,traceback

if __name__ == 'libs.modular_core.libfiler':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'libfiler of modular_core'

# write text to path; ask permission to overwrite if safe
def write_text(path,text,safe = True):
    if safe and os.path.isfile(path):
        msg = 'Are you sure you want\nto overwrite file?:\n'+path
        check = lgd.message_dialog(None,msg,'Overwrite',True)
        if not check: return
    with open(path,'w') as handle:handle.write(text)



#
def save_pkl_object(obj, filename):
    output = open(filename, 'wb')
    pickle.dump(obj, output)
    output.close()

#
def load_pkl_object(filename):
    if not os.path.isfile(filename):
        #dp_path = lfu.get_data_pool_path()
        dp_path = os.getcwd()
        filename = os.path.join(dp_path, filename.split(os.path.sep)[-1])
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
            traceback.print_exc(file=sys.stdout)
            return None
    pkl_file.close()
    return data

#
def output_lines(lines, direc, finame = None, 
        overwrite = True, dont_ask = False):
    #if no finame is given, direc should contain the full path
    if finame is None: path = direc
    else: path = os.path.join(direc, finame)
    if os.path.isfile(path):
        if not overwrite:
            print 'cant output without overwriting; skipping!'
            return False

        else:
            if dont_ask: check = lambda: True
            #if dont_ask: True
            else:
                msg = '\n'.join(['Are you sure you want', 
                    'to overwrite the module?:', path])
                check = lgd.message_dialog(None, msg, 'Overwrite', True)

            #if check(): print 'overwriting as instructed...'
            if check: print 'overwriting as instructed...'
            else:
                print 'wont output without your permission; skipping!'
                return False

    with open(path, 'w') as handle:
        [handle.write(line + '\n') for line in lines]

    return True






