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

# set some overall parameters
bsreps = 3

# Data for Table 1: Outline of LP Replication Exercise  (can ignore the estimation section, since Table 1 reports summary statistics)
est_sample = lpdtUtil.get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=1983, 
                last_year=1993,equal_mixing=['weekend'],drinking_definition='police_report_only', 
                bac_threshold=0,state_year_prop_threshold=0,summarize_sample=True)

mod_res = lpdtFit.fit_model(df_accident,df_vehicle,df_person,first_year=1983,last_year=1993,
                equal_mixing=['weekend'],drinking_definition = 'police_report_only',
                bac_threshold=0,state_year_prop_threshold=0,bsreps=bsreps,summarize_sample=False)
print(mod_res.final_params)

# Data for Table 2: Distribution of police officer judgement of alcohol involvement and BAC test results (see section "Cross-tab for Table 2")
mod_res = lpdtFit.fit_model(df_accident,df_vehicle,df_person,first_year=1983,last_year=1993,
                                equal_mixing=['year','state','weekend','hour'],
                                drinking_definition = 'any_evidence',
                                bac_threshold=0.13,state_year_prop_threshold=0,bsreps=bsreps)
print(mod_res.final_params)





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
