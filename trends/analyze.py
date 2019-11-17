# -*- coding: utf-8 -*-
"""
Created on Fri Nov 8 2019

@author: Nathan Tefft

This script generates summary statistics and estimation analysis results for a nationwide trends analysis
of Levitt and Porter (2001).
"""
import os, sys, pandas, random
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
window = 5 # length of estimation window
windows_end = list(range(1987,2018,window)) # list of windows year ends
#bsreps = 2 # bootstrap replicates for testing
bsreps = 100 # bootstrap replicates for analysis
#mireps = 2 # multiple imputation replicates, for testing
mireps = 10 # multiple imputation replicates for analysis (FARS includes a total of 10)
#results_folder = 'trends\\temp' # for testing
results_folder = 'trends\\results' # for saving estimation results
if not os.path.exists(results_folder):
        os.makedirs(results_folder) # generate results directory, if it doesn't exist

# TABLE 1: Summary statistics for fatal crashes by 5-year interval
sum_stats = list()
for eyr in windows_end:
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,(eyr-window+1),eyr,20,4,'impaired_vs_sober',
                        bac_threshold=0,state_year_prop_threshold=1,mireps=mireps,summarize_sample=True)
    sum_stats.append(analytic_sample.sum_stats)
sum_stats_df = pandas.DataFrame(sum_stats,columns=['Window start year','Window end year','Number of fatal one-car crashes',
                'Number of fatal two-car crashes','Reported to be drinking by police','Reported to not be drinking by police',
                'Drinking status unreported by police','One drinking driver','One sober driver','One drinking, one sober driver',
                'Two sober drivers','Two drinking drivers'])
sum_stats_df.T.to_excel(results_folder + '\\table1.xlsx') # Note: should format as text after opening Excel file

# TABLE 2: Relative Risk and Prevalence of Alcohol-involved Driving by 5 year interval (BAC > 0)
random.seed(1) # for exactly replicating the bootstrapped sample
res_fmt = list() # formatted results for table
for eyr in windows_end:
    print("Estimating model for " + str(eyr)) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,(eyr-window+1),eyr,20,4,'impaired_vs_sober',
                        bac_threshold=0,state_year_prop_threshold=1,mireps=mireps,summarize_sample=False)
    mod_res,model_llf,model_df_resid = estimate.fit_model_mi(analytic_sample,['year','state','weekend','hour'],2,bsreps,mireps)
    res_fmt.append([(eyr-window+1),round(mod_res[0][0][0],2),round(mod_res[0][1][0],2),round(mod_res[0][3][0],6)])
    res_fmt.append([eyr,'('+str(round(mod_res[1][0][0],2))+')','('+str(round(mod_res[1][1][0],2))+')','('+str(format(round(mod_res[1][3][0],5),'.5f'))+')'])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year range','theta','lambda','proportion drinking'])
res_fmt_df.to_excel(results_folder + '\\table2.xlsx') # Note: should format as text after opening Excel file

# TABLE 3: Relative Risk and Prevalence of Alcohol-involved Driving by 5 year interval (BAC > 0.08)
random.seed(1) # for exactly replicating the bootstrapped sample
res_fmt = list() # formatted results for table
for eyr in windows_end:
    print("Estimating model for " + str(eyr)) 
    analytic_sample = util.get_analytic_sample(df_accident,df_vehicle,df_person,(eyr-window+1),eyr,20,4,'impaired_vs_sober',
                        bac_threshold=0.08,state_year_prop_threshold=1,mireps=mireps,summarize_sample=False)
    mod_res,model_llf,model_df_resid = estimate.fit_model_mi(analytic_sample,['year','state','weekend','hour'],2,bsreps,mireps)
    res_fmt.append([(eyr-window+1),round(mod_res[0][0][0],2),round(mod_res[0][1][0],2),round(mod_res[0][3][0],6)])
    res_fmt.append([eyr,'('+str(round(mod_res[1][0][0],2))+')','('+str(round(mod_res[1][1][0],2))+')','('+str(format(round(mod_res[1][3][0],5),'.5f'))+')'])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year range','theta','lambda','proportion drinking'])
res_fmt_df.to_excel(results_folder + '\\table3.xlsx') # Note: should format as text after opening Excel file

# TABLE 4: External cost per mile driven by year and driver BAC level
random.seed(1) # for exactly replicating the bootstrapped sample
# here, include the end years of the calculation window, vehicle miles traveled from NHTSA, DOT VSL (using most recent)
df_window = pandas.DataFrame(data={'year':windows_end,
                                   'annual_vmt':[1924330000000,2247150000000,2560370000000,2829340000000,3003200000000,2938500000000,3208500000000],
                                    'dot_vsl':9600000}).set_index(['year'])
mod_res0 = util.calc_drinking_externality(df_accident,df_vehicle,df_person,df_window,['year','state','weekend','hour'],0,mireps,bsreps)
mod_res8 = util.calc_drinking_externality(df_accident,df_vehicle,df_person,df_window,['year','state','weekend','hour'],0.08,mireps,bsreps)
res_fmt = list() # formatted results for table
for idx in range(0,df_window.index.size):    
    res_fmt.append([str(df_window.index.values[idx]-window+1) + '-' + str(df_window.index.values[idx]),
                    round(mod_res0[0][idx][2],4),round(mod_res8[0][idx][2],4)])
    res_fmt.append(['','('+str(round(mod_res0[1][idx][2],4))+')','('+str(round(mod_res8[1][idx][2],4))+')'])
res_fmt_df = pandas.DataFrame(res_fmt,columns=['year range','BAC > 0','BAC > 0.08'])
res_fmt_df.to_excel(results_folder + '\\table4.xlsx') # Note: should format as text after opening Excel file