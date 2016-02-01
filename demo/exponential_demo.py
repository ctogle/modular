import sim_anneal.anneal as sa

import matplotlib.pyplot as plt
import numpy as np
import sys





# plot the best fit, initial fit, and target fit
def plot(f,x,i,a,b):
    ax = plt.gca()
    ax.plot(x,f(x,*b),color = 'g',label = 'best fit')
    #ax.plot(x,f(x,*i),color = 'b',label = 'initial',linestyle = '--')
    ax.plot(x,f(x,*a),color = 'r',label = 'actual',linestyle = '--')
    ax.legend()
    plt.show()

# summarize the results of a round of fitting
def summarize(f,x,initial,actual,result):
    error = tuple(abs((r-a)/a) for r,a in zip(result,actual))
    print '-'*50
    print 'fit percentage error:',np.round(max(error)*100.0,3)
    print 'actual:',actual
    print 'result:',result
    print '-'*50
    if 'p' in sys.argv:plot(f,x,initial,actual,result)

# return the best fit parameters given:
#   f - function to fit with
#   x - domain to fit over
#   y - input data to fit to
#   i - initial parameters
#   b - parameters bounds
def run(f,x,y,i,b):
    ekwgs = {'iterations':10000,'tolerance':0.0001}
    annealer = sa.annealer(f,x,y,i,b,**ekwgs)
    result = annealer.anneal()
    return result





# actual -> the correct parameters used to create input data
# initial -> the initial parameters provided as a guess
# bounds -> (minimum,maximum) bounds for each axis
#
# x -> the domain used for measuring fitness
# y -> input data to perform fitting against
def run_expo():

    # fitting function
    def exponential(x,a,b):
        return a*np.exp(b*x)

    actual = (4.321,0.765)
    initial = (1000.0,1000.0)
    bounds = ((-1000.0,1000.0),(-1000.0,1000.0))

    f = exponential
    x = np.linspace(-10,0,100)
    y = f(x,*actual)

    result = run(f,x,y,initial,bounds)
    summarize(f,x,initial,actual,result)

def run_bell():

    # fitting function
    def bell(x,a,b,c):
        return a*np.exp(-0.5*((x-b)/c)**2.0)

    actual = (5.0,5.0,5.0)
    initial = (1000.0,1000.0,1000.0)
    bounds = ((-1000.0,1000.0),(-1000.0,1000.0),(0.0,1000.0))

    f = bell
    x = np.linspace(-100,100,1000)
    y = f(x,*actual)

    result = run(f,x,y,initial,bounds)
    summarize(f,x,initial,actual,result)





if __name__ == '__main__':
    run_expo()
    run_bell()





