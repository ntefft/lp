# -*- coding: utf-8 -*-
"""
Created on Fri May 10 11:41:35 2019

@author: ntefft
"""

import numpy,pandas

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
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    elif drinking_definition == 'any_evidence':
        df_driver_drink_status = df_veh_driver['dr_drink']
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    elif drinking_definition == 'police_report_primary':
        df_driver_drink_status = df_veh_driver['drinking']
        df_driver_drink_status.loc[(df_veh_driver['alcohol_test_result']==0) & (df_veh_driver['drinking'].isin([8,9]) | df_veh_driver['drinking'].isna())] = 0
        df_driver_drink_status.loc[(df_veh_driver['alcohol_test_result']>0) & (df_veh_driver['drinking'].isin([8,9]) | df_veh_driver['drinking'].isna())] = 1         
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    elif drinking_definition == 'bac_test_primary':
        df_driver_drink_status = df_veh_driver['drinking']
        df_driver_drink_status.loc[df_veh_driver['alcohol_test_result']==0] = 0
        df_driver_drink_status.loc[df_veh_driver['alcohol_test_result']>bac_threshold_scaled] = 1
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    elif drinking_definition == 'impaired_vs_sober':
        df_driver_drink_status = pandas.Series(index=df_veh_driver.index)
        df_driver_drink_status.loc[(df_veh_driver['alcohol_test_result']==0) | (df_veh_driver['dr_drink']==0)] = 0
        df_driver_drink_status.loc[(df_veh_driver['alcohol_test_result']>=bac_threshold_scaled) & (df_veh_driver['dr_drink']!=0)] = 1
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    
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
def state_year_prop_miss(df_accident,miss_any):
    df_acc_miss_any = df_accident.merge(miss_any,how='inner',on=['year','st_case'])
    return df_acc_miss_any[['state','miss_any']].groupby(['year','state']).mean()
    
#    
## code for testing
#df_acc_miss_flag = accident_missing_data(df_accident,df_vehicle,get_driver(df_person),drinking_definition='any_evidence')
#df_acc_miss_flag['miss_any'].value_counts()
#
#test = state_year_prop_miss(df_acc_miss_flag['miss_any'])

def get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=2017, last_year=2017, earliest_hour=20, 
                               latest_hour=4, equal_mixing=['year','state','weekend','hour'], drinking_definition='any_evidence', 
                               bac_threshold = 0.08, state_year_prop_threshold = 0.13):
    
    df_accident_est = df_accident.loc[range(first_year,last_year+1)] # restrict sample to selected years
    print('Count of accidents after year sample restriction: ')
    print(len(df_accident_est.index))
    if earliest_hour > latest_hour: # wrap selected hours across midnight, and keep that sample
        df_accident_est = df_accident_est.loc[(df_accident_est['hour']>=earliest_hour) | (df_accident_est['hour']<=latest_hour)]
    else: # get simple range of hours, and keep that sample
        df_accident_est = df_accident_est.loc[(df_accident_est['hour']>=earliest_hour) & (df_accident_est['hour']<=latest_hour)]
    print('Count of accidents after hour sample restriction: ')
    print(len(df_accident_est.index))
    
    # keep only accidents with 1 or 2 involved vehicles
    acc_veh_count = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
    acc_veh_count = acc_veh_count.rename('acc_veh_count')
    print('Count of accidents by vehicles per accident:')
    print(acc_veh_count.value_counts())
    df_accident_est = df_accident_est.merge(acc_veh_count.loc[acc_veh_count<=2],how='inner',on=['year','st_case'])
    print('Count of accidents after vehicle count sample restriction: ')
    print(len(df_accident_est.index))
    
    # get dataframe of booleans indicating whether each variable has missing data (or all of them)
    df_acc_miss_flag = accident_missing_data(df_accident_est,
                                             df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)],
                                             get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(df_accident_est.index)]),
                                             drinking_definition)
    df_acc_miss_flag['miss_any'].value_counts()
    df_st_yr_prop_miss = state_year_prop_miss(df_accident,df_acc_miss_flag['miss_any'])
    
    # only keep accidents in state-years that have a proportion of missing data that is above the given threshold
    df_accident_est = df_accident_est.reset_index().set_index(['year','state']) # reset index in order to select by state and year
    df_accident_est = df_accident_est[df_accident_est.index.isin(df_st_yr_prop_miss.loc[df_st_yr_prop_miss['miss_any']<state_year_prop_threshold].index)]
    df_accident_est = df_accident_est.reset_index().set_index(['year','st_case'])
    print('Count of accidents after state-year missing proportion sample restriction: ')
    print(len(df_accident_est.index))
    
    # only keep accidents that don't have missing data
    df_accident_est = df_accident_est[df_accident_est.index.isin(df_acc_miss_flag.loc[df_acc_miss_flag['miss_any']==False].index)]
    print('Count of accidents after state-year missing data sample restriction: ')
    print(len(df_accident_est.index))
    
    # generate weekend variable
    df_accident_est['weekend'] = ((df_accident_est['day_week'] == 6) & (df_accident_est['hour'] >= 20)) | (df_accident_est['day_week'] == 7) | ((df_accident_est['day_week'] == 1) & (df_accident_est['hour'] <= 4))
    print('Count of weekdays vs weekend days: ')
    print(df_accident_est['weekend'].value_counts())
    
    # get dataframe of drinking status, then group by accident to sum drunk counts
#    df_acc_drink_count = veh_dr_drinking_status(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)], 
#                                             get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(df_accident_est.index)]), 
#                                             drinking_definition).groupby(['year','st_case']).sum()
#    
    df_acc_drink_count = veh_dr_drinking_status(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)], 
                                             get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(df_accident_est.index)]), 
                                             drinking_definition)
    
    
    # merge in drinking status and collapse accidents by number of drinkers and number of vehicles per accident
    df_accident_est = df_accident_est.merge(df_acc_drink_count.reset_index().set_index(['year','st_case']),how='left',on=['year','st_case'])
    #    ultimately, label each driver as 1 of 4 types:
    #	1 = not drinking, no kids
    #	2 = drinking, no kids
    #	3 = not drinking, kids
    #	4 = drinking, kids
    df_accident_est['driver_type'] = numpy.nan
    df_accident_est.loc[df_accident_est['drink_status']==0,'driver_type'] = 1 # driver type 1 if non-drinker
    df_accident_est.loc[df_accident_est['drink_status']==1,'driver_type'] = 2 # driver type 2 if drinker
    # reset index for unstacking by veh_no, and keep vehicle count and drink_status
    df_accident_est['veh_no2'] = df_accident_est.groupby(['year','st_case']).cumcount()+1
    df_accident_est = df_accident_est.reset_index().set_index(equal_mixing + ['st_case','veh_no2'])[['acc_veh_count','driver_type']]
    df_accident_est = df_accident_est.unstack()
    
    # should revisit this code because we might be able to use multi-level columns instead of these column names
    num_driver_types = 2
    # one-car crashes, looping over driver types
    for dt in range(1,num_driver_types+1): 
        df_accident_est['a_' + str(dt)] = 0
        df_accident_est.loc[(df_accident_est['acc_veh_count'][1] == 1) & (df_accident_est['driver_type'][1] == dt),'a_' + str(dt)] = 1

    # two-car crashes, looping over driver types
    for dt1 in range(1,num_driver_types+1): 
        for dt2 in range(1,num_driver_types+1): 
#            if dt2 >= dt1: # in order to eliminate duplicates in terms of combinations
            df_accident_est['a_' + str(dt1) + '_' + str(dt2)] = 0
            df_accident_est.loc[(df_accident_est['acc_veh_count'][1] == 2) & (df_accident_est['driver_type'][1] == dt1) & (df_accident_est['driver_type'][2] == dt2),'a_' + str(dt1) + '_' + str(dt2)] = 1
            if dt1 > dt2: # combine duplicates and drop duplicated columns
                df_accident_est['a_' + str(dt2) + '_' + str(dt1)] = df_accident_est['a_' + str(dt2) + '_' + str(dt1)] + df_accident_est['a_' + str(dt1) + '_' + str(dt2)]
                df_accident_est = df_accident_est.drop(columns=['a_' + str(dt1) + '_' + str(dt2)])
    
    # clean up dataset and collapse by equal mixing
    df_accident_est = df_accident_est.drop(columns=['acc_veh_count','driver_type'])
    df_accident_est.columns = df_accident_est.columns.droplevel(level='veh_no2')
    df_accident_est = df_accident_est.groupby(equal_mixing).sum()
    print('Rows of estimation sample after collapsing by equal mixing: ')
    print(len(df_accident_est.index))
    
    # toss observations where there are no (one-vehicle, drunk) or no (one-vehicle, sober) crashes [won't converge otherwise]
    df_accident_est['a_miss'] = 0
    for dt in range(1,num_driver_types+1): 
        df_accident_est.loc[df_accident_est['a_' + str(dt)] == 0,'a_miss'] = 1
    df_accident_est = df_accident_est[df_accident_est['a_miss'] == 0]
    df_accident_est = df_accident_est.drop(columns=['a_miss'])
    print('Rows of estimation sample after tossing out rows with zero single-car observations of either type: ')
    print(len(df_accident_est.index))
    
    print('Final estimation sample: ')
    df_accident_est.describe()
    
    return df_accident_est

# code for testing
#test = get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=2016, last_year=2017)