# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 13:03:22 2019

@author: Nathan Tefft

This is a collection of functions used to create and estimate the LP model, including for multiple imputation.
"""
import numpy, time, lpUtil # import packages
from statsmodels.base.model import GenericLikelihoodModel

# calculates the natural log of the factorial of n (had to build this by hand because I couldn't find an existing python function)
def lnfactorial(n):
    n_calc = int(n)
    lnf = 0
    for i in range(1,n_calc+1):
        lnf += numpy.log(i)
    return lnf

# calculate boostrap standard error from bootstrap estimates
def bs_se(theta_bs, axis=None):
    return numpy.power(numpy.divide(numpy.power((numpy.subtract(theta_bs,numpy.divide(theta_bs.sum(axis),numpy.size(theta_bs,axis)))),2).sum(axis),(numpy.size(theta_bs,axis)-1)),0.5)

# fit the LP model using an already constructed analytic sample
def fit_model(analytic_sample,df_vehicle,df_person,equal_mixing=['year','state','weekend','hour'],bsreps=100):           
    
    start = time.time()
    # get the estimation sample
    est_sample = lpUtil.get_estimation_sample(analytic_sample,df_vehicle,df_person,equal_mixing,analytic_sample.drinking_definition,
                                                analytic_sample.bac_threshold,analytic_sample.mirep)
    end = time.time()
    print("Time to build estimation sample: " + str(end-start))
    
    start = time.time()
    mod = Lp(est_sample) # create the model (modified GenericLikelihoodModel)
    res = mod.fit() # fit the model
    res.bootstrap(nrep=bsreps) # get bootstrapped results
    print(mod.exog_names)
    print(mod.endog_names)
    print(res.summary())
    end = time.time()
    print("Time to fit model: " + str(end-start))
    
    # add final_params attribute to the fit model, which captures the relevant estimates and standard errors
    # row 0 = theta, row 1 = lambda, row 2 = N
    # column 0 = estimate, column 1 = bootstrapped standard error
    res.final_params = numpy.column_stack((res.params,bs_se(res.bootstrap_results,axis=0)))
    res.final_params = numpy.vstack([res.final_params,[(1/res.params[1])*(est_sample['a_2'].sum()/est_sample['a_1'].sum()),bs_se((1/res.bootstrap_results[:,1])*(est_sample['a_2'].sum()/est_sample['a_1'].sum()))]])
    
    # report relevant model statistics
    print('Parameters (theta, lambda, N): ', res.final_params[:,0])
    print('Bootstrap standard errors (theta, lambda, N): ', res.final_params[:,1])
    print('Log-likelihood: ', res.llf)
    print('Residual degrees of freedom: ', res.df_resid)
    
    return res

# wrapper around fit_model which implements multiple imputation estimation. Generates estimates for each MI replicate, and then
# combines the estimates and standard errors
def fit_model_mi(df_accident, df_vehicle, df_person, first_year=2017, last_year=2017, earliest_hour=20, 
                               latest_hour=4, equal_mixing=['year','state','weekend','hour'], drinking_definition='bac_primary', 
                               bac_threshold = 0.08, state_year_prop_threshold = 0.13, bsreps=100, mireps=10):           
    
    res_params = numpy.zeros((mireps, 3, 2))
    mi_res = numpy.zeros((3, 2))
    mi_llf = 0
    mi_df_resid = 0
    # loop over mi replicates and estimate model for each
    for i in range(0,mireps):
        analytic_sample = lpUtil.get_analytic_sample(df_accident,df_vehicle,df_person,first_year,
                        last_year,earliest_hour,latest_hour,drinking_definition,bac_threshold, 
                        state_year_prop_threshold,(i+1),False)
        res = fit_model(analytic_sample,df_vehicle,df_person,equal_mixing,bsreps)
        res_params[i] = res.final_params
        mi_res[:,0] += res_params[i,:,0]/mireps # add estimate to running mean of estimates, for final mi estimate
        mi_llf += res.llf
        mi_df_resid = res.df_resid
        
    # loop again to calculate final standard errors
    for i in range(0,mireps): 
        mi_res[:,1] += numpy.power(res_params[i,:,1],2)/mireps + ((1+1/mireps)/(mireps-1))*numpy.power(res_params[i,:,1]-mi_res[:,1],2)
        
    # report relevant model statistics
    print('MI Parameters (theta, lambda, N): ', mi_res[:,0])
    print('MI bootstrap standard errors (theta, lambda, N): ', mi_res[:,1])
    print('MI log-likelihood: ', mi_llf)
    print('MI residual degrees of freedom: ', mi_df_resid)
    
    # return last model results with mi results attached as new attributes (should use these attributes)
    res.mi_params = mi_res
    res.mi_llf = mi_llf
    res.mi_df_resid = mi_df_resid
    
    return res

# defines the log-likehood function. A is the set of accident data; N[i] is the proportion of crashes of type i, relative to type 1;
# thet[i] is the two-car crash relative risk of type i, relative to type 1; lamb[i] is the one-car crash relative risk of type i, relative to type 1

def _ll_lp(A, num_driver_types, thet, lamb):
    num_agg_rows = numpy.size(A,axis=0)

    # to simplify indexing, first convert the estimation sample into separate matrices, one for single-car and one for two-car
    A_1 = A[:,:num_driver_types] # one car crashes
    A_2 = numpy.zeros((num_agg_rows,num_driver_types,num_driver_types)) # two car crashes
    curr_col = num_driver_types
    for dto in range(0,num_driver_types):
        for dti in range(0,num_driver_types):
            if dti >= dto:
                A_2[:,dto,dti] = A[:,curr_col]
                curr_col += 1
    
    # add arrays of 1's to represent driver type 1 relative to themselves
    thet_1 = numpy.concatenate((numpy.ones(num_driver_types-1),thet)) 
    lamb_1 = numpy.concatenate((numpy.ones(num_driver_types-1),lamb))

    # first substitute in for N values: incorporate information from single car crashes using the fact that larger observed quantities 
    # of one type suggest more drivers on the road of that type
    N = numpy.ones((num_agg_rows,num_driver_types))
    for dt in range(0,num_driver_types): # count of a driver type relative to type 1
        N[:,dt] = (1/lamb_1[dt])*(A_1[:,dt]/A_1[:,0])
#   
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
                    
    # construct the likelihood function using the above components
    ll = numpy.zeros((num_agg_rows))
    two_veh_total = 0
    for dto in range(0,num_driver_types):
       for dti in range(0,num_driver_types):
           if dti >= dto:
               ll += A_2[:,dto,dti]*numpy.log(p[:,dto,dti]) 
               two_veh_total += A_2[:,dto,dti] # build the two-vehicle total while we're at it
    
    # add natural log of the factorial of total 2-car crashes (need to do this separately for each row )
    for i in range(0,num_agg_rows):
        ll[i] += lnfactorial(two_veh_total[i])
        for dto in range(0,num_driver_types):
            for dti in range(0,num_driver_types):
                if dti >= dto:
                    ll[i] -= lnfactorial(A_2[i,dto,dti])
        
    return ll

# create a new LP model class that inherits from GenericLikelihoodModel
class Lp(GenericLikelihoodModel):
    # endog is A (accident counts), and exog is num_driver_types
    def __init__(self, endog, exog=None, num_driver_types=2, extra_params_names=['theta','lambda'], **kwds):
        if exog is None:
            exog = numpy.zeros((numpy.size(endog,axis=0),2*(num_driver_types-1))) # LP doesn't have exogenous variables
        super(Lp, self).__init__(endog, exog, num_driver_types=2, extra_params_names=['theta','lambda'], **kwds)
        
    def nloglikeobs(self, params):
        thet = params[:(self.num_driver_types-1)]
        lamb = params[(self.num_driver_types-1):]
        return -_ll_lp(self.endog, self.num_driver_types, thet, lamb)
    
    def fit(self, start_params=None, maxiter=10000, maxfun=5000, **kwds):
        for xn in ['const','x1']:
            self.exog_names.remove(xn)
        if start_params == None:
            # reasonable starting values (assuming equal risk for each relative driver type)
            start_params = [[20*numpy.ones(self.num_driver_types-1)],[20*numpy.ones(self.num_driver_types-1)]]
        
        return super(Lp, self).fit(start_params=start_params, maxiter=maxiter, maxfun=maxfun, **kwds)