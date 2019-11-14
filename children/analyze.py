# -*- coding: utf-8 -*-
"""
Created on Nov 13 2019

@author: Nathan Tefft

This script generates summary statistics and estimation analysis results for the Dunn and Tefft (2019)
drinking with children analysis.
"""
import os, sys, pandas, pickle
# change working directory to GitHub path
os.chdir(sys.path[0] + '\\Documents\\GitHub\\lp')

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
res_pkl = list() # pickled results for later use
res_fmt = list() # list of results, formatted
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1982,2017,20,4,'bac_test_primary',
                    bac_threshold=0,state_year_prop_threshold=1,mireps=False,summarize_sample=False)
mod_res, mod_llf, mod_df_resid = estimate.fit_model(analytic_sample,['year'],4,bsreps=2)
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1982,2017,20,4,'bac_test_primary',
                    bac_threshold=0,state_year_prop_threshold=1,mireps=10,summarize_sample=False)
mod_res, mod_llf, mod_df_resid = estimate.fit_model_mi(analytic_sample,['year'],4,bsreps=5,mireps=10)




equal_mixings = [['all'],['hour'],['year','hour'],['year','weekend','hour'],['year','state','hour'],['year','state','weekend','hour']]
for drink_def in drink_defs:     
    res_fmt = list() # list of results, formatted
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,drink_def,
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=False)
    for eq_mix in equal_mixings: 
        print("Estimating model for drinking definition: " + drink_def) 
        mod_res = estimate.fit_model(estimate.get_estimation_sample(analytic_sample,eq_mix,2),bsreps)
        res_pkl.append([drink_def,eq_mix,mod_res])
        res_fmt.append([eq_mix,round(mod_res.final_params[0][0],2),'('+str(round(mod_res.final_params[1][0],2))+')',
                     round(mod_res.final_params[0][1],2),'('+str(round(mod_res.final_params[1][1],2))+')',(mod_res.df_resid+2)])
    res_fmt_df = pandas.DataFrame(res_fmt,columns=['eq_mix','theta','theta_se','lambda','lambda_se','total_dof'])
    res_fmt_df.T.to_excel(results_folder + '\\tableA1_panel_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file    

