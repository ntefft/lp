# -*- coding: utf-8 -*-
"""
Created on Wed May 15 11:37:00 2019

@author: ntefft
"""

import os, sys, pandas # import packages
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
sy_p_t = 0.13 # the value that best approximates L&P's results
drink_defs = ['police_report_only','any_evidence','police_report_primary','bac_test_primary'] # drinking definitions 1 through 4

## EXAMPLE REGULAR ESTIMATION
#analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'any_evidence',
#                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)
#mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
#print(mod_res.final_params)
#
## EXAMPLE MULTIPLE IMPUTATION ESTIMATION
#mod_results = lpdtFit.fit_model_mi(df_accident,df_vehicle,df_person,1983,1993,20,4,['year','state','weekend','hour'],'any_evidence',
#                    bac_threshold=0,state_year_prop_threshold=sy_p_t,bsreps=bsreps,mireps=10)
#print(mod_results.mi_params)
#print(mod_results.mi_llf)
#print(mod_results.mi_df_resid)

# TABLE 1
# Data for Table 1: Outline of LP Replication Exercise  (can ignore the estimation section, since Table 1 reports summary statistics)
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'police_report_only',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)
# Data for item 9 of Table 1: Outline of LP Replication Exercise  (definition has changed to definition 5, which runs the supplemental analysis, so need only look at the section "FOR BOTTOM HALF OF TABLE 1" )
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)

# TABLE 2
# Data for Table 2: Distribution of police officer judgement of alcohol involvement and BAC test results (see section "Cross-tab for Table 2")
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'any_evidence',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)

# TABLE 4
# Data for Table 4 (top portion, definitions 1 through 4)
for drink_def in drink_defs: 
    print("Calculating summary statistics for drinking definition: " + drink_def) 
    analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,drink_def,
                    bac_threshold=0,state_year_prop_threshold=1,mirep=False,summarize_sample=True)
# Data for Table 4 (last column, optimized to match L&P for missing state-years)
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'any_evidence',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)
# Data for Table 4 (bottom portion)
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0.10,state_year_prop_threshold=1,mirep=False,summarize_sample=True)
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0.10,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)

# TABLE 5
tab5_panel1 = list()
for drink_def in drink_defs: 
    print("Estimating model for drinking definition: " + drink_def) 
    analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,drink_def,
                        bac_threshold=0,state_year_prop_threshold=0.13,mirep=False,summarize_sample=False)
    mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
    tab5_panel1.append([drink_def,mod_res.final_params[0],mod_res.final_params[1],mod_res.df_resid])
