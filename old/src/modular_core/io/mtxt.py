import modular_core.fundamental as lfu

import csv

__doc__ = '''Provides basic functions for txt (csv) formatted io of modular data'''

if __name__ == 'libs.modular_core.mtxt':pass
    #if lfu.gui_pack is None: lfu.find_gui_pack()
    #lgm = lfu.gui_pack.lgm
    #lgd = lfu.gui_pack.lgd
    #lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'mtxt of modular_core.io'

def write_csv(system,filename,specifics = []):
    '''Save data found in system object at \'filename.\' 
    If data\'s label is not in \'specifics\', ignore it.
    '''
    if not filename.endswith('.csv'):filename += '.csv'
    #filename = filename[:-4] + '.csv'
    out = csv.writer(open(filename,"wb"),
        delimiter =',',quoting=csv.QUOTE_NONE)
    out.writerow([data.name for data in 
        system.data if data.name in specifics])
    lens = [len(d.data) for d in system.data]
    for dex in range(min(lens)):
        row = []
        for data in system.data:
            if data.name in specifics:
                row.append(data.data[dex])
        out.writerow(row)

def write_text(path,text,safe = True):
    '''Write text to a file at path.
    Ask for overwrite permission if necessary.
    '''
    if safe and os.path.isfile(path):
        msg = 'Are you sure you want\nto overwrite file?:\n'+path
        check = lgd.message_dialog(None,msg,'Overwrite',True)
        if not check:return
    with open(path,'w') as handle:handle.write(text)










