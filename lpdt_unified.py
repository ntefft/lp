# -*- coding: utf-8 -*-
"""
Created on Wed May 15 11:37:00 2019

@author: ntefft
"""

import os, sys, numpy, pandas # import packages
from statsmodels.base.model import GenericLikelihoodModel

# path for Spyder or Jupyter Notebooks
if os.path.exists(sys.path[0] + '\\Documents\\GitHub\\lpdt'):
    os.chdir(sys.path[0] + '\\Documents\\GitHub\\lpdt')
else:
    os.chdir(sys.path[0])
    
import lpdtutil

# read in FARS data
df_accident = pandas.read_csv('data\\df_accident.csv')
df_accident.set_index(['year','st_case'],inplace=True) # set the index
df_vehicle = pandas.read_csv('data\\df_vehicle.csv')
df_vehicle.set_index(['year','st_case','veh_no'],inplace=True) # set the index
df_person = pandas.read_csv('data\\df_person.csv')
df_person.set_index(['year','st_case','veh_no','per_no'],inplace=True) # set the index

# get estimation sample
#A = lpdtutil.get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=1983, last_year=2017, equal_mixing=['year','weekend','hour'])
A = lpdtutil.get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=1983, last_year=2017, equal_mixing=['year'])

# code drawn from http://www.statsmodels.org/dev/examples/notebooks/generated/generic_mle.html
# also https://austinrochford.com/posts/2015-03-03-mle-python-statsmodels.html

# define the log-likehood for the model
# A is the set of accident data
# N[i] is the proportion of crashes of type i, relative to type 1
# thet[i] is the two-car crash relative risk of type i, relative to type 1
# lamb[i] is the one-car crash relative risk of type i, relative to type 1
def _ll_lpdt(A, num_driver_types, thet, lamb):
    # I think we just add across rows of A (all the equal mixing rows), but need to check this again
    
    # first substitute in for N values: incorporate information from single car crashes using the fact that larger observed quantities of one type suggest more drivers on the road of that type
    N = numpy.ones((numpy.size(A,axis=0),num_driver_types))
    for dt in range(1,num_driver_types): # N relative to type 1 is 1
#        N[dt] = (1/lamb[dt])*(A['a_' + str(dt+1)]/A['a_1'])
        N[:,dt] = (1/lamb[dt])*(A[:,dt]/A[:,0])

    # build the probability values for accidents of each type: first build the probability denominator
    p_denom = numpy.zeros((numpy.size(A,axis=0)))
    for dto in range(0,num_driver_types):
        for dti in range(0,num_driver_types):
            p_denom += N[:,dto]*N[:,dti]*(thet[dto]+thet[dti])
    
    # next build the set of probabilities and add accidents
    p = numpy.zeros((numpy.size(A,axis=0),num_driver_types,num_driver_types))
    for dto in range(0,num_driver_types):
        for dti in range(0,num_driver_types):
            if dti >= dto:
                p[:,dto,dti] = N[:,dto]*N[:,dti]*(thet[dto]+thet[dti])/p_denom
                if dti != dto:
                    p[:,dto,dti] = 2*p[:,dto,dti] # after eliminating the duplicates, need to add in the probability of observing the two types reversed
    
    # construct the likelihood function
    ll = numpy.zeros((numpy.size(A,axis=0)))
    current_col = num_driver_types # column numbers to draw from begin after the one-car crashes
    two_veh_total = 0
    for dto in range(0,num_driver_types):
       for dti in range(0,num_driver_types):
           if dti >= dto:
               ll += A[:,current_col]*numpy.log(p[:,dto,dti]) 
               two_veh_total += A[:,current_col]
               current_col += 1
    
    # add natural log of the factorial of total 2-car crashes (have to do for each row separately)
    # add the same time, total up log likelihood
    ll_total = 0
    for i in range(0,numpy.size(A,axis=0)):
        ll_total += ll[i]    
        ll_total += lpdtutil.lnfactorial(two_veh_total[i])

    return ll_total

# create a new model class which inherits from GenericLikelihoodModel
class Lpdt(GenericLikelihoodModel):
    # endog is A (accident counts), and exog is num_driver_types
    def __init__(self, endog, exog=None, num_driver_types=2, **kwds):
        if exog is None:
            exog = numpy.zeros((numpy.size(endog,axis=0),2*num_driver_types)) # we don't have exogenous variables in our model
        super(Lpdt, self).__init__(endog, exog, num_driver_types=2, **kwds)
        
    def nloglikeobs(self, params):
        thet = params[:self.num_driver_types]
        lamb = params[self.num_driver_types:]
        ll = _ll_lpdt(self.endog, self.num_driver_types, thet, lamb)
        return -ll 
    
    def fit(self, start_params=None, maxiter=10000, maxfun=5000, **kwds):
        # we have one additional parameter and we need to add it for summary
#        self.exog_names.append('lambda')
        for xn in ['const','x1', 'x2', 'x3']:
            self.exog_names.remove(xn)
        if start_params == None:
            # Reasonable starting values (equal risk and counts for each relative driver type)
            start_params = numpy.ones(2*self.num_driver_types)
        return super(Lpdt, self).fit(start_params=start_params, 
                                     maxiter=maxiter, maxfun=maxfun, 
                                     **kwds)
        
mod = Lpdt(A, num_driver_types=2, extra_params_names=['theta','lambda'])
res = mod.fit()
print(mod.exog_names)
print(mod.endog_names)
print(res.summary())