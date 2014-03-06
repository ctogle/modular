import os
import glob
import time

def get_fi_lengths(extensions = ['.py', '.cl', '.pyx']):
	
	def check_fi(file_):
		with open(file_, 'r') as hand:
			return len(hand.readlines())

	def check_root(root):
		return root.endswith('Devices') or\
				root.endswith('Phidgets') or\
					root.endswith('Events')

	def check_extension(file_):
		return True in [file_.endswith(ext) for ext in extensions]

	leng=0
	for root, dirs, files in os.walk(os.getcwd()):
		for file_ in files:
			if check_extension(file_):
				if not check_root(root):
					fi_leng = check_fi(os.path.join(root, file_))
					#print root, file_, fi_leng
					leng += fi_leng

	return leng

def run():
	total = get_fi_lengths()
	print 'total line count:', total
	raw_input('')
	#print 'DECISION: ||' + ':'.join([str(val) for val in ['right', ('left', 10)]]) + '||'
	#print 'DECISION: ||' + ':'.join([str(val) for val in ['-20000', ('20000', 10)]]) + '||'

run()




