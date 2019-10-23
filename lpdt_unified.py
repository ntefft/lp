# -*- coding: utf-8 -*-
"""
Created on Wed May 15 11:37:00 2019

@author: ntefft
"""

import os, sys, pandas, numpy # import packages
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

## EXAMPLE REGULAR ESTIMATION
#mod_results = lpdtFit.fit_model(df_accident, df_vehicle, df_person, 
#                    first_year=1983, 
#                    last_year=1993, 
##                    equal_mixing=['hour'], 
#                    equal_mixing=['year','state','weekend','hour'], 
##                    drinking_definition='police_report_primary', 
#                    drinking_definition = 'bac_test_primary',                                     
##                    bac_threshold = 0.1, 
#                    bac_threshold = 0, 
#                    state_year_prop_threshold = 0.13,
##                    state_year_prop_threshold = 0.12, # closest restriction to L&P's sample size
#                    bsreps=3)
#print(mod_results.final_params)



# EXAMPLE MULTIPLE IMPUTATION ESTIMATION
mod_results = lpdtFit.fit_model_mi(df_accident, df_vehicle, df_person, 
                    first_year=1983, 
                    last_year=1993, 
#                    equal_mixing=['hour'], 
                    equal_mixing=['year','state','weekend','hour'],
                    drinking_definition = 'bac_test_primary',                                     
#                    bac_threshold = 0.1, 
                    bac_threshold = 0,
                    bsreps=3)
print(mod_results.mi_params)
print(mod_results.mi_llf)
print(mod_results.mi_df_resid)



## CODE USED TO BUILD MULTIPLE IMPUTATION ESTIMATION...LIKELY DON'T NEED ANYMORE
#
#mireps = 10
#mod_results_params = numpy.zeros((mireps, 3, 2))
#mi_results = numpy.zeros((3, 2))
#mi_llf = 0
#mi_df_resid = 0
## loop over mi replicates and estimate model
#for i in range(0,mireps): 
#    A = lpdtUtil.get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=1983, last_year=1993, 
#    #                    bac_threshold = 0.1, 
#                        bac_threshold = 0, 
##                        equal_mixing=['hour','year','state','weekend'], 
#                        equal_mixing=['hour'], 
#    #                    drinking_definition = 'police_report_only')
#    #                    drinking_definition = 'any_evidence')
#                        drinking_definition = 'bac_test_primary',
#                        mirep = (i+1))                    
#    mod_results = lpdtFit.fit_model(A, bsreps=3)
#    mod_results_params[i] = mod_results.final_params
#    mi_results[:,0] += mod_results_params[i,:,0]/mireps # add estimate to running mean of estimates
#    mi_llf += mod_results.llf
#    mi_df_resid = mod_results.df_resid
#    
## loop again to calculate standard errors
#for i in range(0,mireps): 
#    mi_results[:,1] += numpy.power(mod_results_params[i,:,1],2)/mireps + ((1+1/mireps)/(mireps-1))*numpy.power(mod_results_params[i,:,1]-mi_results[:,1],2)
#    
#print('MI Parameters (theta, lambda, N): ', mi_results[:,0])
#print('MI bootstrap standard errors (theta, lambda, N): ', mi_results[:,1])
#print('MI log-likelihood: ', mi_llf)
#print('MI residual degrees of freedom: ', mi_df_resid)
