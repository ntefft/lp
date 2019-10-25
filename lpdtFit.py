# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 13:03:22 2019

@author: Nathan Tefft
"""
import numpy, time # import packages
import lpdtUtil
from statsmodels.base.model import GenericLikelihoodModel

def fit_model(analytic_sample, df_vehicle, df_person, 
              equal_mixing=['year','state','weekend','hour'], drinking_definition='any_evidence', 
              bac_threshold = 0.08, bsreps=100, mirep=0):           
    
    est_sample = lpdtUtil.get_estimation_sample(analytic_sample, df_vehicle, df_person, 
                                equal_mixing,drinking_definition, bac_threshold, mirep)
    
    mod = Lpdt(est_sample)
    start = time.time()
    res = mod.fit()
        
    res.bootstrap(nrep=bsreps) # get bootstrapped results
    end = time.time()
    print(mod.exog_names)
    print(mod.endog_names)
    print(res.summary())
    print("time to fit: " + str(end-start))

    # row 0 = theta, row 1 = lambda, row 2 = N
    # column 0 = estimate, column 1 = bootstrapped standard error
    res.final_params = numpy.column_stack((res.params,lpdtUtil.bs_se(res.bootstrap_results,axis=0)))
    res.final_params = numpy.vstack([res.final_params,[(1/res.params[1])*(est_sample['a_2'].sum()/est_sample['a_1'].sum()),lpdtUtil.bs_se((1/res.bootstrap_results[:,1])*(est_sample['a_2'].sum()/est_sample['a_1'].sum()))]])
    
    print('Parameters (theta, lambda, N): ', res.final_params[:,0])
    print('Bootstrap standard errors (theta, lambda, N): ', res.final_params[:,1])
    print('Log-likelihood: ', res.llf)
    print('Residual degrees of freedom: ', res.df_resid)
    
    return res

def fit_model_mi(df_accident, df_vehicle, df_person, first_year=2017, last_year=2017, earliest_hour=20, 
                               latest_hour=4, equal_mixing=['year','state','weekend','hour'], drinking_definition='any_evidence', 
                               bac_threshold = 0.08, state_year_prop_threshold = 0.13, bsreps=100, mireps=10):           
    
    res_params = numpy.zeros((mireps, 3, 2))
    mi_res = numpy.zeros((3, 2))
    mi_llf = 0
    mi_df_resid = 0
    # loop over mi replicates and estimate model
    for i in range(0,mireps):
        analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,first_year,
                        last_year,earliest_hour,latest_hour,drinking_definition,bac_threshold, 
                        state_year_prop_threshold,mirep=(i+1),summarize_sample=False)
        res = fit_model(analytic_sample,df_vehicle,df_person,equal_mixing, 
                        drinking_definition,bac_threshold,bsreps,mirep=(i+1))
        res_params[i] = res.final_params
        mi_res[:,0] += res_params[i,:,0]/mireps # add estimate to running mean of estimates
        mi_llf += res.llf
        mi_df_resid = res.df_resid
        
    # loop again to calculate standard errors
    for i in range(0,mireps): 
        mi_res[:,1] += numpy.power(res_params[i,:,1],2)/mireps + ((1+1/mireps)/(mireps-1))*numpy.power(res_params[i,:,1]-mi_res[:,1],2)
        
    print('MI Parameters (theta, lambda, N): ', mi_res[:,0])
    print('MI bootstrap standard errors (theta, lambda, N): ', mi_res[:,1])
    print('MI log-likelihood: ', mi_llf)
    print('MI residual degrees of freedom: ', mi_df_resid)
    
    # return last model results with mi results attached
    res.mi_params = mi_res
    res.mi_llf = mi_llf
    res.mi_df_resid = mi_df_resid
    
    return res

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
    def __init__(self, endog, exog=None, num_driver_types=2, extra_params_names=['theta','lambda'], **kwds):
        if exog is None:
            exog = numpy.zeros((numpy.size(endog,axis=0),2*(num_driver_types-1))) # we don't have exogenous variables in our model
        super(Lpdt, self).__init__(endog, exog, num_driver_types=2, extra_params_names=['theta','lambda'], **kwds)
        
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
