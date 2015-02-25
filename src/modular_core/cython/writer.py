import modular_core.libfundamental as lfu
import modular_core.io.liboutput as lo

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

import pdb,os,sys,shutil,numpy,pyximport
from cStringIO import StringIO

class function(lfu.mobject):

    def _code(self):
        coder = StringIO()
        coder.write('\n'+'#'*80+'\n')
        self._code_header(coder)
        self._code_body(coder)
        coder.write('\n'+'#'*80+'\n')
        return coder.getvalue()
    
    def _code_header(self,coder):
        coder.write('\n'+self.cytype+' '+self.name+'('+self.argstring+')')
        coder.write(':')
        #if self.cytype.startswith('cdef') and not self.cytype.count('void'):
        #    coder.write(' except -1:')
        #else:coder.write(':')

    def _code_body(self,coder):
        coder.write('\tprint \'helloworld!\'\n\n')

    def __init__(self,*args,**kwargs):
        self._default('name','afunc',**kwargs)
        self._default('argstring','',**kwargs)
        self._default('cytype','def',**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

class extension(lfu.mobject):

    header =\
'''
# cython:profile=False,boundscheck=False,nonecheck=False,wraparound=False,initializedcheck=False,cdivision=True
###################################
# imports:
from libc.math cimport log
from libc.math cimport sin
from libc.math cimport cos
from libc.stdlib cimport rand
cdef extern from "limits.h":
\tint INT_MAX
import random,numpy
'''

    def _import(self):
        return __import__(self.name)

    def _uninstall(self):
        #builddir = os.path.join(os.getcwd(),'build')
        #if os.path.isdir(builddir):pass
        
        lastname = self.name.replace('_','.',1)
        lastname = lo.decrement_filename(lastname)
        lastname = lastname.replace('.','_',1)

        extname = lastname+'.so'
        extinplace = os.path.join(os.getcwd(),extname)
        if os.path.isfile(extinplace):os.remove(extinplace)

        extname = lastname+'.c'
        extinresrc = lfu.get_resource_path(extname)
        if os.path.isfile(extinresrc):os.remove(extinresrc)

        extname = lastname+'.pyx'
        extinresrc = lfu.get_resource_path(extname)
        if os.path.isfile(extinresrc):os.remove(extinresrc)

        #if self.name in sys.modules.keys():
        #    print 'rcnt',sys.getrefcount(sys.modules[self.name])
        #    del sys.modules[self.name]

    def _install(self):
        self._uninstall()
        srcs = [self.filepath]
        exts = cythonize([Extension(self.name,srcs)])

        #args = ['clean','--all','build_ext','--inplace','install','--user']
        #args = ['clean','--all','build_ext','install','--user']
        #args = ['build_ext','install','--user']

        # clean everything
        args = ['clean']
        setup(script_args = args,ext_modules = exts,
            include_dirs = [numpy.get_include()])
        # ensure '/build' exists to prevent bug...
        os.makedirs(os.path.join(os.getcwd(),'build'))
        # actually build the extension in place
        args = ['build_ext','--inplace']
        setup(script_args = args,ext_modules = exts,
            include_dirs = [numpy.get_include()])

    def _write(self):
        self.code = self._code()
        with open(self.filepath,'w') as fh:fh.write(self.code)

    def __init__(self,*args,**kwargs):
        self._default('name',None,**kwargs)

        self._default('imports',[],**kwargs)
        self._default('functions',[],**kwargs)

        lfu.mobject.__init__(self,*args,**kwargs)
        self.filepath = lfu.get_resource_path(self.name+'.pyx')

    def _code_header(self,coder):
        coder.write(self.header)
        for im in self.imports:
            coder.write('import '+im+'\n')
        coder.write('\n\n')

    def _code_functions(self,coder):
        for f in self.functions:coder.write(f._code())

    def _code(self):
        coder = StringIO()
        self._code_header(coder)
        self._code_functions(coder)
        return coder.getvalue()

def test():
    mname = 'modu_ext'
    funcs = [function()]

    writer = extension(
        name = mname,
        functions = funcs)
    writer._write()
    writer._install()
    module = writer._import()

    pdb.set_trace()

###
if __name__ == '__main__':test()
###





