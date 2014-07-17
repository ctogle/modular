import libs.modular_core.libfundamental as lfu

import csv
import libs.modular_core.libfiler as lf

if __name__ == 'libs.modular_core.libtxtoutput':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd

if __name__ == '__main__': print 'this is a library!'

def write_csv(system, csv_filename, specifics = []):
	csv_filename=csv_filename[:-4] + '.csv'
	out = csv.writer(open(csv_filename,"wb"),
		delimiter =',',quoting=csv.QUOTE_NONE)
	out.writerow([data.label for data in system.data 
						if data.label in specifics])
	for dex in range(len(system.data[0].scalars)):
		row = []
		for data in system.data:
			if data.label in specifics:
				row.append(data.scalars[dex])
				
		out.writerow(row)


