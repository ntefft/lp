# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 13:03:22 2019

@author: Nathan Tefft

This is a collection of functions used to create and estimate the LP model, including for multiple imputation.
"""
import numpy, time # import packages
from statsmodels.base.model import GenericLikelihoodModel

# converts the analytic sample (see the util.get_analytic_sample function) into a form that can be used in estimation
def get_estimation_sample(analytic_sample,equal_mixing,num_driver_types,mirep=False):
    start = time.time()
    print("Building the estimation sample...")
    estimation_sample = analytic_sample.copy()
    
    if mirep==False:
        mirep_suf = ''
    else:
        mirep_suf = str(mirep)
    
    # reset index for unstacking by veh_no, and keep vehicle count and driver_type
    estimation_sample['veh_no2'] = estimation_sample.groupby(['year','st_case']).cumcount()+1
    idx_add_veh_no2 = ['year','st_case','veh_no2']
    if 'all' not in equal_mixing:
        idx_add_veh_no2 = equal_mixing + idx_add_veh_no2
    estimation_sample = estimation_sample.reset_index().set_index(idx_add_veh_no2)[['acc_veh_count','driver_type'+mirep_suf]]
    estimation_sample = estimation_sample.unstack()    
    
    # identify one-car crashes, looping over driver types
    for dt in range(1,num_driver_types+1): 
        estimation_sample['a_' + str(dt)] = 0
        estimation_sample.loc[(estimation_sample['acc_veh_count'][1] == 1) & (estimation_sample['driver_type'+mirep_suf][1] == dt),'a_' + str(dt)] = 1

    # identify two-car crashes, looping over driver types
    for dt1 in range(1,num_driver_types+1): 
        for dt2 in range(1,num_driver_types+1): 
            estimation_sample['a_' + str(dt1) + '_' + str(dt2)] = 0
            estimation_sample.loc[(estimation_sample['acc_veh_count'][1] == 2) & (estimation_sample['driver_type'+mirep_suf][1] == dt1) & (estimation_sample['driver_type'+mirep_suf][2] == dt2),'a_' + str(dt1) + '_' + str(dt2)] = 1
            if dt1 > dt2: # combine duplicates and drop duplicated columns
                estimation_sample['a_' + str(dt2) + '_' + str(dt1)] = estimation_sample['a_' + str(dt2) + '_' + str(dt1)] + estimation_sample['a_' + str(dt1) + '_' + str(dt2)]
                estimation_sample = estimation_sample.drop(columns=['a_' + str(dt1) + '_' + str(dt2)])
            
    # clean up dataset and collapse by equal mixing
    estimation_sample = estimation_sample.drop(columns=['acc_veh_count','driver_type'+mirep_suf])
    estimation_sample.columns = estimation_sample.columns.droplevel(level='veh_no2')
    if 'all' not in equal_mixing:
        estimation_sample = estimation_sample.groupby(equal_mixing).sum()
    else:
        estimation_sample = estimation_sample.sum().to_frame().transpose()
    print('Rows of estimation sample after collapsing by equal mixing: ')
    print(len(estimation_sample.index))
    if 'all' not in equal_mixing:
        # drop observations where there are no (one-vehicle, driver type 1) or no (one-vehicle, driver type 2) crashes [otherwise, model won't converge]
        estimation_sample['a_miss'] = 0
        for dt in range(1,num_driver_types+1): 
            estimation_sample.loc[estimation_sample['a_' + str(dt)] == 0,'a_miss'] = 1
        estimation_sample = estimation_sample[estimation_sample['a_miss'] == 0]
        estimation_sample = estimation_sample.drop(columns=['a_miss'])
        print('Rows of estimation sample after dropping rows with zero single-car observations of either type: ')
        print(len(estimation_sample.index))
    
    print('Describing final estimation sample: ')
    print(estimation_sample.describe())

    end = time.time()
    print("Time to build estimation sample: " + str(end-start))
    return estimation_sample

# fit the LP model using constructed estimation sample
def fit_model(estimation_sample,bsreps=100):           
    start = time.time()
    mod = Lp(estimation_sample) # create the model (modified GenericLikelihoodModel)
    res = mod.fit() # fit the model
    res.bootstrap(nrep=bsreps) # get bootstrapped results
    print(mod.exog_names)
    print(mod.endog_names)
    print(res.summary())
    end = time.time()
    print("Time to fit model: " + str(end-start))
    
    # add final_params attribute to the fit model, which captures the relevant estimates and standard errors
    # row 0 = estimate, row 1 = bootstrapped standard error
    # col 0 = theta, col 1 = lambda, col 2 = N
    res.final_params = numpy.zeros((2,3))
    res.final_params[0] = numpy.concatenate((res.params,(1/res.params[1])*(estimation_sample['a_2'].sum()/estimation_sample['a_1'].sum())),axis=None)
    res.final_params[1] = numpy.concatenate((bs_se(res.bootstrap_results,axis=0),bs_se((1/res.bootstrap_results[:,1])*(estimation_sample['a_2'].sum()/estimation_sample['a_1'].sum()))),axis=None)
#    res.final_params = numpy.row_stack((res.params,bs_se(res.bootstrap_results,axis=0)))
#    res.final_params = numpy.hstack([res.final_params,[(1/res.params[1])*(estimation_sample['a_2'].sum()/estimation_sample['a_1'].sum()),bs_se((1/res.bootstrap_results[:,1])*(estimation_sample['a_2'].sum()/estimation_sample['a_1'].sum()))]])
    
    # report relevant model statistics
    print('Parameters (theta, lambda, N): ', res.final_params[0])
    print('Bootstrap standard errors (theta, lambda, N): ', res.final_params[1])
    print('Log-likelihood: ', res.llf)
    print('Residual degrees of freedom: ', res.df_resid)
    
    return res

# wrapper around fit_model which implements multiple imputation estimation. Generates estimates for each MI replicate, and then
# combines the results to produce final estimates and standard errors
def fit_model_mi(analytic_sample,equal_mixing,num_driver_types,bsreps=100,mireps=10):           
    # dimensions are mireps, estimates & standard errors, and finally the parameters
    res_params = numpy.zeros((mireps,2,3))
    mi_res = numpy.zeros((2,3))
    mi_llf = 0
    mi_df_resid = 0
    # loop over mi replicates and estimate model for each
    for i in range(0,mireps):
        estimation_sample = get_estimation_sample(analytic_sample,equal_mixing,
                                                  num_driver_types,mirep=(i+1))
        res = fit_model(estimation_sample,bsreps)
        res_params[i] = res.final_params
        mi_llf += res.llf
        mi_df_resid = res.df_resid
    
    # get MI estimates and standard errors
    mi_res = mi_theta_se(res_params)

    # report relevant model statistics
    print('MI Parameters (theta, lambda, N): ', mi_res[0])
    print('MI bootstrap standard errors (theta, lambda, N): ', mi_res[1])
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

# generate the MI estimates of thetas and standard errors    
# reps_theta_se: dimension 1 is MI replicate, dimension 2 is estimates (0) and standard errors (1), the remaining dimensions contain the values
def mi_theta_se(reps_theta_se, axis=0):
    mi_estimates = numpy.zeros(reps_theta_se.mean(axis=axis).shape)
    mireps = reps_theta_se.shape[0]
    
    # average across MI replicates for final estimate
    mi_estimates[0] = reps_theta_se[:,0].mean(axis=axis)
    
    # loop through MI replicates for final standard errors
    for miidx in range(0,mireps): 
        mi_estimates[1] += numpy.power(reps_theta_se[miidx,1],2)/mireps + ((1+(1/mireps))/(mireps-1))*numpy.power(reps_theta_se[miidx,0]-mi_estimates[0],2)
        
    return mi_estimates