# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 13:03:22 2019

@author: Nathan Tefft

This is a collection of functions used to create and estimate the LP model, including for multiple imputation.
"""
import pandas, numpy, time # import packages
from statsmodels.base.model import GenericLikelihoodModel

# converts the analytic sample (see the util.get_analytic_sample function) into a form that can be used in estimation
def get_estimation_sample(analytic_sample,equal_mixing,num_driver_types,mirep=False):
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

    return estimation_sample

# fit the LP model using constructed estimation sample
#def fit_model(estimation_sample,num_driver_types,bsreps=100):           
def fit_model(analytic_sample,equal_mixing,num_driver_types,bsreps=100,mirep=False):           
    # dim 1: bootstrap replicate; dim 2: theta, lambda, N; dim 3: driver types relative to type 1
    boot_results = numpy.zeros((bsreps,3,(num_driver_types-1)))
    for bsr in range(0,bsreps):
        if bsr==0: # use the original sample
            boot_analytic_sample = analytic_sample.copy()
        else: # draw random samples within each year for bootstrapping
            boot_analytic_sample = pandas.DataFrame(index=analytic_sample.index.droplevel('veh_no').unique()).sample(frac=1,replace=True)
            boot_analytic_sample = boot_analytic_sample.merge(analytic_sample.reset_index().set_index(['year','st_case']),on=['year','st_case']).reset_index().set_index(['year','st_case','veh_no'])
                # for now, fully resample, but might consider resampling by equal_mixing
#                test = analytic_sample.groupby(equal_mixing).apply(lambda x: x.sample(frac=1,replace=True))
        estimation_sample = get_estimation_sample(boot_analytic_sample,equal_mixing,num_driver_types,mirep)
        mod = Lp(estimation_sample,num_driver_types=num_driver_types) # create the model (modified GenericLikelihoodModel)    
        results = mod.fit(skip_hessian=True) # fit the model, skipping hessian calculation because we're bootstrapping
#        print(results.summary()) # summarize the model fit
        boot_results[bsr][0] = results.params[:(num_driver_types-1)] # thetas
        boot_results[bsr][1] = results.params[(num_driver_types-1):] # lambdas
        for i in range(0,(num_driver_types-1)): # Ns
            boot_results[bsr][2][i] = (1/boot_results[bsr][1][i])*(estimation_sample['a_'+str(i+2)].sum()/estimation_sample['a_1'].sum())        
        if bsr==0:
            model_llf = results.llf
            model_df_resid = results.df_resid
        print('([theta], [lambda], [N]) estimated for bootstrap replicate '+str(bsr))
        print(boot_results[bsr])
        print('Log-likelihood: ', results.llf)
        print('Residual degrees of freedom: ', results.df_resid)
        
    # dim 1: estimate, std err; dim 2: theta, lambda, N; dim 3: driver types relative to type 1
    final_results = numpy.zeros((2,3,(num_driver_types-1)))
    final_results[0] = boot_results[0]
    final_results[1] = bs_se(boot_results,axis=0)
    
    print('')
    print('PARAMETERS AND BOOTSTRAPPED STANDARD ERRORS')
    print('*******************')
    print('Parameters ([theta], [lambda], [N]):')
    print(final_results[0])
    print('Bootstrapped standard errors ([theta], [lambda], [N]):')
    print(final_results[1])
    print('Log-likelihood: ', model_llf)
    print('Residual degrees of freedom: ', model_df_resid)
    
    return final_results, model_llf, model_df_resid

# wrapper around fit_model which implements multiple imputation estimation. Generates estimates for each MI replicate, and then
# combines the results to produce final estimates and standard errors
def fit_model_mi(analytic_sample,equal_mixing,num_driver_types,bsreps=100,mireps=10):           
    # dimensions are mireps, estimates & standard errors, parameters, driver types relative to type 1
    results_params = numpy.zeros((mireps,2,3,(num_driver_types-1)))
    mi_llf = 0
    mi_df_resid = 0
    # loop over mi replicates and estimate model for each
    for mir in range(0,mireps):
        print('Estimating model for multiple imputation replicate ' + str(mir))
        mod_results, mod_llf, mod_df_resid = fit_model(analytic_sample,equal_mixing,num_driver_types,bsreps,(mir+1))
        results_params[mir] = mod_results
        mi_llf += mod_llf/mireps
        mi_df_resid += mod_df_resid/mireps
    mi_results = mi_theta_se(results_params)
    
    # report relevant model statistics
    print('')
    print('MI PARAMETERS AND MI/BOOTSTRAPPED STANDARD ERRORS')
    print('*******************')
    print('MI Parameters (theta, lambda, N):')
    print(mi_results[0])
    print('MI bootstrapped standard errors (theta, lambda, N):')
    print(mi_results[1])
    print('MI log-likelihood: ', mi_llf)
    print('MI residual degrees of freedom: ', mi_df_resid)

    return mi_results, mi_llf, mi_df_resid

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
    def __init__(self, endog, exog=None, num_driver_types=2, **kwds):
        extra_params_names = list()
        for dtr in range(2,(num_driver_types+1)):
            extra_params_names.append('theta' + str(dtr))
        for dtr in range(2,(num_driver_types+1)):
            extra_params_names.append('lambda' + str(dtr))
        if exog is None:
            exog = numpy.zeros((numpy.size(endog,axis=0),2*(num_driver_types-1))) # LP doesn't have exogenous variables
        super(Lp, self).__init__(endog, exog, num_driver_types=num_driver_types, extra_params_names=extra_params_names, **kwds)
        
    def nloglikeobs(self, params):
        thet = params[:(self.num_driver_types-1)]
        lamb = params[(self.num_driver_types-1):]
        return -_ll_lp(self.endog, self.num_driver_types, thet, lamb)
    
    def fit(self, start_params=None, maxiter=10000, maxfun=5000, **kwds):
        self.exog_names.remove('const')
        for xn in range(1,(2*(self.num_driver_types-1))):
            self.exog_names.remove('x'+str(xn))
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