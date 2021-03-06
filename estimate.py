# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 13:03:22 2019

@author: Nathan Tefft

This is a collection of functions used to create and estimate the LP model, including for multiple imputation.
"""
import pandas, numpy, random # import packages
from statsmodels.base.model import GenericLikelihoodModel

# converts the analytic sample (see the util.get_analytic_sample function) into a form that can be used in estimation
def get_estimation_sample(analytic_sample,equal_mixing,driver_types,mirep=False):
    estimation_sample = analytic_sample.copy()
    
    num_driver_types = len(driver_types)
    
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
    
    # need to store one-vehicle crash share parameters before dropping missing 
    one_veh_crash_ratio = numpy.zeros((num_driver_types-1))
    for i in range(0,(num_driver_types-1)):
        one_veh_crash_ratio[i] = estimation_sample['a_'+str(i+2)].sum()/estimation_sample['a_1'].sum()
    
    if 'all' not in equal_mixing:
        estimation_sample['a_miss'] = 0
        # drop observations where there are no (one-vehicle, driver type 1) or no (one-vehicle, driver type 2) crashes [otherwise, model won't converge]
        for dt in range(1,num_driver_types+1): 
            estimation_sample.loc[estimation_sample['a_' + str(dt)] == 0,'a_miss'] = 1
        estimation_sample = estimation_sample[estimation_sample['a_miss'] == 0]
        estimation_sample = estimation_sample.drop(columns=['a_miss'])
        
        print('Rows of estimation sample after dropping rows with zero single-car observations of any type: ')
        print(len(estimation_sample.index))
        
    estimation_sample.one_veh_crash_ratio = one_veh_crash_ratio # add attribute for use during estimation
    
    return estimation_sample

# fit the LP model using constructed estimation sample
#def fit_model(estimation_sample,num_driver_types,bsreps=100):           
def fit_model(analytic_sample,equal_mixing,driver_types,pairwise=True,init_rel_risk=10,bsreps=100,mirep=False,rseed=1,acc_bs=True):           
    random.seed(rseed) # for exactly replicating the bootstrapped sample
    num_driver_types = len(driver_types)
    start_params= [[init_rel_risk*numpy.ones(num_driver_types-1)],[init_rel_risk*numpy.ones(num_driver_types-1)]] # initial relative risk parameter value for estimation
    # dim 1: bootstrap replicate; dim 2: theta, lambda, N, eta; dim 3: driver types relative to type 1
    boot_results = numpy.zeros((bsreps,4,(num_driver_types-1)))
    # if not bootstrapping at the accident level, convert to estimation sample now, otherwise convert after bootstrapping
    if acc_bs==False:
        real_sample = get_estimation_sample(analytic_sample,equal_mixing,driver_types,mirep)
        one_veh_crash_ratio = real_sample.one_veh_crash_ratio
    else:
        real_sample = analytic_sample.copy()
    for bsr in range(0,bsreps):
        if bsr==0: # use the original sample
            boot_sample = real_sample.copy()
        else: # draw random samples for bootstrapping
            if acc_bs==False:
                boot_sample = real_sample.sample(frac=1,replace=True)
            else:                
                boot_sample = pandas.DataFrame(index=real_sample.index.droplevel('veh_no').unique()).sample(frac=1,replace=True)
                boot_sample = boot_sample.merge(real_sample.reset_index().set_index(['year','st_case']),on=['year','st_case']).reset_index().set_index(['year','st_case','veh_no'])
        if acc_bs==False:
            estimation_sample = boot_sample.copy()
        else:
            estimation_sample = get_estimation_sample(boot_sample,equal_mixing,driver_types,mirep)
            one_veh_crash_ratio = estimation_sample.one_veh_crash_ratio
        mod = Lp(estimation_sample,num_driver_types=num_driver_types,pairwise=pairwise) # create the model (modified GenericLikelihoodModel)    
        results = mod.fit(start_params=start_params,skip_hessian=True) # fit the model, skipping hessian calculation because we're bootstrapping
#        print(results.summary()) # summarize the model fit
        boot_results[bsr][0] = results.params[:(num_driver_types-1)] # theta
        boot_results[bsr][1] = results.params[(num_driver_types-1):] # lambda
        for i in range(0,(num_driver_types-1)): # N
            boot_results[bsr][2][i] = (1/boot_results[bsr][1][i])*one_veh_crash_ratio[i]   
        # P, the proportion of that driver type on the road (LP didn't assign a letter to this value)
        for i in range(0,(num_driver_types-1)):
            boot_results[bsr][3][i] = boot_results[bsr][2][i]/(1+numpy.sum(boot_results[bsr][2],axis=0))
        if bsr==0:
            model_llf = results.llf
            model_df_resid = results.df_resid
        print('([theta], [lambda], [N], [P]) estimated for bootstrap replicate '+str(bsr))
        print(boot_results[bsr])
        print('Log-likelihood: ', results.llf)
        print('Residual degrees of freedom: ', results.df_resid)
        
    # dim 1: estimate, std err; dim 2: theta, lambda, N, eta; dim 3: driver types relative to type 1
    final_results = numpy.zeros((2,4,(num_driver_types-1)))
    final_results[0] = boot_results[0]
    if bsreps>1:    
        final_results[1] = bs_se(boot_results,axis=0)
    else:
        final_results[1] = numpy.nan
    
    print('')
    print('PARAMETERS AND BOOTSTRAPPED STANDARD ERRORS')
    print('*******************')
    print('Parameters ([theta], [lambda], [N], [P]):')
    print(final_results[0])
    print('Bootstrapped standard errors ([theta], [lambda], [N], [P]):')
    print(final_results[1])
    print('Log-likelihood: ', model_llf)
    print('Residual degrees of freedom: ', model_df_resid)
    
    return final_results, model_llf, model_df_resid

# wrapper around fit_model which implements multiple imputation estimation. Generates estimates for each MI replicate, and then
# combines the results to produce final estimates and standard errors
def fit_model_mi(analytic_sample,equal_mixing,driver_types,pairwise=True,init_rel_risk=10,bsreps=100,mireps=10,rseed=1,acc_bs=True):    
    num_driver_types = len(driver_types)       
    # dimensions are mireps, estimates & standard errors, parameters, driver types relative to type 1
    results_params = numpy.zeros((mireps,2,4,(num_driver_types-1)))
    mi_llf = 0
    mi_df_resid = 0
    # loop over mi replicates and estimate model for each
    for mir in range(0,mireps):
        print('Estimating model for multiple imputation replicate ' + str(mir))
        mod_results, mod_llf, mod_df_resid = fit_model(analytic_sample,equal_mixing,driver_types,pairwise,init_rel_risk,bsreps,(mir+1),rseed,acc_bs)
        results_params[mir] = mod_results
        mi_llf += mod_llf/mireps
        mi_df_resid += mod_df_resid/mireps
    mi_results = mi_theta_se(results_params)
    
    # report relevant model statistics
    print('')
    print('MI PARAMETERS AND MI/BOOTSTRAPPED STANDARD ERRORS')
    print('*******************')
    print('MI Parameters ([theta], [lambda], [N], [P]):')
    print(mi_results[0])
    print('MI bootstrapped standard errors ([theta], [lambda], [N], [P]):')
    print(mi_results[1])
    print('MI log-likelihood: ', mi_llf)
    print('MI residual degrees of freedom: ', mi_df_resid)

    return mi_results, mi_llf, mi_df_resid

# defines the log-likehood function. A is the set of accident data; N[i] is the proportion of crashes of type i, relative to type 1;
# thet[i] is the two-car crash relative risk of type i, relative to type 1; lamb[i] is the one-car crash relative risk of type i, relative to type 1
# A can't be passed in as a pandas, so need to work with matrix indices
def _ll_lp(A, num_driver_types, pairwise, thet, lamb):    
    # print(thet)
    # print(lamb)
    num_agg_rows = numpy.size(A,axis=0)
    ll = numpy.zeros((num_agg_rows)) # log-likelihood
          
    if (pairwise == True): # For pairwise estimation, loop over pairs relative to the base type (first in driver type list)   
        # print('Running pairwise estimation model')    
        for dti in range(1,num_driver_types): # for each driver type index, build pairwise log-likelihood component                    
            A_1 = A[:,[0,dti]] # one car crashes
            A_2 = numpy.zeros((num_agg_rows,2,2)) # two car crashes
            curr_col = num_driver_types
            for dtout in range(0,num_driver_types):
                for dtin in range(0,num_driver_types):
                    if (dtin >= dtout) & (dtout in [0,dti]) & (dtin in [0,dti]):
                        A_2[:,int(dtout/dti),int(dtin/dti)] = A[:,curr_col]
                    if dtin >= dtout:
                        curr_col += 1                                    
            ll += _ll_lp_component(A_1, A_2, 2, [thet[(dti-1)]], [lamb[(dti-1)]])
    else: # For full estimation (more than two driver types), use all types simultaneously
        # to simplify indexing, first convert the estimation sample into separate matrices, one for single-car and one for two-car
        # print('Running full estimation model')
        A_1 = A[:,:num_driver_types] # one car crashes
        A_2 = numpy.zeros((num_agg_rows,num_driver_types,num_driver_types)) # two car crashes
        curr_col = num_driver_types
        for dtout in range(0,num_driver_types):
            for dtin in range(0,num_driver_types):
                if dtin >= dtout:
                    A_2[:,dtout,dtin] = A[:,curr_col]
                    curr_col += 1        
        ll += _ll_lp_component(A_1, A_2, num_driver_types, thet, lamb)
        
    return ll

def _ll_lp_component(A_1, A_2, num_driver_types, thet, lamb):
    num_agg_rows = numpy.size(A_1,axis=0)
    ll_component = numpy.zeros((num_agg_rows)) # log-likelihood
    
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
    for dtout in range(0,num_driver_types):
        for dtin in range(0,num_driver_types):
            p_denom += N[:,dtout]*N[:,dtin]*(thet_1[dtout]+thet_1[dtin])
    
    # next build the set of probabilities and add accidents
    p = numpy.zeros((num_agg_rows,num_driver_types,num_driver_types))
    for dtout in range(0,num_driver_types):
        for dtin in range(0,num_driver_types):
            if dtin >= dtout:
                p[:,dtout,dtin] = N[:,dtout]*N[:,dtin]*(thet_1[dtout]+thet_1[dtin])/p_denom
                if dtin != dtout:
                    p[:,dtout,dtin] = 2*p[:,dtout,dtin] # after eliminating the duplicates, need to add in the probability of observing the two types reversed
                    
    # construct the likelihood function using the above components
    two_veh_total = 0
    for dtout in range(0,num_driver_types):
       for dtin in range(0,num_driver_types):
           if dtin >= dtout:
               ll_component += A_2[:,dtout,dtin]*numpy.log(p[:,dtout,dtin]) 
               two_veh_total += A_2[:,dtout,dtin] # build the two-vehicle total while we're at it
    
    # add natural log of the factorial of total 2-car crashes (need to do this separately for each row )
    for i in range(0,num_agg_rows):
        ll_component[i] += lnfactorial(two_veh_total[i])
        for dtout in range(0,num_driver_types):
            for dtin in range(0,num_driver_types):
                if dtin >= dtout:
                    ll_component[i] -= lnfactorial(A_2[i,dtout,dtin])
                    
    return ll_component

# create a new LP model class that inherits from GenericLikelihoodModel
class Lp(GenericLikelihoodModel):
    # endog is A (accident counts), and exog is num_driver_types and pairwise
    def __init__(self, endog, exog=None, num_driver_types=2, pairwise=True, **kwds):
        extra_params_names = list()
        for dtr in range(2,(num_driver_types+1)):
            extra_params_names.append('theta' + str(dtr))
        for dtr in range(2,(num_driver_types+1)):
            extra_params_names.append('lambda' + str(dtr))
        if exog is None:
            exog = numpy.zeros((numpy.size(endog,axis=0),2*(num_driver_types-1))) # LP doesn't have exogenous variables
        super(Lp, self).__init__(endog, exog, num_driver_types=num_driver_types, pairwise=pairwise, extra_params_names=extra_params_names, **kwds)
        
    def nloglikeobs(self, params):
        thet = params[:(self.num_driver_types-1)]
        lamb = params[(self.num_driver_types-1):]
        return -_ll_lp(self.endog, self.num_driver_types, self.pairwise, thet, lamb)
    
    def fit(self, start_params=None, maxiter=10000, maxfun=5000, **kwds):
        self.exog_names.remove('const')
        for xn in range(1,(2*(self.num_driver_types-1))):
            self.exog_names.remove('x'+str(xn))
        
        return super(Lp, self).fit(start_params=start_params, maxiter=maxiter, maxfun=maxfun, **kwds)
        # return super(Lp, self).fit(maxiter=maxiter, maxfun=maxfun, **kwds)

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
    
    # loop through MI replicates and calculate square root for final standard errors
    for miidx in range(0,mireps): 
        mi_estimates[1] += numpy.power(reps_theta_se[miidx,1],2)/mireps + ((1+(1/mireps))/(mireps-1))*numpy.power(reps_theta_se[miidx,0]-mi_estimates[0],2)
    mi_estimates[1] = numpy.sqrt(mi_estimates[1])
    
    return mi_estimates