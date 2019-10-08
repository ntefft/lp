# -*- coding: utf-8 -*-
"""
Created on Wed May 15 11:37:00 2019

@author: ntefft
"""

import os, sys, pandas, time, numpy # import packages
import lpdtFit

# path for Spyder or Jupyter Notebooks
if os.path.exists(sys.path[0] + '\\Documents\\GitHub\\lpdt'):
    os.chdir(sys.path[0] + '\\Documents\\GitHub\\lpdt')
else:
    os.chdir(sys.path[0])
    
import lpdtUtil

# read in FARS data
df_accident = pandas.read_csv('data\\df_accident.csv')
df_accident.set_index(['year','st_case'],inplace=True) # set the index
df_vehicle = pandas.read_csv('data\\df_vehicle.csv')
df_vehicle.set_index(['year','st_case','veh_no'],inplace=True) # set the index
df_person = pandas.read_csv('data\\df_person.csv')
df_person.set_index(['year','st_case','veh_no','per_no'],inplace=True) # set the index

# get estimation sample
#A = lpdtutil.get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=1983, last_year=2017, equal_mixing=['year','weekend','hour'])
A = lpdtUtil.get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=1983, last_year=1993, 
#                    bac_threshold = 0.1, 
                    bac_threshold = 0, 
                    equal_mixing=['hour','year','state','weekend'], 
#                    equal_mixing=['hour'], 
                    drinking_definition = 'police_report_only')
#                    drinking_definition = 'any_evidence')

#A.to_csv('A.csv')
#A = pandas.read_csv('A_test.csv') # testing output from Stata to see if ML routine is the same...it is
#A.set_index(['hour','year','state','weekend'],inplace=True) # set the index
        
mod = lpdtFit.Lpdt(A, num_driver_types=2, extra_params_names=['theta','lambda'])
start = time.time()
res = mod.fit()
res.bootstrap(nrep=10) # get bootstrapped results
end = time.time()
print(mod.exog_names)
print(mod.endog_names)
print(res.summary())
print("time to fit: " + str(end-start))

print('Parameters: ', res.params)
print('Standard errors: ', res.bse)
print('P-values: ', res.pvalues)
print('AIC: ', res.aic)
print('Log-likelihood: ', res.llf)

theta_hat = res.params[0]
theta_hat_se = lpdtUtil.bs_se(res.bootstrap_results[:,0])
lambda_hat = res.params[1]
lambda_hat_se = lpdtUtil.bs_se(res.bootstrap_results[:,1])
N_hat = (1/lambda_hat)*(A['a_2'].sum()/A['a_1'].sum())
N_hat_se = lpdtUtil.bs_se((1/res.bootstrap_results[:,1])*(A['a_2'].sum()/A['a_1'].sum()))


dir(res)
print('Testing: ', res.model)
test = res.bootstrap(nrep=10)