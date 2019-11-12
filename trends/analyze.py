# -*- coding: utf-8 -*-
"""
Created on Fri Nov 8 2019

@author: Nathan Tefft

This script generates summary statistics and estimation analysis results for a nationwide trends analysis
of Levitt and Porter (2001).
"""
import os, sys, pandas, random, pickle
# change working directory to GitHub path
os.chdir(sys.path[0] + '\\Documents\\GitHub\\lp')

# import LP utility and model fit functions
import estimate
from trends import util

# read in previously extracted and stored dataframes
df_accident = pandas.read_csv('trends\\data\\df_accident.csv')
df_accident.set_index(['year','st_case'],inplace=True) # set the index
df_vehicle = pandas.read_csv('trends\\data\\df_vehicle.csv')
df_vehicle.set_index(['year','st_case','veh_no'],inplace=True) # set the index
df_person = pandas.read_csv('trends\\data\\df_person.csv')
df_person.set_index(['year','st_case','veh_no','per_no'],inplace=True) # set the index

# set estimation parameters
firstyr = 1983
lastyr = 2017
bsreps = 2 # bootstrap replicates for testing
#bsreps = 100 # bootstrap replicates for analysis
mireps = 2 # multiple imputation replicates, for testing
#mireps = 10 # multiple imputation replicates for analysis (FARS includes a total of 10)
window = 5 # length of estimation window
#results_folder = 'trends\\results' # for saving estimation results
results_folder = 'trends\\temp' # for testing
if not os.path.exists(results_folder):
        os.makedirs(results_folder) # generate results directory, if it doesn't exist

# TABLE 1: Summary statistics for fatal crashes by 5-year interval
sum_stats = list()
for yr in range(firstyr,(lastyr+1),window): 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,yr,(yr+window-1),20,4,'impaired_vs_sober',
                        bac_threshold=0,state_year_prop_threshold=1,mireps=mireps,summarize_sample=True)
    sum_stats.append(analytic_sample.sum_stats)
sum_stats_df = pandas.DataFrame(sum_stats,columns=['Window start year','Window end year','Number of fatal one-car crashes',
                'Number of fatal two-car crashes','Reported to be drinking by police','Reported to not be drinking by police',
                'Drinking status unreported by police','One drinking driver','One sober driver','One drinking, one sober driver',
                'Two sober drivers','Two drinking drivers'])
pickle.dump(sum_stats_df, open(results_folder + '\\table1.pkl', 'wb')) # pickle object for later use
sum_stats_df.T.to_excel(results_folder + '\\table1.xlsx') # Note: should format as text after opening Excel file

# TABLE 2: Relative Risk and Prevalence of Alcohol-involved Driving by 5 year interval (BAC > 0)
res_pkl = list() # pickled results for later use
res_fmt = list() # formatted results for table
for yr in range(firstyr,(lastyr+1),window): 
    print("Estimating model for " + str(yr)) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,yr,(yr+window-1),20,4,'impaired_vs_sober',
                        bac_threshold=0,state_year_prop_threshold=1,mireps=mireps,summarize_sample=False)
    mod_res = estimate.fit_model_mi(analytic_sample,['year','state','weekend','hour'],2,bsreps,mireps)
    res_pkl.append([yr,mod_res])
    res_fmt.append([yr,round(mod_res.mi_params[0][0],2),round(mod_res.mi_params[0][1],2),round(mod_res.mi_params[0][2]/(1+mod_res.mi_params[0][2]),3)])
    # Note that N is converted into proportion of drinking drivers
    res_fmt.append([(yr+window-1),'('+str(round(mod_res.mi_params[1][0],2))+')','('+str(round(mod_res.mi_params[1][1],2))+')','('+str(round(mod_res.mi_params[1][2]/(1+mod_res.mi_params[1][2]),3))+')'])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year range','theta','lambda','proportion drinking'])
pickle.dump(res_pkl, open(results_folder + '\\table2.pkl', 'wb')) # pickle object for later use
res_fmt_df.to_excel(results_folder + '\\table2.xlsx') # Note: should format as text after opening Excel file

# TABLE 3: Relative Risk and Prevalence of Alcohol-involved Driving by 5 year interval (BAC > 0.08)
res_pkl = list() # pickled results for later use
res_fmt = list() # formatted results for table
for yr in range(firstyr,(lastyr+1),window): 
    print("Estimating model for " + str(yr)) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,yr,(yr+window-1),20,4,'impaired_vs_sober',
                        bac_threshold=0.08,state_year_prop_threshold=1,mireps=mireps,summarize_sample=False)
    mod_res = estimate.fit_model_mi(analytic_sample,['year','state','weekend','hour'],2,bsreps,mireps)
    res_pkl.append([yr,mod_res])
    res_fmt.append([yr,round(mod_res.mi_params[0][0],2),round(mod_res.mi_params[0][1],2),round(mod_res.mi_params[0][2]/(1+mod_res.mi_params[0][2]),3)])
    # Note that N is converted into proportion of drinking drivers
    res_fmt.append([(yr+window-1),'('+str(round(mod_res.mi_params[1][0],2))+')','('+str(round(mod_res.mi_params[1][1],2))+')','('+str(round(mod_res.mi_params[1][2]/(1+mod_res.mi_params[1][2]),3))+')'])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year range','theta','lambda','proportion drinking'])
pickle.dump(res_pkl, open(results_folder + '\\table3.pkl', 'wb')) # pickle object for later use
res_fmt_df.to_excel(results_folder + '\\table3.xlsx') # Note: should format as text after opening Excel file

# TABLE 4: External cost per mile driven by year and driver BAC level
period_params = pandas.read_csv('trends\\externality_period_params.csv') # import externality calc parameters
random.seed(1) # for exactly replicating the bootstrapped sample
mod_res0 = util.calc_drinking_externality(df_accident,df_vehicle,df_person,period_params,0,mireps,bsreps)
mod_res8 = util.calc_drinking_externality(df_accident,df_vehicle,df_person,period_params,0.08,mireps,bsreps)
res_pkl = list([mod_res0,mod_res8]) # pickled results for later use
res_fmt = list() # formatted results for table
for idx in range(0,period_params['end_5yr_window'].size):    
    res_fmt.append([str(period_params['end_5yr_window'].iloc[idx]-window+1) + '-' + str(period_params['end_5yr_window'].iloc[idx]),
                    round(mod_res0[0][idx][2],4),round(mod_res8[0][idx][2],4)])
    res_fmt.append(['','('+str(round(mod_res0[1][idx][2],4))+')','('+str(round(mod_res8[1][idx][2],4))+')'])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year range','BAC > 0','BAC > 0.08'])
pickle.dump(res_pkl, open(results_folder + '\\table4.pkl', 'wb')) # pickle object for later use
res_fmt_df.to_excel(results_folder + '\\table4.xlsx') # Note: should format as text after opening Excel file