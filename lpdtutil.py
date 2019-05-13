# -*- coding: utf-8 -*-
"""
Created on Fri May 10 11:41:35 2019

@author: ntefft
"""

import pandas

# Function that returns a dataframe of drivers, from the person file. The default is to drop crashes with multiple drivers in at least one of the driver's seats
def get_driver(df_person, keep_duplicated = False, keep_per_no = False):
    df_driver = df_person.loc[df_person['seat_pos']==11] # keep only drivers from the person file
    df_driver = df_driver.loc[~df_driver.index.droplevel(['per_no']).duplicated(keep_duplicated)] # drop the first of duplicate drivers (when there were two persons in the driver seat)
    if keep_per_no == False:
        df_driver = df_driver.droplevel(['per_no'])
    return df_driver

# function that identifies a vehicle's driver as drunk, depending on Levitt & Porter definition of interest
# returns either a series (single status) or a dataframe (10 imputed values for mi)
def veh_dr_drinking_status(df_vehicle, df_driver, drinking_definition = 'mi', bac_threshold = 0.08):
    df_veh_driver = df_vehicle.merge(df_driver,how='left',left_index=True,right_index=True,validate='1:m') # merge in drivers from person file
    
    # DRINKING DEFINITIONS
    # mi: use multiple imputation values
    # police_report_only: police officer report [0 if nondrinking, 1 if drinking, 8 if not reported, 9 if unknown] (definition 1 in L&P, 2001; what LP say they use)
    # any_evidence: drinking if any evidence, not drinking otherwise (definition 2 in paper; what LP actually use)
    # police_report_primary: officer report primary, missing values adjusted by BAC test (definition 3 in paper)
    # bac_test_primary: BAC test primary (definition 4 in paper)
    # impaired_vs_sober: Legal impairment based on tested BAC, compared against not drinking (intermediate values dropped...this is the supplemental analysis in LP)
    
    bac_threshold_scaled = bac_threshold*100 # need to scale the threshold to match how the data are stored
    
    if drinking_definition == 'mi':
        df_driver_drink_status = df_veh_driver[['mibac1','mibac2','mibac3','mibac4','mibac5','mibac6','mibac7','mibac8','mibac9','mibac10']] > bac_threshold_scaled        
        df_driver_drink_status = df_driver_drink_status.astype('int')
        df_driver_drink_status = df_driver_drink_status.rename(columns={'mibac1':'drink_status1','mibac2':'drink_status2','mibac3':'drink_status3','mibac4':'drink_status4','mibac5':'drink_status5','mibac6':'drink_status6','mibac7':'drink_status7','mibac8':'drink_status8','mibac9':'drink_status9','mibac10':'drink_status10',}) # rename columns 
    elif drinking_definition == 'police_report_only':
        df_driver_drink_status = df_veh_driver['drinking']
    elif drinking_definition == 'any_evidence':
        df_driver_drink_status = df_veh_driver['dr_drink']
    elif drinking_definition == 'police_report_primary':
        df_driver_drink_status = df_veh_driver['drinking']
        df_driver_drink_status.loc[(df_veh_driver['alcohol_test_result']==0) & (df_veh_driver['drinking'].isin([8,9]) | df_veh_driver['drinking'].isna())] = 0
        df_driver_drink_status.loc[(df_veh_driver['alcohol_test_result']>0) & (df_veh_driver['drinking'].isin([8,9]) | df_veh_driver['drinking'].isna())] = 1         
    elif drinking_definition == 'bac_test_primary':
        df_driver_drink_status = df_veh_driver['drinking']
        df_driver_drink_status.loc[df_veh_driver['alcohol_test_result']==0] = 0
        df_driver_drink_status.loc[df_veh_driver['alcohol_test_result']>bac_threshold_scaled] = 1
    elif drinking_definition == 'impaired_vs_sober':
        df_driver_drink_status = pandas.Series(index=df_veh_driver.index)
        df_driver_drink_status.loc[(df_veh_driver['alcohol_test_result']==0) | (df_veh_driver['dr_drink']==0)] = 0
        df_driver_drink_status.loc[(df_veh_driver['alcohol_test_result']>=bac_threshold_scaled) & (df_veh_driver['dr_drink']!=0)] = 1
    
    return df_driver_drink_status

# test code for veh_dr_drinking_status
#test = veh_dr_drinking_status(df_vehicle, df_person, drinking_definition = 'any_evidence')
#test.describe()
#test.value_counts()
#test.isna().sum()

# function that identifies accidents with missing data (for exclusion from L&P estimation)
def accident_missing_data(df_accident,df_vehicle,df_driver, drinking_definition = 'mi', bac_threshold = 0.08):
    # collect missing info about the driver
    df_dr_miss = pandas.DataFrame(index=df_driver.index)
    df_dr_miss['miss_age'] = df_driver['age'].isna()
    df_dr_miss['miss_sex'] = df_driver['sex'].isna()
    
    # collect missing info about the vehicle
    df_veh_miss = pandas.DataFrame(index=df_vehicle.index)
    df_veh_miss['miss_minor_blemishes'] = (df_vehicle['prev_acc'].isna() | df_vehicle['prev_spd'].isna() | df_vehicle['prev_oth'].isna()) 
    df_veh_miss['miss_major_blemishes'] = (df_vehicle['prev_sus'].isna() | df_vehicle['prev_dwi'].isna()) 
    df_veh_miss['miss_drinking_status'] = pandas.DataFrame(veh_dr_drinking_status(df_vehicle, df_driver, drinking_definition, bac_threshold)).isna().any(axis='columns')
    
    # collect missing info about the accident
    df_acc_miss = pandas.DataFrame(index=df_accident.index)
    df_acc_miss['miss_hour'] = df_accident['hour'].isna()
    df_acc_miss['miss_day_week'] = df_accident['day_week'].isna()
    df_acc_miss['miss_state'] = df_accident['state'].isna()
    
    df_return_miss = df_acc_miss.merge(df_veh_miss.merge(df_dr_miss,how='left',on=['year','st_case','veh_no']),how='left',on=['year','st_case']).groupby(['year','st_case']).any()
    df_return_miss['miss_any'] = df_return_miss.any(axis='columns')
    
    return df_return_miss

# function that calculates the proportion of state-year observations that have missing data (for exclusion from L&P estimation)
def state_year_prop_miss(miss_any):
    df_acc_miss_any = df_accident.merge(miss_any,how='inner',on=['year','st_case'])
    return df_acc_miss_any[['state','miss_any']].groupby(['year','state']).mean()
    
    
# code for testing
df_acc_miss_flag = accident_missing_data(df_accident,df_vehicle,get_driver(df_person),drinking_definition='any_evidence')
df_acc_miss_flag['miss_any'].value_counts()

test = state_year_prop_miss(df_acc_miss_flag['miss_any'])
