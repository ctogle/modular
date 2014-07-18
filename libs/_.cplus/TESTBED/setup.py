import sys, os, pdb

from distutils.core import setup
from distutils.extension import Extension

USE_CYTHON = True
try: from Cython.Build import cythonize
except ImportError: USE_CYTHON = False

def parse(lines):
	res = {}; key = None
	for li in lines:
		if not li == '' and not li.startswith('#'):
			if li.startswith('<') and li.endswith('>'): key = li[1:-1]
			else:
				if not key in res.keys(): res[key] = [li]
				else: res[key].append(li)
	return res

def read_make_list(filename = 'setup.info'):
	with open(os.path.join(os.getcwd(), filename), 'r') as handle:
		lines = [li.strip() for li in handle.readlines()]
	result = parse(lines)
	return result['wrapper'][0], results['headers'], result['sources']

def make():
	if len(sys.argv) == 1: sys.argv += ['build_ext','--inplace','clean']
	wrapper, headdirs, sourcefiles = read_make_list()
	ext = '.pyx' if USE_CYTHON else '.cpp'
	extensions = [Extension(wrapper,sources = [wrapper+ext]+sourcefiles, 
				include_dirs = headdirs,extra_compile_args = ['/EHsc'])]
	if USE_CYTHON: extensions = cythonize(extensions)
	setup(ext_modules = extensions)
	return wrapper

def test(wrapper):
	__import__(wrapper)
	bd = sys.modules[wrapper]
	samples = extra(bd)
	return bd, samples

def extra(bd):
	vec = bd.pybtVector3(1,2,3)
	return {'vec':vec}

def dump_info():

	def catch(x, fis, new):
		x = list(x)
		x[0] = x[0][offs+len(os.sep):]
		x[2] = cfis
		for fi in fis:
			afi = '\t'+'/'.join([x[0].replace(os.sep,'/'),fi])
			new[-1].append(afi)

	cnew = []; hnew = []; offs = len(os.getcwd())
	for src_dir in src_dirs:
		walk = os.walk(os.path.join(os.getcwd(),src_dir))
		cnew.append([])
		hnew.append([])
		for x in walk:
			cfis = [y for y in x[2] if y.endswith('.cpp')]
			hfis = [y for y in x[2] if y.endswith('.h')]
			if cfis: catch(x, cfis, cnew)
			if hfis: catch(x, hfis, hnew)

	lines = ['','<wrapper>','\t'+wrapper_name]
	lines.extend(['','<headers>'])
	for filist, srcdir in zip(hnew, src_dirs):
		lines.extend(['\t# ' + srcdir] + filist + [''])
	lines.extend(['','<sources>'])
	for filist, srcdir in zip(cnew, src_dirs):
		lines.extend(['\t# ' + srcdir] + filist + [''])
	with open('setup.info', 'w') as handle:
		[handle.write(str(item)+'\n') for item in lines]

if __name__ == '__main__':
	bd, samples = test(make())
	v = samples['vec']
elif __name__ == 'setup': pass

wrapper_name = 'bindings'
src_dirs = ['src_sample', 'src_b3']
headdirs = ['src_b3/src','src_b3/btgui','src_b3/btgui/OpenGLWindow']


# python setup.py build_ext --inplace clean


