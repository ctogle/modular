import modular_core.fundamental as lfu
import modular_core.io.liboutput as lo

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

import pdb,os,sys,shutil,numpy,pyximport
from cStringIO import StringIO

if __name__ == '__main__':print 'cython writer of modular_core'

###############################################################################
### function is intended to aid in writing cython extensions from python
###############################################################################

class function(lfu.mobject):

    # handy function to write cython to initialize a numpy array
    def _nparray(self,coder,name,shape,dtype = 'numpy.double',spacer = '\n\t'):
        predtype = dtype[dtype.find('.')+1:]
        coder.write(spacer+'cdef '+predtype+' [')
        coder.write(','.join([':']*len(shape))+'] '+name+' = ')
        coder.write('numpy.zeros('+str(shape)+',dtype = '+dtype+')')

    # handy function to write cython to initialize a cython.view array
    def _carray(self,coder,name,shape,dtype = 'double',spacer = '\n\t'):
        coder.write(spacer+'cdef '+dtype+' '+name+'[')
        coder.write(','.join([str(s) for s in shape])+']')

    def _code(self):
        coder = StringIO()
        coder.write('\n'+'#'*80+'\n')
        self._code_header(coder)
        self._code_body(coder)
        coder.write('\n'+'#'*80+'\n')
        return coder.getvalue()
    
    def _code_header(self,coder):
        coder.write('\n'+self.cytype+' '+self.name+'('+self.argstring+')')
        coder.write(self.cyoptions+':')

    def _code_body(self,coder):
        coder.write('\tprint \'helloworld!\'\n\n')

    def __init__(self,*args,**kwargs):
        self._default('name','afunc',**kwargs)
        self._default('argstring','',**kwargs)
        self._default('cytype','def',**kwargs)
        self._default('cyoptions','',**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

###############################################################################
### extension is a wrapper for creating pyx cython extensions on the fly
###############################################################################

class extension(lfu.mobject):

    header =\
'''
# cython:profile=False,boundscheck=False,nonecheck=False,wraparound=False,initializedcheck=False,cdivision=True
###################################
# imports:
from libc.math cimport log
from libc.math cimport sin
from libc.math cimport cos
#from libc.stdlib cimport rand
#cdef extern from "limits.h":
#\tint INT_MAX
from numpy import cumprod as cumulative_product
cdef double pi = 3.14159265359
import random,numpy
import time as timemodule
from cython.view cimport array as cvarray
'''

    # import and return the extension module this installs
    def _import(self):
        return __import__(self.name)

    # attempt to uninstall the last on-the-fly 
    # module created this runtime
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

    # install the last written pyx file as a python extension
    # attempt to uninstall the last on-the-fly extension by first uninstalling
    def _install(self):
        self._uninstall()
        srcs = [self.filepath]
        exts = cythonize([Extension(self.name,srcs)])
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

    # calculate the code for an extension and write it to a safe place
    def _write(self):
        self.code = self._code()
        with open(self.filepath,'w') as fh:fh.write(self.code)

    def __init__(self,*args,**kwargs):
        self._default('name',None,**kwargs)

        self._default('imports',[],**kwargs)
        self._default('functions',[],**kwargs)

        lfu.mobject.__init__(self,*args,**kwargs)
        self.filepath = lfu.get_resource_path(self.name+'.pyx')

    # add standard cython header info to pyx file
    def _code_header(self,coder):
        coder.write(self.header)
        for im in self.imports:
            coder.write('import '+im+'\n')
        coder.write('\n\n')

    # turn function mobjects into cython code and add to pyx file
    def _code_functions(self,coder):
        for f in self.functions:coder.write(f._code())

    # write the code which constitutes the entire pyx file
    def _code(self):
        coder = StringIO()
        self._code_header(coder)
        self._code_functions(coder)
        return coder.getvalue()

###############################################################################










