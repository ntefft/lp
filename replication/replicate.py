# -*- coding: utf-8 -*-
"""
Created on Wed May 15 11:37:00 2019

@author: Nathan Tefft

This script generates summary statistics and estimation analysis results for the Dunn and Tefft (2019)
replication of Levitt and Porter (2001).
"""
import os, pandas, random

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
from replication import util

# read in previously extracted and stored dataframes
df_accident = pandas.read_csv('replication\\data\\df_accident.csv')
df_accident.set_index(['year','st_case'],inplace=True) # set the index
df_vehicle = pandas.read_csv('replication\\data\\df_vehicle.csv')
df_vehicle.set_index(['year','st_case','veh_no'],inplace=True) # set the index
df_person = pandas.read_csv('replication\\data\\df_person.csv')
df_person.set_index(['year','st_case','veh_no','per_no'],inplace=True) # set the index

# set estimation parameters
# bsreps = 2 # bootstrap replicates for testing
bsreps = 100 # bootstrap replicates for replication
# mireps = 2 # multiple imputation replicates, for testing
mireps = 10 # multiple imputation replicates for replication (FARS includes a total of 10)
sy_p_t = 0.13 # state-year proportion missing threshold that best approximates L&P's results
# drinking definitions 1 through 4
drink_defs = ['police_report_only','any_evidence','police_report_primary','bac_test_primary']
# results_folder = 'replication\\results' # for saving estimation results
results_folder = 'replication\\temp' # for testing
if not os.path.exists(results_folder):
        os.makedirs(results_folder) # generate results directory, if it doesn't exist

# TABLE 1
# Data for Table 1: Outline of LP Replication Exercise 
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'police_report_only',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=True)
# Data for item 9 of Table 1: Outline of LP Replication Exercise  
# (definition 5 (supplemental analysis) so need only look at the section "FOR BOTTOM HALF OF TABLE 1" )
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=True)

# TABLE 2
# Data for Table 2: Distribution of police officer judgement of alcohol involvement and BAC test results (see section "Cross-tab for Table 2")
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'any_evidence',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=True)

# TABLE 4
# Data for Table 4 (top portion, definitions 1 through 4)
random.seed(1) # for exactly replicating the bootstrapped sample
for drink_def in drink_defs: 
    print("Calculating summary statistics for drinking definition: " + drink_def) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,drink_def,
                    bac_threshold=0,state_year_prop_threshold=1,mireps=False,summarize_sample=True)
# Data for Table 4 (last column, optimized to match L&P for missing state-years)
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'any_evidence',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=True)
# Data for Table 4 (bottom portion)
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0.10,state_year_prop_threshold=1,mireps=False,summarize_sample=True)
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0.10,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=True)

# TABLE 5, PANEL 1
random.seed(1) # for exactly replicating the bootstrapped sample
res_fmt = list() # list of results, formatted
for drink_def in drink_defs: 
    print("Estimating model for drinking definition: " + drink_def) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,drink_def,
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=False)
    mod_res,model_llf,model_df_resid = estimate.fit_model(analytic_sample,['year','state','weekend','hour'],2,bsreps)
    res_fmt.append([drink_def,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                 round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
print("Estimating multiple imputation model:") 
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'bac_test_primary',
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=mireps,summarize_sample=False)
mod_res,model_llf,model_df_resid = estimate.fit_model_mi(analytic_sample,['year','state','weekend','hour'],2,bsreps,mireps)
res_fmt.append(['multiple_imputation',round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                 round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['drink_def','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel(results_folder + '\\table5_panel1.xlsx') # Note: should format as text after opening Excel file

# TABLE 5, PANEL 2
random.seed(1) # for exactly replicating the bootstrapped sample
res_fmt = list() # list of results, formatted
print("Estimating model for drinking definition: any_evidence") 
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0.1,state_year_prop_threshold=1,mireps=False,summarize_sample=False)
mod_res,model_llf,model_df_resid = estimate.fit_model(analytic_sample,['year','state','weekend','hour'],2,bsreps)
res_fmt.append([drink_def,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
             round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
print("Estimating multiple imputation model:") 
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                        bac_threshold=0.1,state_year_prop_threshold=1,mireps=mireps,summarize_sample=False)
mod_res,model_llf,model_df_resid = estimate.fit_model_mi(analytic_sample,['year','state','weekend','hour'],2,bsreps,mireps)
res_fmt.append(['multiple_imputation',round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                 round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['drink_def','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel(results_folder + '\\table5_panel2.xlsx') # Note: should format as text after opening Excel file

# APPENDIX TABLE 1
random.seed(1) # for exactly replicating the bootstrapped sample
equal_mixings = [['all'],['hour'],['year','hour'],['year','weekend','hour'],['year','state','hour'],['year','state','weekend','hour']]
for drink_def in drink_defs:     
    res_fmt = list() # list of results, formatted
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,drink_def,
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=False)
    for eq_mix in equal_mixings: 
        print("Estimating model for drinking definition: " + drink_def) 
        mod_res,model_llf,model_df_resid = estimate.fit_model(analytic_sample,eq_mix,2,bsreps)
        res_fmt.append([eq_mix,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                     round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
    res_fmt_df = pandas.DataFrame(res_fmt,columns=['eq_mix','theta','theta_se','lambda','lambda_se','total_dof'])
    res_fmt_df.T.to_excel(results_folder + '\\tableA1_panel_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file    
res_fmt = list() # list of results, formatted
analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'bac_test_primary',
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=mireps,summarize_sample=False)
for eq_mix in equal_mixings: 
    print("Estimating multiple imputation model:")     
    mod_res,model_llf,model_df_resid = estimate.fit_model_mi(analytic_sample,eq_mix,2,bsreps,mireps)
    res_fmt.append([eq_mix,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                     round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['eq_mix','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel(results_folder + '\\tableA1_panel_multiple_imputation.xlsx') # Note: should format as text after opening Excel file

# APPENDIX FIGURE 1
random.seed(1) # for exactly replicating the bootstrapped sample
for drink_def in drink_defs: 
    res_fmt = list() # list of results, formatted
    for yr in range(1983,1994): 
        print("Estimating model for drinking definition " + drink_def + " in year " + str(yr)) 
        analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,yr,yr,20,4,drink_def,
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=False)
        mod_res,model_llf,model_df_resid = estimate.fit_model(analytic_sample,['year','state','weekend','hour'],2,bsreps)
        res_fmt.append([yr,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                     round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
    res_fmt_df = pandas.DataFrame(res_fmt,columns=['year','theta','theta_se','lambda','lambda_se','total_dof'])
    res_fmt_df.T.to_excel(results_folder + '\\figureA1_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file    

# APPENDIX FIGURE 2
random.seed(1) # for exactly replicating the bootstrapped sample
for drink_def in drink_defs: 
    res_fmt = list() # list of results, formatted
    for earliest_hour_raw in range(20,29): 
        if earliest_hour_raw > 23:
            earliest_hour = earliest_hour_raw - 24
        else:
            earliest_hour = earliest_hour_raw
        print("Estimating model for drinking definition " + drink_def + " in hour " + str(earliest_hour)) 
        analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,earliest_hour,earliest_hour,drink_def,
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=False)
        mod_res,model_llf,model_df_resid = estimate.fit_model(analytic_sample,['year','state','weekend','hour'],2,bsreps)
        res_fmt.append([earliest_hour,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                     round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
    res_fmt_df = pandas.DataFrame(res_fmt,columns=['hour','theta','theta_se','lambda','lambda_se','total_dof'])
    res_fmt_df.T.to_excel(results_folder + '\\figureA2_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file    

# APPENDIX FIGURE 3  
random.seed(1) # for exactly replicating the bootstrapped sample  
drink_def = 'police_report_primary'
res_fmt = list() # list of results, formatted
for yr in range(1983,1994): 
    print("Estimating model for drinking definition " + drink_def + " in year " + str(yr)) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,yr,yr,20,4,drink_def,
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=False)
    mod_res,model_llf,model_df_resid = estimate.fit_model(analytic_sample,['year','state','weekend','hour'],2,bsreps)
    res_fmt.append([yr,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                 round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel(results_folder + '\\figureA3_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file   
res_fmt = list() # list of results, formatted
for yr in range(1983,1994): 
    print("Estimating multiple imputation model in year " + str(yr)) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,yr,yr,20,4,'bac_test_primary',
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=mireps,summarize_sample=False)
    mod_res,model_llf,model_df_resid = estimate.fit_model_mi(analytic_sample,['year','state','weekend','hour'],2,bsreps,mireps)
    res_fmt.append([yr,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                     round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel(results_folder + '\\figureA3_multiple_imputation.xlsx') # Note: should format as text after opening Excel file

# APPENDIX FIGURE 4
random.seed(1) # for exactly replicating the bootstrapped sample
drink_def = 'police_report_primary'
res_fmt = list() # list of results, formatted
for earliest_hour_raw in range(20,29): 
    if earliest_hour_raw > 23:
        earliest_hour = earliest_hour_raw - 24
    else:
        earliest_hour = earliest_hour_raw    
    print("Estimating model for drinking definition " + drink_def + " in hour " + str(earliest_hour)) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,earliest_hour,earliest_hour,drink_def,
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=False,summarize_sample=False)
    mod_res,model_llf,model_df_resid = estimate.fit_model(analytic_sample,['year','state','weekend','hour'],2,bsreps)
    res_fmt.append([earliest_hour,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                 round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['hour','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel(results_folder + '\\figureA4_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file   
res_fmt = list() # list of results, formatted
for earliest_hour_raw in range(20,29): 
    if earliest_hour_raw > 23:
        earliest_hour = earliest_hour_raw - 24
    else:
        earliest_hour = earliest_hour_raw    
    print("Estimating multiple imputation model in hour " + str(earliest_hour)) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,earliest_hour,earliest_hour,'bac_test_primary',
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,mireps=mireps,summarize_sample=False)
    mod_res,model_llf,model_df_resid = estimate.fit_model_mi(analytic_sample,['year','state','weekend','hour'],2,bsreps,mireps)
    res_fmt.append([earliest_hour,round(mod_res[0][0][0],2),'('+str(round(mod_res[1][0][0],2))+')',
                     round(mod_res[0][1][0],2),'('+str(round(mod_res[1][1][0],2))+')',round(model_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['hour','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel(results_folder + '\\figureA4_multiple_imputation.xlsx') # Note: should format as text after opening Excel file
