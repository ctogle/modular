from distutils.core import setup, Extension

module1 = Extension('helloworld',
                    sources = ['helloworld.cpp'])

#module1=Extension('_HelloWorld', sources=['Hello.cpp'])

setup (name = 'ModuleWrapDemo',
       version = '1.0',
       description = 'This is a demo simulation module',
       ext_modules = [module1])







