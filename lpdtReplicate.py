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

# EXAMPLE REGULAR ESTIMATION
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'any_evidence',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)
mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
print(mod_res.final_params)

# EXAMPLE MULTIPLE IMPUTATION ESTIMATION
mod_results = lpdtFit.fit_model_mi(df_accident,df_vehicle,df_person,1983,1993,20,4,['year','state','weekend','hour'],'any_evidence',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,bsreps=bsreps,mireps=10)
print(mod_results.mi_params)
print(mod_results.mi_llf)
print(mod_results.mi_df_resid)

# Data for Table 1: Outline of LP Replication Exercise  (can ignore the estimation section, since Table 1 reports summary statistics)
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'police_report_only',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)

# Data for bottom of Table 1: Outline of LP Replication Exercise  (definition has changed to definition 5, which runs the supplemental analysis, so need only look at the section "FOR BOTTOM HALF OF TABLE 1" )
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)

# Data for Table 2: Distribution of police officer judgement of alcohol involvement and BAC test results (see section "Cross-tab for Table 2")
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'any_evidence',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)

# Data for Table 4 (top portion)
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'any_evidence',
                    bac_threshold=0,state_year_prop_threshold=0.2,mirep=False,summarize_sample=True)

# Data for Table 4 (bottom portion)
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0,state_year_prop_threshold=0.2,mirep=False,summarize_sample=True)
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0,state_year_prop_threshold=0.13,mirep=False,summarize_sample=True)
