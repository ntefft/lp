# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 13:03:22 2019

@author: Nathan Tefft
"""
import numpy # import packages
import lpdtUtil
from statsmodels.base.model import GenericLikelihoodModel

# code drawn from http://www.statsmodels.org/dev/examples/notebooks/generated/generic_mle.html
# also https://austinrochford.com/posts/2015-03-03-mle-python-statsmodels.html

# define the log-likehood for the model
# A is the set of accident data
# N[i] is the proportion of crashes of type i, relative to type 1
# thet[i] is the two-car crash relative risk of type i, relative to type 1
# lamb[i] is the one-car crash relative risk of type i, relative to type 1

def _ll_lpdt(A, num_driver_types, thet, lamb):
    num_agg_rows = numpy.size(A,axis=0)
#    print("A: " + str(A))
    # in order to simplify issues with indexing, first convert the accident dataframe to separate matrices, one for single-car and one for two-car
    A_1 = A[:,:num_driver_types] # one car crashes
    A_2 = numpy.zeros((num_agg_rows,num_driver_types,num_driver_types)) # two car crashes
    curr_col = num_driver_types
    for dto in range(0,num_driver_types):
        for dti in range(0,num_driver_types):
            if dti >= dto:
                A_2[:,dto,dti] = A[:,curr_col]
                curr_col += 1
#    print("A_2: " + str(A_2))        
    thet_1 = numpy.concatenate((numpy.ones(num_driver_types-1),thet)) # add 1 to represent driver type 1 relative to themselves
    lamb_1 = numpy.concatenate((numpy.ones(num_driver_types-1),lamb)) # add 1 to represent driver type 1 relative to themselves
#    print("lamb_1: " + str(lamb_1))
#    print("thet_1: " + str(thet_1))
    # first substitute in for N values: incorporate information from single car crashes using the fact that larger observed quantities of one type suggest more drivers on the road of that type
    N = numpy.ones((num_agg_rows,num_driver_types))
    
    for dt in range(0,num_driver_types): # count of type dt driving on the road relative to type 1
        N[:,dt] = (1/lamb_1[dt])*(A_1[:,dt]/A_1[:,0])
#    print("N: " + str(N))
    # build the probability values for accidents of each type: first build the probability denominator
    p_denom = numpy.zeros((num_agg_rows))
    for dto in range(0,num_driver_types):
        for dti in range(0,num_driver_types):
            p_denom += N[:,dto]*N[:,dti]*(thet_1[dto]+thet_1[dti])
    
    # next build the set of probabilities and add accidents
    p = numpy.zeros((num_agg_rows,num_driver_types,num_driver_types))
    for dto in range(0,num_driver_types):
        for dti in range(0,num_driver_types):
            if dti >= dto:
                p[:,dto,dti] = N[:,dto]*N[:,dti]*(thet_1[dto]+thet_1[dti])/p_denom
                if dti != dto:
                    p[:,dto,dti] = 2*p[:,dto,dti] # after eliminating the duplicates, need to add in the probability of observing the two types reversed
#    print("p: " + str(p))
                    
    # construct the likelihood function
    ll = numpy.zeros((num_agg_rows))
    two_veh_total = 0
    for dto in range(0,num_driver_types):
       for dti in range(0,num_driver_types):
           if dti >= dto:
#               ll += A_2[:,dti]*numpy.log(p[:,dto,dti]) 
#               two_veh_total += A_2[:,dti]
               ll += A_2[:,dto,dti]*numpy.log(p[:,dto,dti]) 
               two_veh_total += A_2[:,dto,dti] # build the two-vehicle total while we're at it
#    print("ll 1: " + str(ll))
    
    # add natural log of the factorial of total 2-car crashes (have to do for each row separately)
    for i in range(0,num_agg_rows):
        ll[i] += lpdtUtil.lnfactorial(two_veh_total[i])
        for dto in range(0,num_driver_types):
            for dti in range(0,num_driver_types):
                if dti >= dto:
                    ll[i] -= lpdtUtil.lnfactorial(A_2[i,dto,dti])
        
#    print("ll 2: " + str(ll))
    return ll

# create a new model class which inherits from GenericLikelihoodModel
class Lpdt(GenericLikelihoodModel):
    # endog is A (accident counts), and exog is num_driver_types
    def __init__(self, endog, exog=None, num_driver_types=2, **kwds):
        if exog is None:
            exog = numpy.zeros((numpy.size(endog,axis=0),2*(num_driver_types-1))) # we don't have exogenous variables in our model
        super(Lpdt, self).__init__(endog, exog, num_driver_types=2, **kwds)
        
    def nloglikeobs(self, params):
        thet = params[:(self.num_driver_types-1)]
        lamb = params[(self.num_driver_types-1):]
        return -_ll_lpdt(self.endog, self.num_driver_types, thet, lamb)
    
    def fit(self, start_params=None, maxiter=10000, maxfun=5000, **kwds):
        for xn in ['const','x1']:
            self.exog_names.remove(xn)
        if start_params == None:
            # Reasonable starting values (assuming equal risk for each relative driver type)
            start_params = [[20*numpy.ones(self.num_driver_types-1)],[20*numpy.ones(self.num_driver_types-1)]]
        
        return super(Lpdt, self).fit(start_params=start_params, maxiter=maxiter, maxfun=maxfun, **kwds)
