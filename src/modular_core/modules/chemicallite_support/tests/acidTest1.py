from time import sleep
from time import clock

from math import *
import numpy as np
from scipy import linalg
from scipy import integrate
from scipy import stats
import matplotlib as mpl
from matplotlib import pyplot as plt
from numpy import linalg as la
from numpy import random as rnd
import random
import pdb

import string as str

from multiprocessing import Pool

import cProfile, pstats, StringIO

#from scipy.stats import gamma


import pstats, cProfile
#import libchemicalstring_9WM as lcs
import libs.modules.chemicallite_support.stringchemical as lcs

import time
import os

import pickle

############################################################################
############################################################################

def make_plots(labels, meanData, stdData):
	t = meanData[labels.index('time')]
	iter = meanData[labels.index('iteration')]

	x_mean = meanData[labels.index('x')]
	y_mean = meanData[labels.index('y')]
	z_mean = meanData[labels.index('z')]
	w_mean = meanData[labels.index('w')]

	x_std = stdData[labels.index('x')]
	z_std = stdData[labels.index('z')]

	# change fonts so that PDF's do not export with outlined fonts (bad for editing)
	mpl.rcParams['pdf.fonttype'] = 42

	# make a Matlab-like environment, where plots are updated on the fly
	plt.ion()
	plt.show()

	plt.figure(1)

	plt.subplot('321')
	plt.plot(t, x_mean, 'b')
	plt.plot(t, 10.0*np.exp(-t), 'r')
	plt.legend(('measured', 'predicted'))

	plt.subplot('322')
	plt.plot(t, y_mean, 'b')
	plt.plot(t, 10.0*(1.0-np.exp(-t))*2.0, 'r')

	plt.subplot('323')
	plt.plot(t, z_mean, 'b')
	plt.plot(t, 5.0+2.0*t, 'r')

	plt.subplot('324')
	plt.plot(t, w_mean, 'b')
	plt.plot(t, 5.0*np.exp(-0.5*t), 'r')

	plt.subplot('325')
	plt.plot(t, x_std, 'b')
	x_p = np.exp(-t)
	x_std_theory = np.sqrt(10.0*x_p*(1-x_p))
	plt.plot(t, x_std_theory, 'r')

	plt.subplot('326')
	plt.plot(t, z_std, 'b')
	z_std_theory = np.sqrt(2.0*t)
	plt.plot(t, z_std_theory, 'r')

	plt.savefig('acidTest1_compare.pdf')

	##########################
	##########################

	plt.figure(2)

	plt.subplot('321')
	plt.plot(t, x_mean-(10.0*np.exp(-t)), 'r')
	plt.legend(('error',))

	plt.subplot('322')
	plt.plot(t, y_mean-(10.0*(1.0-np.exp(-t))*2.0), 'r')

	plt.subplot('323')
	plt.plot(t, z_mean-(5.0+2.0*t), 'r')

	plt.subplot('324')
	plt.plot(t, w_mean-(5.0*np.exp(-0.5*t)), 'r')

	plt.subplot('325')
	x_p = np.exp(-t)
	x_std_theory = np.sqrt(10.0*x_p*(1-x_p))
	plt.plot(t, x_std-x_std_theory, 'r')

	plt.subplot('326')
	z_std_theory = np.sqrt(2.0*t)
	plt.plot(t, z_std-z_std_theory, 'r')

	plt.savefig('acidTest1_error.pdf')

def test(_make_plots_ = False, TotSamp = 10000):
	tdir = os.path.dirname(os.path.realpath(__file__))
	fileIn = os.path.join(tdir, 'models/acidTest1.inp')

	SysString = open(fileIn).read()
	print '-------------------------------------------------------'
	print '-------------------------------------------------------'
	print SysString
	print '-------------------------------------------------------'
	print '-------------------------------------------------------'
	SysString = SysString.replace('\n','') + '||'

	##########################
	##########################

	labels, meanData, stdData = runBatch(SysString, TotSamp)
	print labels

	##########################
	##########################

	t = meanData[labels.index('time')]
	iter = meanData[labels.index('iteration')]

	x_mean = meanData[labels.index('x')]
	y_mean = meanData[labels.index('y')]
	z_mean = meanData[labels.index('z')]
	w_mean = meanData[labels.index('w')]

	x_std = stdData[labels.index('x')]
	z_std = stdData[labels.index('z')]

	if _make_plots_: make_plots(labels, meanData, stdData)

	##########
	### INSERT CODE WHICH RETURNS "PASS" OR "FAIL" OR SOMETHING MORE DESCRIPTIVE
	##########
	return None

if __name__ == '__main__':
	test(True)

_tests_ = {'acid test 1':test}

############################################################################
############################################################################

def genBatch(SysParm):

	SysString, N, nPool = SysParm
	offset = nPool*N

	DataAll = []
	
	start = time.time()
	for samp in range(N):
		RES = lcs.simulate(SysString, samp+offset)
		data = RES[0]
		labels = RES[1]
		DataAll.append(np.array(RES[0], dtype=np.double))
		timeLeft = (N-samp+1)*((time.time()-start)/(samp+1))
		#print samp+offset, ', seconds left =', timeLeft, ', minutes left =', timeLeft/60.0

	return labels, np.array(DataAll)

def runBatch(SysString, N):

	NPool = 8
	nSamp = N/NPool
	pool = Pool(NPool)
	SysParms = []
	RES = []
	for ii in range(NPool):
		#SysParms.append((SysString, nSamp, ii))
		RES.append(genBatch((SysString, nSamp, ii)))
	#RES = pool.map(genBatch, SysParms)
	
	labels = RES[0][0]
	vDataAll = np.concatenate([RES[x][1] for x in range(NPool)], axis=0)
	
	meanData = np.mean(vDataAll, axis=0)
	stdData = np.std(vDataAll, axis=0)

	#pdb.set_trace()

	return labels, meanData, stdData

############################################################################
############################################################################




