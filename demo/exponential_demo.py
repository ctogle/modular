import sim_anneal.anneal as sa

import matplotlib.pyplot as plt
import numpy as np
import pdb,sys,random,inspect





# plot the best fit, initial fit, and target fit
def plot(f,x,i,a,b):
    ax = plt.gca()
    ax.plot(x,f(x,*b),color = 'g',label = 'best fit')
    ax.plot(x,f(x,*a),color = 'r',label = 'actual',linestyle = '--')
    ax.legend()
    plt.show()

# summarize the results of a round of fitting
def summarize(f,x,initial,actual,result):
    error = tuple(abs((r-a)/a) for r,a in zip(result,actual))
    percenterror = np.round(max(error)*100.0,3)
    print '-'*50
    print 'fit percentage error:',percenterror
    print 'actual:',actual
    print 'result:',result
    print '-'*50
    if 'p' in sys.argv:plot(f,x,initial,actual,result)
    return percenterror

d = 2.0

# return the best fit parameters given:
#   f - function to fit with
#   x - domain to fit over
#   y - input data to fit to
#   b - parameters bounds (can be None)
#   i - initial parameters (can be None)
def run(f,x,y,b = None,i = None,**ekwgs):
    if b is None:
        dim = len(inspect.getargspec(f)[0])-1
        b = tuple(bound(f,x,10**d,j,dim) for j in range(dim))
    if i is None:i = tuple(sum(bd)/2.0 for bd in b)
    annealer = sa.annealer(f,x,y,i,b,**ekwgs)
    #result = annealer.anneal()
    result = annealer.anneal_iter(10)
    return result

# using a randomized actual data set...
# return the best fit parameters given:
#   f - function to fit with
#   x - domain to fit over
#   b - parameters bounds (can be None)
#   i - initial parameters (can be None)
def run_func(f,x,b = None,i = None,**ekwgs):

    dim = len(inspect.getargspec(f)[0])-1
    bounds = tuple(bound(f,x,10**d,j,dim) for j in range(dim))
    actual = random_position(bounds)
    y = f(x,*actual)

    result = run(f,x,y,b,i,**ekwgs)
    summary = summarize(f,x,i,actual,result)
    return result,summary

# determine the proper boundary of an axis 
def bound(f,x,d,ax,dim):
    r = random.random
    ap = tuple(r() for j in range(dim))
    an = tuple(r if j != ax else -r for j,r in enumerate(ap))
    if (f(x,*ap) == f(x,*an)).all():b = (0,d)
    else:b = (-d,d)
    return b

# return a random position in parameter space
def random_position(bounds):
    rpos = tuple(b[0]+random.random()*(b[1]-b[0]) for b in bounds)
    return rpos





# f -> function to fit with
# x -> the domain used for measuring fitness
def run_expo(**kws):
    f = lambda x,a,b : a*np.exp(b*x)
    x = np.linspace(-1,1,1000)
    return run_func(f,x,None,None,**kws)

# f -> function to fit with
# x -> the domain used for measuring fitness
def run_bell(**kws):
    f = lambda x,a,b,c : a*np.exp(-0.5*((x-b)/c)**2.0)
    x = np.linspace(-100,100,1000)
    return run_func(f,x,None,None,**kws)





def bell_mean_error(i = 100):
    summaries = []

    sx = []
    sy = []

    kws = {}
    for j in range(5):
        ss = []
        for x in range(i):
            kws['heatrate'] = (j+1)*10
            r,s = run_bell(**kws)
            ss.append(s)

        summaries.append(np.mean(ss))

        sx.append((j+1)*10)
        sy.append(summaries[-1])

    plt.plot(sx,sy)
    plt.show()

    return summaries





if __name__ == '__main__':
    res,summ = run_expo()
    res,summ = run_bell()


    #summ = bell_mean_error()
    #print 'bell mean error'
    #print 'summary:',summ





