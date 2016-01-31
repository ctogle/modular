import sim_anneal.anneal as sa
import sim_anneal.forms as sf

import profiling

import matplotlib.pyplot as plt
import unittest,random,numpy,os

import pdb

#python -m unittest discover -v ./ "*tests.py"

def plot(x,f,a,g,r):
    plt.plot(x,f(x,*a),color = 'g',label = 'actual')
    plt.plot(x,f(x,*g),color = 'b',label = 'initial')
    plt.plot(x,f(x,*r),color = 'r',label = 'result')
    plt.show()

class test_anneal(unittest.TestCase):

    def atest_mmkinetics(self):
        import sim_anneal.modular_annealer as mann

        #mcfg = os.path.join(os.getcwd(),'MM_kinetics_means.mcfg')
        #emng = mce.ensemble_manager()
        #ensm = emng._add_ensemble('gillespiem')
        #ensm.mcfg_path = mcfg
        #ensm._parse_mcfg()
        #ensm._run_mcfg(mcfg)
        ann = mann.annealer()


        pdb.set_trace()


        bounds = ((-1000.0,1000.0),(0.0,1000.0))
        actual = (1.0,0.01,800.0,5000,10000,0,100)
        guess = (1.0,0.01,800.0,5000,100,0,100)
        maxiter = 100000
        tolerance = 0.0001

        def d(b,c):
            ensm.cartographer_plan._move_to(0)
            ensm._run_params_to_location_prepoolinit()
            ensm._run_params_to_location()
            rinit = ensm._run_init()
            dshp = tuple(x for x in rinit if type(x) == type(1))
            trgs = rinit[-1]
            data = ensm._run_batch_np(100,dshp)

            pdb.set_trace()

            y,bins = numpy.histogram(data,density = True,bins = 100)
            x = numpy.array([(bins[j-1]+bins[j])/2.0 for j in range(1,bins.size)])
            return x,y

        def f(x,b,c):
            a = 1/(2*numpy.pi*c**2)**(0.5)
            return a*numpy.exp(-0.5*((x-b)/c)**2)
    
        x,y = d(*actual)
        res = sa.simanneal(f,x,y,guess,bounds,maxiter,tolerance)

        #plt.plot(x,y,color = 'r')
        #plt.plot(x,f(x,*res),color = 'g')
        #plt.plot(x,f(x,*guess),color = 'b')
        #plt.show()

        error = tuple(abs((r-a)/a) for r,a in zip(res,actual))
        print 'mmkinetics error:',max(error)
        self.assertTrue(max(error) < 0.01)

    def atest_distribution(self):
        bounds = ((-1000.0,1000.0),(0.0,1000.0))
        actual = (20.0,10.0)
        guess = (1.0,1.0)
        maxiter = 100000
        tolerance = 0.0001

        def d(b,c):
            data = numpy.random.normal(b,c,10000)
            y,bins = numpy.histogram(data,density = True,bins = 100)
            x = numpy.array([(bins[j-1]+bins[j])/2.0 for j in range(1,bins.size)])
            return x,y

        def f(x,b,c):
            a = 1/(2*numpy.pi*c**2)**(0.5)
            return a*numpy.exp(-0.5*((x-b)/c)**2)
    
        x,y = d(*actual)
        res = sa.simanneal(f,x,y,guess,bounds,maxiter,tolerance)

        #plt.plot(x,y,color = 'r')
        #plt.plot(x,f(x,*res),color = 'g')
        #plt.plot(x,f(x,*guess),color = 'b')
        #plt.show()

        error = tuple(abs((r-a)/a) for r,a in zip(res,actual))
        print 'distribution error:',max(error)
        self.assertTrue(max(error) < 0.01)

    ###########################################################################
    ### exponential tests
    ###########################################################################

    def run_expo(self,x,actual,guess,bounds,maxiter,tolerance):
        f = sf.exponential
        y = f(x,*actual)
        res = sa.simanneal(f,x,y,guess,bounds,maxiter,tolerance)
        return res

    def run_expo_buff(self,x,actual,guess,bounds,maxiter,tolerance):
        f = sf.exponential_buffered
        b = numpy.zeros(x.shape,x.dtype)
        f(x.size,x,b,*actual)
        res = sa.simanneal(f,x,b,guess,bounds,maxiter,tolerance,True)
        return res

    def expo(self,x,a,g,b,i,t):
        res = self.run_expo(x,a,g,b,i,t)
        error = tuple(abs((r-a)/a) for r,a in zip(res,a))
        #plot(domain,sf.exponential,actual,guess,res)
        return max(error)

    def expo_buff(self,x,a,g,b,i,t):
        res = self.run_expo_buff(x,a,g,b,i,t)
        error = tuple(abs((r-a)/a) for r,a in zip(res,a))
        #plot(domain,sf.exponential,actual,guess,res)
        return max(error)

    def expo_profile(self,x,a,g,b,i,t):
        s = profiling.profile_function(self.run_expo,x,a,g,b,i,t)
        return s

    def expo_buff_profile(self,x,a,g,b,i,t):
        s = profiling.profile_function(self.run_expo_buff,x,a,g,b,i,t)
        return s

    def test_expo(self):
        actual = (5.0,-5.0)
        guess = (1.0,1.0)
        domain = numpy.linspace(0,1000,1000)
        bounds = ((-1000.0,1000.0),(-1000.0,1000.0))
        maxiter = 100000
        tolerance = 0.0001      
        eargs = (domain,actual,guess,bounds,maxiter,tolerance)

        expo_error = self.expo(*eargs)
        expo_buff_error = self.expo_buff(*eargs)
        expo_s = self.expo_profile(*eargs)
        expo_buff_s = self.expo_buff_profile(*eargs)

        print 'exponential error:',expo_error
        print 'exponential buffered error:',expo_buff_error
        print 'exponential profile stats:',expo_s.total_tt
        print 'exponential buffered profile stats:',expo_buff_s.total_tt

        self.assertTrue(expo_error < 0.01)
        self.assertTrue(expo_buff_error < 0.01)
        self.assertTrue(expo_s.total_tt < 10.0)
        self.assertTrue(expo_buff_s.total_tt < 10.0)
        expo_s.strip_dirs().sort_stats('time').print_stats()
        expo_buff_s.strip_dirs().sort_stats('time').print_stats()

    ###########################################################################
    ###########################################################################
    ###########################################################################

    def bell(self,x,actual,guess):
        bounds = ((-1000.0,1000.0),(0.0,1000.0),(-1000.0,1000.0))
        maxiter = 100000
        tolerance = 0.0001
        f = sf.bell
        y = f(x,*actual)
        res = sa.simanneal(f,x,y,guess,bounds,maxiter,tolerance)
        return res

    def bell_buff(self,x,actual,guess):
        bounds = ((-1000.0,1000.0),(0.0,1000.0),(-1000.0,1000.0))
        maxiter = 100000
        tolerance = 0.0001
        f = sf.bell_buffered
        b = numpy.zeros(x.shape,x.dtype)
        f(x.size,x,b,*actual)
        res = sa.simanneal(f,x,b,guess,bounds,maxiter,tolerance,True)
        return res

    def atest_bell(self):
        actual = (20.0,10.0,8.0)
        guess = (-1.0,1.0,0.1)
        domain = numpy.linspace(-100,100,200)
        res = self.bell(domain,actual,guess)
        #plot(domain,sf.bell,actual,guess,res)
        error = tuple(abs((r-a)/a) for r,a in zip(res,actual))
        print 'bell error:',max(error)
        self.assertTrue(max(error) < 0.01)

    def atest_bell_buff(self):
        actual = (20.0,10.0,8.0)
        guess = (-1.0,1.0,0.1)
        domain = numpy.linspace(-100,100,200)
        res = self.bell_buff(domain,actual,guess)
        #plot(domain,sf.bell,actual,guess,res)
        error = tuple(abs((r-a)/a) for r,a in zip(res,actual))
        print 'bell buffered error:',max(error)
        self.assertTrue(max(error) < 0.01)

    def atest_bell_profile(self):
        actual = (20.0,10.0,8.0)
        guess = (-1.0,1.0,0.1)
        domain = numpy.linspace(-100,100,200)
        s = profiling.profile_function(self.bell,domain,actual,guess)
        print 'bell profile stats:',s.total_tt
        s.strip_dirs().sort_stats('time').print_stats()

    def atest_bell_buff_profile(self):
        actual = (20.0,10.0,8.0)
        guess = (-1.0,1.0,0.1)
        domain = numpy.linspace(-100,100,200)
        s = profiling.profile_function(self.bell_buff,domain,actual,guess)
        print 'bell buffered profile stats:',s.total_tt
        s.strip_dirs().sort_stats('time').print_stats()

if __name__ == '__main__':unittest.main()





