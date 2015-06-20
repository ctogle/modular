import modular_core.fundamental as lfu

import pdb

__doc__ = '''Provides basic functions for html (table) formatted io of modular data'''

if __name__ == 'modular_core.io.mhtml':pass
    #if lfu.gui_pack is None:lfu.find_gui_pack()
    #lgm = lfu.gui_pack.lgm
    #lgd = lfu.gui_pack.lgd
    #lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'mhtml of modular_core.io'

def write_table(names,atts,headers,filename):
    '''Create an html table for data in names,atts with headers at filename.'''
    if not filename.endswith('.html'):filename += '.html'
    border = "2";width = "50%";cellspacing = "5"
    cellpadding = "8";bgcolor = "white";columns = len(atts)

    rows = []
    for name in names:
        row = ()
        for att in atts:
            row += (getattr(name,att),)
        rows.append(row)

    fhand = open(filename, "w")

    tattsline = '\
        <table border={} width={} cellspacing={} \
        cellpadding={} bgcolor={} cols={}>\n'.format(
            border,width,cellspacing,cellpadding,bgcolor,columns)
    fhand.write(tattsline)

    header = '<tr>'
    for att in range(len(headers)):header += '<td>{}</td>'
    header += '</tr>'
    fhand.write(header.format(*tuple(headers)))

    for x in range(len(names)):
        new = '<tr>'
        for att in atts:new += '<td>{}</td>'
        new = new + '</tr>\n'
        fhand.write(new.format(*rows[x]))
    fhand.write('</table>')










