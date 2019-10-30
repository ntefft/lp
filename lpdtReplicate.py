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
#bsreps = 2
bsreps = 100
#mireps = 2
mireps = 10
sy_p_t = 0.13 # the value that best approximates L&P's results
drink_defs = ['police_report_only','any_evidence','police_report_primary','bac_test_primary'] # drinking definitions 1 through 4
if not os.path.exists('results'):
        os.makedirs('results') # generate results directory, if it doesn't exist

## EXAMPLE REGULAR ESTIMATION
#analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'any_evidence',
#                    bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=True)
#mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
#print(mod_res.final_params)
#
## EXAMPLE MULTIPLE IMPUTATION ESTIMATION
#mod_res = lpdtFit.fit_model_mi(df_accident,df_vehicle,df_person,1983,1993,20,4,['year','state','weekend','hour'],'any_evidence',
#                    bac_threshold=0,state_year_prop_threshold=sy_p_t,bsreps=bsreps,mireps=mireps)
#print(mod_res.mi_params)
#print(mod_res.mi_llf)
#print((mod_res.mi_df_resid+2))

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

# TABLE 5, PANEL 1
res_fmt = list() # list of results, formatted
for drink_def in drink_defs: 
    print("Estimating model for drinking definition: " + drink_def) 
    analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,drink_def,
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=False)
    mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
    res_fmt.append([drink_def,round(mod_res.final_params[0][0],2),'('+str(round(mod_res.final_params[0][1],2))+')',
                 round(mod_res.final_params[1][0],2),'('+str(round(mod_res.final_params[1][1],2))+')',(mod_res.df_resid+2)])
print("Estimating multiple imputation model:") 
mod_res = lpdtFit.fit_model_mi(df_accident,df_vehicle,df_person,1983,1993,20,4,['year','state','weekend','hour'],'bac_test_primary',
                    bac_threshold=0,state_year_prop_threshold=sy_p_t,bsreps=bsreps,mireps=mireps)
res_fmt.append(['multiple_imputation',round(mod_res.mi_params[0][0],2),'('+str(round(mod_res.mi_params[0][1],2))+')',
                 round(mod_res.mi_params[1][0],2),'('+str(round(mod_res.mi_params[1][1],2))+')',(mod_res.mi_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['drink_def','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel('results\\table5_panel1.xlsx') # Note: should format as text after opening Excel file

# TABLE 5, PANEL 2
res_fmt = list() # list of results, formatted
print("Estimating model for drinking definition: any_evidence") 
analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,'impaired_vs_sober',
                    bac_threshold=0.1,state_year_prop_threshold=1,mirep=False,summarize_sample=False)
mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
res_fmt.append([drink_def,round(mod_res.final_params[0][0],2),'('+str(round(mod_res.final_params[0][1],2))+')',
             round(mod_res.final_params[1][0],2),'('+str(round(mod_res.final_params[1][1],2))+')',(mod_res.df_resid+2)])
print("Estimating multiple imputation model:") 
mod_res = lpdtFit.fit_model_mi(df_accident,df_vehicle,df_person,1983,1993,20,4,['year','state','weekend','hour'],'impaired_vs_sober',
                    bac_threshold=0.1,state_year_prop_threshold=1,bsreps=bsreps,mireps=mireps)
res_fmt.append(['multiple_imputation',round(mod_res.mi_params[0][0],2),'('+str(round(mod_res.mi_params[0][1],2))+')',
                 round(mod_res.mi_params[1][0],2),'('+str(round(mod_res.mi_params[1][1],2))+')',(mod_res.mi_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['drink_def','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel('results\\table5_panel2.xlsx') # Note: should format as text after opening Excel file

# APPENDIX TABLE 1
equal_mixings = [['all'],['hour'],['year','hour'],['year','weekend','hour'],['year','state','hour'],['year','state','weekend','hour']]
#equal_mixings = [['all'],['hour']]
for drink_def in drink_defs: 
    res_fmt = list() # list of results, formatted
    for eq_mix in equal_mixings: 
        print("Estimating model for drinking definition: " + drink_def) 
        analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,20,4,drink_def,
                            bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=False)
        mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,eq_mix,bsreps)
        res_fmt.append([eq_mix,round(mod_res.final_params[0][0],2),'('+str(round(mod_res.final_params[0][1],2))+')',
                     round(mod_res.final_params[1][0],2),'('+str(round(mod_res.final_params[1][1],2))+')',(mod_res.df_resid+2)])
    res_fmt_df = pandas.DataFrame(res_fmt,columns=['eq_mix','theta','theta_se','lambda','lambda_se','total_dof'])
    res_fmt_df.T.to_excel('results\\tableA1_panel_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file    
res_fmt = list() # list of results, formatted
for eq_mix in equal_mixings: 
    print("Estimating multiple imputation model:") 
    mod_res = lpdtFit.fit_model_mi(df_accident,df_vehicle,df_person,1983,1993,20,4,eq_mix,'bac_test_primary',
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,bsreps=bsreps,mireps=mireps)
    res_fmt.append([eq_mix,round(mod_res.mi_params[0][0],2),'('+str(round(mod_res.mi_params[0][1],2))+')',
                     round(mod_res.mi_params[1][0],2),'('+str(round(mod_res.mi_params[1][1],2))+')',(mod_res.mi_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['eq_mix','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel('results\\tableA1_panel_multiple_imputation.xlsx') # Note: should format as text after opening Excel file

# APPENDIX FIGURE 1
for drink_def in drink_defs: 
    res_fmt = list() # list of results, formatted
    for yr in range(1983,1994): 
        print("Estimating model for drinking definition " + drink_def + " in year " + yr) 
        analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,yr,yr,20,4,drink_def,
                            bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=False)
        mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
        res_fmt.append([yr,round(mod_res.final_params[0][0],2),'('+str(round(mod_res.final_params[0][1],2))+')',
                     round(mod_res.final_params[1][0],2),'('+str(round(mod_res.final_params[1][1],2))+')',(mod_res.df_resid+2)])
    res_fmt_df = pandas.DataFrame(res_fmt,columns=['year','theta','theta_se','lambda','lambda_se','total_dof'])
    res_fmt_df.T.to_excel('results\\tableA1_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file    
    
# APPENDIX FIGURE 2
for drink_def in drink_defs: 
    res_fmt = list() # list of results, formatted
    for earliest_hour_raw in range(20,29): 
        if earliest_hour_raw > 23:
            earliest_hour = earliest_hour_raw - 24
        print("Estimating model for drinking definition " + drink_def + " in hour " + earliest_hour) 
        analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,earliest_hour,earliest_hour,drink_def,
                            bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=False)
        mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
        res_fmt.append([earliest_hour,round(mod_res.final_params[0][0],2),'('+str(round(mod_res.final_params[0][1],2))+')',
                     round(mod_res.final_params[1][0],2),'('+str(round(mod_res.final_params[1][1],2))+')',(mod_res.df_resid+2)])
    res_fmt_df = pandas.DataFrame(res_fmt,columns=['hour','theta','theta_se','lambda','lambda_se','total_dof'])
    res_fmt_df.T.to_excel('results\\tableA2_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file    

# APPENDIX FIGURE 3    
drink_def = 'police_report_primary'
res_fmt = list() # list of results, formatted
for yr in range(1983,1994): 
    print("Estimating model for drinking definition " + drink_def + " in year " + yr) 
    analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,yr,yr,20,4,drink_def,
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=False)
    mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
    res_fmt.append([yr,round(mod_res.final_params[0][0],2),'('+str(round(mod_res.final_params[0][1],2))+')',
                 round(mod_res.final_params[1][0],2),'('+str(round(mod_res.final_params[1][1],2))+')',(mod_res.df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel('results\\tableA3_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file   
for yr in range(1983,1994): 
    print("Estimating multiple imputation model in year " + yr) 
    mod_res = lpdtFit.fit_model_mi(df_accident,df_vehicle,df_person,yr,yr,20,4,['year','state','weekend','hour'],drink_def,
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,bsreps=bsreps,mireps=mireps)
    res_fmt.append([yr,round(mod_res.mi_params[0][0],2),'('+str(round(mod_res.mi_params[0][1],2))+')',
                     round(mod_res.mi_params[1][0],2),'('+str(round(mod_res.mi_params[1][1],2))+')',(mod_res.mi_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel('results\\tableA3_multiple_imputation.xlsx') # Note: should format as text after opening Excel file

# APPENDIX FIGURE 4
drink_def = 'police_report_primary'
res_fmt = list() # list of results, formatted
for earliest_hour_raw in range(20,29): 
    if earliest_hour_raw > 23:
        earliest_hour = earliest_hour_raw - 24
    print("Estimating model for drinking definition " + drink_def + " in hour " + earliest_hour) 
    analytic_sample = lpdtUtil.get_analytic_sample(df_accident,df_vehicle,df_person,1983,1993,earliest_hour,earliest_hour,drink_def,
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,mirep=False,summarize_sample=False)
    mod_res = lpdtFit.fit_model(analytic_sample,df_vehicle,df_person,['year','state','weekend','hour'],bsreps)
    res_fmt.append([earliest_hour,round(mod_res.final_params[0][0],2),'('+str(round(mod_res.final_params[0][1],2))+')',
                 round(mod_res.final_params[1][0],2),'('+str(round(mod_res.final_params[1][1],2))+')',(mod_res.df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['hour','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel('results\\tableA4_' + drink_def + '.xlsx') # Note: should format as text after opening Excel file   
for earliest_hour_raw in range(20,29): 
    if earliest_hour_raw > 23:
        earliest_hour = earliest_hour_raw - 24
    print("Estimating multiple imputation model in hour " + earliest_hour) 
    mod_res = lpdtFit.fit_model_mi(df_accident,df_vehicle,df_person,1983,1993,earliest_hour,earliest_hour,['year','state','weekend','hour'],drink_def,
                        bac_threshold=0,state_year_prop_threshold=sy_p_t,bsreps=bsreps,mireps=mireps)
    res_fmt.append([earliest_hour,round(mod_res.mi_params[0][0],2),'('+str(round(mod_res.mi_params[0][1],2))+')',
                     round(mod_res.mi_params[1][0],2),'('+str(round(mod_res.mi_params[1][1],2))+')',(mod_res.mi_df_resid+2)])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['hour','theta','theta_se','lambda','lambda_se','total_dof'])
res_fmt_df.T.to_excel('results\\tableA4_multiple_imputation.xlsx') # Note: should format as text after opening Excel file
