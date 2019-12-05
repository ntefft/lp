# -*- coding: utf-8 -*-
"""
Created on Nov 13 2019

@author: Nathan Tefft

This script generates summary statistics and estimation analysis results for the Dunn and Tefft (2019)
drinking with children analysis.
"""
import os, pandas

"""
   USER-DEFINED ATTRIBUTES 
      
1) The working directory.
    The user MUST set their own working directory before running the script. 
    We recommend the folder of the cloned GitHub repository.
        For example, set the working directory to "C:\\Users\\JoeEconomist\\GitHub\\lp"
    Results will then be placed into the project results subfolder (specified below)
"""

# import LP utility and model fit functions
import estimate
from children import util

# read in previously extracted and stored dataframes
df_accident = pandas.read_csv('children\\data\\df_accident.csv')
df_accident.set_index(['year','st_case'],inplace=True) # set the index
df_vehicle = pandas.read_csv('children\\data\\df_vehicle.csv')
df_vehicle.set_index(['year','st_case','veh_no'],inplace=True) # set the index
df_person = pandas.read_csv('children\\data\\df_person.csv')
df_person.set_index(['year','st_case','veh_no','per_no'],inplace=True) # set the index

# set estimation parameters
bsreps = 2 # bootstrap replicates for testing
#bsreps = 100 # bootstrap replicates for analysis
mireps = 2 # multiple imputation replicates, for testing
#mireps = 10 # multiple imputation replicates for analysis (FARS includes a total of 10)
# drinking definitions 1 through 4
drink_defs = ['police_report_only','any_evidence','police_report_primary','bac_test_primary']
#results_folder = 'children\\results' # for saving estimation results
results_folder = 'children\\temp' # for testing
if not os.path.exists(results_folder):
        os.makedirs(results_folder) # generate results directory, if it doesn't exist

# TEST CODE
res_fmt = list() # list of results, formatted
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1982,2017,20,4,'bac_test_primary',
                    bac_threshold=0,state_year_prop_threshold=1,mireps=False,summarize_sample=False)
mod_res, mod_llf, mod_df_resid = estimate.fit_model(analytic_sample,['year'],4,bsreps=2)
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1982,2017,20,4,'bac_test_primary',
                    bac_threshold=0,state_year_prop_threshold=1,mireps=10,summarize_sample=False)
mod_res, mod_llf, mod_df_resid = estimate.fit_model_mi(analytic_sample,['year'],4,bsreps=5,mireps=10)
