import modular_core.fundamental as lfu

import pdb

def create_table(nameList, attList, headers, filename):
    nameReturnList=nameList
    attReturnList=attList

    #make a tuple out of the requested attributes for each specimen in
    #nameReturnList
    rows = []
    for name in nameReturnList:
        row = ()
        for att in attReturnList:
            newItem = (getattr(name, att),)
            row = row + newItem
        rows.append(row)

    #Table attributes
    border = "2"
    width = "50%"
    cellSpacing = "5"
    cellPadding = "8"
    bgcolor = "white"
    columns = len(attReturnList)

    #Construction of table
    if not filename.endswith('.html'):
        filename += '.html'
    text_file = open(filename, "w")
    text_file.write(
        "<table border={} width={} cellspacing={}\
            cellpadding={} bgcolor={} cols={}>\n".format(
              border, width, cellSpacing, 
              cellPadding, bgcolor, columns))

    #This loop writes the header of the table
    header = "<tr>"
    hcnt = len(headers)
    for att in range(hcnt):
        header += "<td>{}</td>"
    header += "</tr>"
    text_file.write(header.format(*tuple(headers)))

    #This loop writes the body
    for x in range(len(nameReturnList)):
        newLine = "<tr>"
        for att in attReturnList:
            newLine = newLine + "<td>{}</td>"
        newLine = newLine + "</tr>\n"
        text_file.write(newLine.format(*rows[x]))
    text_file.write("</table>")

if __name__ == 'modular_core.libhtmloutput':
    if lfu.gui_pack is None: lfu.find_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb

if __name__ == '__main__':
    print 'this is a library!'





