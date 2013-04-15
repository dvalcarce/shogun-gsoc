from pylab import figure,pcolor,scatter,contour,colorbar,show,subplot,plot,connect,axis
from numpy.random import randn
from shogun.Features import *
from shogun.Classifier import *
from shogun.Kernel import *
import pickle
import numpy as np


f = open("a.pkl", "rb")

x, y, z = pickle.load(f)
z = np.rot90(z)
pcolor(x, y, z, shading='interp')

contour(x, y, z, linewidths=1, colors='black', hold=True)

axis('tight')

#connect('key_press_event', util.quit)

show()

