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

"""
DRIVER TYPES:
    1) Sober and driving with children
    2) Sober and driving without children
    3) Drinking and driving with children
    4) Drinking and driving without children

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
mod_res, mod_llf, mod_df_resid = estimate.fit_model(analytic_sample,['year'],4,bsreps=bsreps)
res_fmt.append([round(mod_res[0][0][0],2),round(mod_res[0][0][1],2),round(mod_res[0][0][2],2),round(mod_res[0][1][0],2),round(mod_res[0][1][1],2),round(mod_res[0][1][2],2),round(mod_res[0][3][0],6),round(mod_res[0][3][1],6),round(mod_res[0][3][2],6)])
res_fmt.append(['('+str(round(mod_res[1][0][0],2))+')','('+str(round(mod_res[1][0][1],2))+')','('+str(round(mod_res[1][0][2],2))+')','('+str(round(mod_res[1][1][0],2))+')','('+str(round(mod_res[1][1][1],2))+')','('+str(round(mod_res[1][1][2],2))+')','('+str(format(round(mod_res[1][3][0],5),'.5f'))+')','('+str(format(round(mod_res[1][3][1],5),'.5f'))+')','('+str(format(round(mod_res[1][3][2],5),'.5f'))+')'])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['theta2','theta3','theta4','lambda2','lambda3','lambda4','proportion2','proportion3','proportion4'])
res_fmt_df.to_excel(results_folder + '\\test_results.xlsx') # Note: should format as text after opening Excel file