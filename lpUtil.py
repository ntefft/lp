# -*- coding: utf-8 -*-
"""
Created on Fri May 10 11:41:35 2019

@author: ntefft
"""

import numpy,pandas,time

# Function that returns a dataframe of drivers, from the person file. The default is to drop crashes with multiple drivers in at least one of the driver's seats
def get_driver(df_person, keep_duplicated = False, keep_per_no = False):
    df_driver = df_person.loc[df_person['seat_pos']==11] # keep only drivers from the person file
    df_driver = df_driver.loc[~df_driver.index.droplevel(['per_no']).duplicated(keep_duplicated)] # either don't keep duplicate drivers, or drop the first or last of the duplicates
    if keep_per_no == False:
        df_driver = df_driver.droplevel(['per_no'])
    return df_driver

# test code for get_driver
#
#test3 = get_driver(df_person) # keep only drivers from the person file
    
# function that identifies a vehicle's driver as drunk, depending on Levitt & Porter definition of interest
# returns either a series (single status) or a dataframe (10 imputed values for mi)
def veh_dr_drinking_status(df_vehicle, df_driver, drinking_definition, bac_threshold, mirep):
    df_veh_driver = df_vehicle.merge(df_driver,how='left',left_index=True,right_index=True,validate='1:m') # merge in drivers from person file
    
    # DRINKING DEFINITIONS
    # mi: use multiple imputation values
    # police_report_only: police officer report [0 if nondrinking, 1 if drinking, 8 if not reported, 9 if unknown] (definition 1 in L&P, 2001; what LP say they use)
    # any_evidence: drinking if any evidence, not drinking otherwise (definition 2 in paper; what LP actually use)
    # police_report_primary: officer report primary, missing values adjusted by BAC test (definition 3 in paper)
    # bac_test_primary: BAC test primary (definition 4 in paper)
    # impaired_vs_sober: Legal impairment based on tested BAC, compared against not drinking (intermediate values dropped...this is the supplemental analysis in LP)
    
    bac_threshold_scaled = bac_threshold*100 # need to scale the threshold to match how the data are stored
    if mirep == False:
        driver_bac = df_veh_driver['alcohol_test_result']
    else:
        driver_bac = df_veh_driver['mibac' + str(mirep)]
    
#    if drinking_definition == 'mi':
#        df_driver_drink_status = df_veh_driver[['mibac1','mibac2','mibac3','mibac4','mibac5','mibac6','mibac7','mibac8','mibac9','mibac10']] > bac_threshold_scaled        
#        df_driver_drink_status = df_driver_drink_status.astype('int')
#        df_driver_drink_status = df_driver_drink_status.rename(columns={'mibac1':'drink_status1','mibac2':'drink_status2','mibac3':'drink_status3','mibac4':'drink_status4','mibac5':'drink_status5','mibac6':'drink_status6','mibac7':'drink_status7','mibac8':'drink_status8','mibac9':'drink_status9','mibac10':'drink_status10',}) # rename columns 
    if drinking_definition == 'police_report_only':
        df_driver_drink_status = df_veh_driver['drinking']
        df_driver_drink_status.loc[df_driver_drink_status.isin([8,9])] = numpy.nan
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    elif drinking_definition == 'any_evidence':
        df_driver_drink_status = df_veh_driver['dr_drink']
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    elif drinking_definition == 'police_report_primary':
        df_driver_drink_status = df_veh_driver['drinking']
        df_driver_drink_status.loc[df_driver_drink_status.isin([8,9])] = numpy.nan
        df_driver_drink_status.loc[(df_driver_drink_status.isna()) & (driver_bac==0)] = 0
        df_driver_drink_status.loc[(df_driver_drink_status.isna()) & (driver_bac>bac_threshold_scaled)] = 1                 
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    elif drinking_definition == 'bac_test_primary':
        df_driver_drink_status = df_veh_driver['drinking']
        df_driver_drink_status.loc[driver_bac==0] = 0
        df_driver_drink_status.loc[driver_bac>bac_threshold_scaled] = 1
        df_driver_drink_status.loc[df_driver_drink_status.isin([8,9])] = numpy.nan
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    elif drinking_definition == 'impaired_vs_sober':
        df_driver_drink_status = pandas.Series(index=df_veh_driver.index)
        df_driver_drink_status.loc[(driver_bac==0) | (df_veh_driver['dr_drink']==0)] = 0
        df_driver_drink_status.loc[(driver_bac>=bac_threshold_scaled) & (~driver_bac.isna()) & (df_veh_driver['dr_drink']!=0)] = 1
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    
    return df_driver_drink_status

# test code for veh_dr_drinking_status
#test = veh_dr_drinking_status(df_vehicle, df_person.loc[df_person['seat_pos']==11], drinking_definition = 'bac_test_primary', 
#                              bac_threshold = 0.1,mirep=2)
#print(test.value_counts())
#print(test.isna().sum())

# function that identifies accidents with missing data (for exclusion from L&P estimation)
def accident_missing_data(df_accident,df_vehicle,df_driver, drinking_definition, bac_threshold, mirep):
    # collect missing info about the driver
    df_dr_miss = pandas.DataFrame(index=df_driver.index)
    df_dr_miss['miss_age'] = (df_driver['age'].isna()) | (df_driver['age'] < 13) # exclude child drivers
    df_dr_miss['miss_sex'] = df_driver['sex'].isna()
    
    # collect missing info about the vehicle
    df_veh_miss = pandas.DataFrame(index=df_vehicle.index)
    df_veh_miss['miss_minor_blemishes'] = (df_vehicle['prev_acc'].isna() | df_vehicle['prev_spd'].isna() | df_vehicle['prev_oth'].isna()) 
    df_veh_miss['miss_major_blemishes'] = (df_vehicle['prev_sus'].isna() | df_vehicle['prev_dwi'].isna()) 
    df_veh_miss['miss_any_blemishes'] = (df_veh_miss['miss_minor_blemishes'] | df_veh_miss['miss_major_blemishes']) 
    df_veh_miss['miss_drinking_status'] = pandas.DataFrame(veh_dr_drinking_status(df_vehicle, df_driver, drinking_definition, bac_threshold, mirep)).isna().any(axis='columns')
    
    # collect missing info about the accident
    df_acc_miss = pandas.DataFrame(index=df_accident.index)
    df_acc_miss['miss_hour'] = df_accident['hour'].isna()
    df_acc_miss['miss_day_week'] = df_accident['day_week'].isna()
    df_acc_miss['miss_state'] = df_accident['state'].isna()
    
    df_return_miss = df_acc_miss.merge(df_veh_miss.merge(df_dr_miss,how='left',on=['year','st_case','veh_no']),how='left',on=['year','st_case']).groupby(['year','st_case']).any()
    df_return_miss['miss_any_excl_drink_stat'] = df_return_miss.drop(columns=['miss_drinking_status']).any(axis='columns')
    df_return_miss['miss_any'] = df_return_miss.any(axis='columns')
    
    return df_return_miss
## code for testing
#df_driver = get_driver(df_person)
#test = (df_driver['age'].isna()) | (df_driver['age'] < 13)
#test.value_counts()
#df_acc_miss_flag = accident_missing_data(df_accident,df_vehicle,get_driver(df_person),'any_evidence',0,0)
#df_acc_miss_flag['miss_age'].value_counts()
#

def get_analytic_sample(df_accident, df_vehicle, df_person, first_year=2017, last_year=2017, earliest_hour=20, 
                        latest_hour=4, drinking_definition='any_evidence', bac_threshold = 0.08, 
                        state_year_prop_threshold = 0.13, mirep=False,summarize_sample=True):
#    first_year=1983
#    last_year=1993
#    earliest_hour=20
#    latest_hour=4
#    equal_mixing=['year','state','weekend','hour']
##    drinking_definition='police_report_only'
#    drinking_definition='any_evidence'
#    bac_threshold = 0
##    state_year_prop_threshold = 0.13
#    state_year_prop_threshold = 0.2
#    mirep=False
#    summarize_sample=True
#   
    start = time.time()
    print("Building the analytic sample...")
    if summarize_sample == True:
        print('Count of all accidents: ')
        print(len(df_accident.index))
        print('Count of all vehicles: ')
        print(len(df_vehicle.index))
        print('Count of all drivers: ')
        print(len(get_driver(df_person)))
        
    # Implement year sample restriction
    df_accident_est = df_accident.loc[range(first_year,last_year+1)] # restrict sample to selected years
    if summarize_sample == True:
        print('Count of accidents after year sample restriction: ') # note slightly higher count because in Stata version we initially drop accidents in which no drivers were reported
        print(len(df_accident_est.index))
        print('Count of vehicles after year sample restriction: ') # note slightly higher count because in Stata version we initially drop accidents in which no drivers were reported
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)].index))
        
#    # Drop accidents that do not have any identified drivers
#    df_accident_est = df_accident_est[df_accident_est.index.isin(get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(df_accident_est.index)]).index.droplevel('veh_no'))] # restrict sample to accidents with at least one driver (initial replication exercise assumption)
    # Drop accidents that include any vehicles that don't have a driver (all vehicles must have a driver)
    df_accident_est = df_accident_est[~df_accident_est.index.isin(df_vehicle[~df_vehicle.index.isin(get_driver(df_person).index)].index.droplevel(['veh_no']))]
    if summarize_sample == True:    
        print('Count of accidents after excluding accidents with no recorded drivers: ')
        print(len(df_accident_est.index))
        print('Count of vehicles after excluding accidents with no recorded drivers: ') # note slightly higher count because in Stata version we initially drop accidents in which no drivers were reported
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)].index))
        print('Count of accidents with missing hours: ')
        print(len(df_accident_est.loc[df_accident_est['hour'].isna()]))
        print('Count of vehicles with missing hours: ')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.loc[df_accident_est['hour'].isna()].index)].index))   
        acc_veh_count = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
        acc_veh_count = acc_veh_count.rename('acc_veh_count')
        print('Count of accidents by vehicles per accident, before hours restriction:')
        print(acc_veh_count.value_counts())
        print('Proportion of accidents with 3 or more drivers, before hours restriction:')
        print(len(df_accident_est.merge(acc_veh_count.loc[acc_veh_count>=3],how='inner',on=['year','st_case']).index)/len(df_accident_est.index))
        print('Proportion of drivers in accidents with 3 or more drivers, before hours restriction:')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.merge(acc_veh_count.loc[acc_veh_count>=3],how='inner',on=['year','st_case']).index)])/len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)]))
        
    # Implement hours restriction
    if earliest_hour > latest_hour: # wrap selected hours across midnight, and keep that sample
        df_accident_est = df_accident_est.loc[(df_accident_est['hour']>=earliest_hour) | (df_accident_est['hour']<=latest_hour)]
    else: # get simple range of hours, and keep that sample
        df_accident_est = df_accident_est.loc[(df_accident_est['hour']>=earliest_hour) & (df_accident_est['hour']<=latest_hour)]
    if summarize_sample == True:    
        print('Count of accidents after hour sample restriction: ')
        print(len(df_accident_est.index))
        print('Count of vehicles after hour sample restriction: ')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)].index))      
        print('Count of accidents by vehicles per accident, after hours restriction:')
        acc_veh_count = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
        acc_veh_count = acc_veh_count.rename('acc_veh_count')
        print(acc_veh_count.value_counts())
        print('Proportion of accidents with 3 or more drivers, after hours restriction:')
        print(len(df_accident_est.merge(acc_veh_count.loc[acc_veh_count>=3],how='inner',on=['year','st_case']).index)/len(df_accident_est.index))
        print('Proportion of drivers in accidents with 3 or more drivers, before hours restriction:')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.merge(acc_veh_count.loc[acc_veh_count>=3],how='inner',on=['year','st_case']).index)])/len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)]))
        
    # Implement restriction keeping only accidents with 1 or 2 involved vehicles
    acc_veh_count = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
    acc_veh_count = acc_veh_count.rename('acc_veh_count')
    df_accident_est = df_accident_est.merge(acc_veh_count.loc[acc_veh_count<=2],how='inner',on=['year','st_case'])
    if summarize_sample == True:    
        print('Count of accidents after vehicle count sample restriction: ')
        print(len(df_accident_est.index))
        print('Count of drivers after vehicle count sample restriction: ')
        tmp_driver = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(df_accident_est.index)])
        print(len(tmp_driver.index))
        print('Count and proportion of drivers with drinking==8 or drinking==9 after vehicle count sample restriction: ')
        print(len(tmp_driver.loc[tmp_driver['drinking'].isin([8,9])]))
        print(len(tmp_driver.loc[tmp_driver['drinking'].isin([8,9])])/len(tmp_driver))
        print('Proportion of all drivers involved in all fatal crashes lacking a police evaluation: ')
        tmp_all_driver = get_driver(df_person)
        print(len(tmp_all_driver.loc[tmp_all_driver['drinking'].isin([8,9]) | tmp_all_driver['drinking'].isna()])/len(tmp_all_driver))
        print('Count and proportion of drivers missing BAC test after vehicle count sample restriction: ')
        if mirep == False:
            tmp_driver['driver_bac'] = tmp_driver['alcohol_test_result']
        else:
            tmp_driver['driver_bac'] = tmp_driver['mibac' + str(mirep)]
        print(len(tmp_driver.loc[tmp_driver['driver_bac'].isna()]))
        print(len(tmp_driver.loc[tmp_driver['driver_bac'].isna()])/len(tmp_driver))
        print('Cross-tabulation of police evaluation and BAC test result: ')
        tmp_driver['bac_gt0_na'] = tmp_driver['driver_bac']
        tmp_driver.loc[tmp_driver['bac_gt0_na']>0,'bac_gt0_na'] = 1
        tmp_driver.loc[tmp_driver['bac_gt0_na'].isna(),'bac_gt0_na'] = 2
        print(pandas.crosstab(tmp_driver['bac_gt0_na'],tmp_driver['drinking'],margins=True))
        print(pandas.crosstab(tmp_driver['bac_gt0_na'],tmp_driver['drinking'],margins=True).apply(lambda r: r/len(tmp_driver)))
       
    # calculate how many would be dropped if the following were followed:
#        page 1214, paragraph 2: "we exclude all crashes occurring in states that do not test at least 95 percent of those judged to have been drinking 
#		by the police in our sample in that year (regardless of whether the motorist in question was tested). This requirement excludes more than 80 percent 
#		of the fatal crashes in the sample."
    if drinking_definition == 'impaired_vs_sober':
        tmp_driver_veh = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(df_accident_est.index)]).merge(df_vehicle,how='inner',on=['year','st_case','veh_no'])
        tmp_driver_veh['at_flag'] = numpy.nan
        if mirep == False:
            tmp_driver_veh['driver_bac'] = tmp_driver_veh['alcohol_test_result']
        else:
            tmp_driver_veh['driver_bac'] = tmp_driver_veh['mibac' + str(mirep)]
        tmp_driver_veh['at_flag'].loc[(tmp_driver_veh['dr_drink'] == 1) & (tmp_driver_veh['driver_bac'].isna())] = 0
        tmp_driver_veh['at_flag'].loc[(tmp_driver_veh['dr_drink'] == 1) & (~tmp_driver_veh['driver_bac'].isna())] = 1
        df_acc_at_flag = tmp_driver_veh.merge(df_accident_est[['state']],how='inner',on=['year','st_case'])
        df_acc_at_flag = df_acc_at_flag.reset_index().set_index(['year','st_case','state'])
        df_st_yr_prop_at = df_acc_at_flag[['at_flag']].groupby(['year','state']).mean()
        df_st_yr_prop_at['at_flag_prop'] = df_st_yr_prop_at['at_flag']
        df_accident_est = df_accident_est.reset_index().set_index(['year','state']) # reset index in order to select by state and year
        if summarize_sample == True:  
            print('Proportion of crashes occurring in states that do not test at least 95 percent of those judged to have been drinking: ')
            print(len(df_accident_est[df_accident_est.index.isin(df_st_yr_prop_at.loc[df_st_yr_prop_at['at_flag_prop']<0.95].index)])/len(df_accident_est)) 
        df_accident_est = df_accident_est[df_accident_est.index.isin(df_st_yr_prop_at.loc[df_st_yr_prop_at['at_flag_prop']>=0.95].index)]
        df_accident_est = df_accident_est.reset_index().set_index(['year','st_case'])
        
    # get dataframe of booleans indicating whether each variable has missing data (or all of them)
    df_acc_miss_flag = accident_missing_data(df_accident_est,
                                             df_vehicle[df_vehicle.index.droplevel('veh_no').isin(df_accident_est.index)],
                                             get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(df_accident_est.index)]),
                                             drinking_definition, bac_threshold, mirep)
    if summarize_sample == True:    
        print('Proportion of accidents missing information about various and any characteristics:')
        print(df_acc_miss_flag.mean())
    
    df_acc_miss_flag_plus = df_accident_est[['state']].merge(df_acc_miss_flag,how='inner',on=['year','st_case'])
    df_st_yr_prop_miss = df_acc_miss_flag_plus[['state','miss_any']].groupby(['year','state']).mean()
        
    # only keep accidents in state-years that have a proportion of missing data that is above the given threshold
    df_accident_est = df_accident_est.reset_index().set_index(['year','state']) # reset index in order to select by state and year
    df_accident_est = df_accident_est[df_accident_est.index.isin(df_st_yr_prop_miss.loc[df_st_yr_prop_miss['miss_any']<=state_year_prop_threshold].index)]
    df_accident_est = df_accident_est.reset_index().set_index(['year','st_case'])
    if summarize_sample == True:    
        print('Count of accidents after state-year missing proportion sample restriction: ')
        print(len(df_accident_est.index))

    # only keep accidents that don't have missing data
    df_accident_est = df_accident_est[df_accident_est.index.isin(df_acc_miss_flag.loc[df_acc_miss_flag['miss_any']==False].index)]
    if summarize_sample == True:    
        print('Count of accidents after state-year missing data sample restriction: ')
        print(len(df_accident_est.index))

    # TABLE 4 OF L&P REPLICATION
    if summarize_sample == True:    
        print('Count of one- and two-car accidents: ')
        print(df_accident_est['acc_veh_count'].value_counts())
        tmp_driver = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(df_accident_est.index)])
        tmp_vehicle = df_vehicle[df_vehicle.index.isin(tmp_driver.index)]
        tmp_driver_veh = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(df_accident_est.index)]).merge(df_vehicle,how='inner',on=['year','st_case','veh_no'])
        tmp_driver_veh['drink_status'] = veh_dr_drinking_status(tmp_vehicle, tmp_driver, drinking_definition, bac_threshold, mirep)
        tmp_driver_veh['male'] = tmp_driver_veh['sex']==1
        tmp_driver_veh['age_lt25'] = tmp_driver_veh['age'] < 25        
        tmp_driver_veh['minor_blemishes'] = tmp_driver_veh['prev_acc'] + tmp_driver_veh['prev_spd'] + tmp_driver_veh['prev_oth']
        tmp_driver_veh['major_blemishes'] = tmp_driver_veh['prev_sus'] + tmp_driver_veh['prev_dwi']
        tmp_driver_veh['bad_record'] = (tmp_driver_veh['minor_blemishes']>=2) | (tmp_driver_veh['major_blemishes']>=1)
        tmp_driver_veh['male_and_drinking'] = (tmp_driver_veh['male']==1) & (tmp_driver_veh['drink_status']==1)
        tmp_driver_veh['age_lt25_and_drinking'] = (tmp_driver_veh['age_lt25']==1) & (tmp_driver_veh['drink_status']==1)
        tmp_driver_veh['bad_record_and_drinking'] = (tmp_driver_veh['bad_record']==1) & (tmp_driver_veh['drink_status']==1)
        print('Proportions of all drivers in fatal crashes: ')
        print(tmp_driver_veh[['drink_status','male','age_lt25','bad_record','male_and_drinking',
                              'age_lt25_and_drinking','bad_record_and_drinking']].mean())
        print('Percentage of fatal one-car crashes with zero or one drinking driver: ')
        print(tmp_driver_veh[tmp_driver_veh.index.droplevel('veh_no').isin(df_accident_est.loc[df_accident_est['acc_veh_count']==1].index)]['drink_status'].groupby(['year','st_case']).mean().value_counts()/len(df_accident_est.loc[df_accident_est['acc_veh_count']==1]))
        print('Percentage of fatal two-car crashes with zero, one, or two drinking drivers: ')
        print(tmp_driver_veh[tmp_driver_veh.index.droplevel('veh_no').isin(df_accident_est.loc[df_accident_est['acc_veh_count']==2].index)]['drink_status'].groupby(['year','st_case']).mean().value_counts()/len(df_accident_est.loc[df_accident_est['acc_veh_count']==2]))
    
    # generate weekend variable
    df_accident_est['weekend'] = ((df_accident_est['day_week'] == 6) & (df_accident_est['hour'] >= 20)) | (df_accident_est['day_week'] == 7) | ((df_accident_est['day_week'] == 1) & (df_accident_est['hour'] <= 4))
    if summarize_sample == True:    
        print('Count of weekdays vs weekend days: ')
        print(df_accident_est['weekend'].value_counts())
        
    # Add attributes needed for building the estimation sample 
    df_accident_est.drinking_definition = drinking_definition
    df_accident_est.bac_threshold = bac_threshold
    df_accident_est.mirep = mirep
    
    end = time.time()
    print("Time to build analytic sample: " + str(end-start))
    return df_accident_est

# code for testing
#test = get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=1983, last_year=1993)

def get_estimation_sample(analytic_sample, df_vehicle, df_person, 
                          equal_mixing=['year','state','weekend','hour'], 
                          drinking_definition='any_evidence', bac_threshold = 0.08, mirep=False):

    start = time.time()
    print("Building the estimation sample...")
    
    estimation_sample = analytic_sample
    
    # get dataframe of drinking status, then group by accident to sum drunk counts 
    df_acc_drink_count = veh_dr_drinking_status(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)], 
                                             get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)]), 
                                             drinking_definition, bac_threshold, mirep)
    
    # merge in drinking status and collapse accidents by number of drinkers and number of vehicles per accident
    estimation_sample = estimation_sample.merge(df_acc_drink_count.reset_index().set_index(['year','st_case']),how='left',on=['year','st_case'])
    #    ultimately, label each driver as 1 of 4 types:
    #	1 = not drinking, no kids
    #	2 = drinking, no kids
    #	3 = not drinking, kids
    #	4 = drinking, kids
    estimation_sample['driver_type'] = numpy.nan
    estimation_sample.loc[estimation_sample['drink_status']==0,'driver_type'] = 1 # driver type 1 if non-drinker
    estimation_sample.loc[estimation_sample['drink_status']==1,'driver_type'] = 2 # driver type 2 if drinker
    # reset index for unstacking by veh_no, and keep vehicle count and drink_status
    estimation_sample['veh_no2'] = estimation_sample.groupby(['year','st_case']).cumcount()+1
    idx_add_veh_no2 = ['year','st_case','veh_no2']
    if 'all' not in equal_mixing:
        idx_add_veh_no2 = equal_mixing + idx_add_veh_no2
    estimation_sample = estimation_sample.reset_index().set_index(idx_add_veh_no2)[['acc_veh_count','driver_type']]
    estimation_sample = estimation_sample.unstack()
    
    # should revisit this code because we might be able to use multi-level columns instead of these column names
    num_driver_types = 2
    # one-car crashes, looping over driver types
#    estimation_sample['a_1veh_total'] = 0 # keep a running total, for the maximum likelihood function
    for dt in range(1,num_driver_types+1): 
        estimation_sample['a_' + str(dt)] = 0
        estimation_sample.loc[(estimation_sample['acc_veh_count'][1] == 1) & (estimation_sample['driver_type'][1] == dt),'a_' + str(dt)] = 1
#        estimation_sample['a_1veh_total'] = estimation_sample['a_1veh_total'] + estimation_sample['a_' + str(dt)]

    # two-car crashes, looping over driver types
#    estimation_sample['a_2veh_total'] = 0 # keep a running total, for the maximum likelihood function
    for dt1 in range(1,num_driver_types+1): 
        for dt2 in range(1,num_driver_types+1): 
#            if dt2 >= dt1: # in order to eliminate duplicates in terms of combinations
            estimation_sample['a_' + str(dt1) + '_' + str(dt2)] = 0
            estimation_sample.loc[(estimation_sample['acc_veh_count'][1] == 2) & (estimation_sample['driver_type'][1] == dt1) & (estimation_sample['driver_type'][2] == dt2),'a_' + str(dt1) + '_' + str(dt2)] = 1
#            estimation_sample['a_2veh_total'] = estimation_sample['a_2veh_total'] + estimation_sample['a_' + str(dt1) + '_' + str(dt2)]
            if dt1 > dt2: # combine duplicates and drop duplicated columns
                estimation_sample['a_' + str(dt2) + '_' + str(dt1)] = estimation_sample['a_' + str(dt2) + '_' + str(dt1)] + estimation_sample['a_' + str(dt1) + '_' + str(dt2)]
                estimation_sample = estimation_sample.drop(columns=['a_' + str(dt1) + '_' + str(dt2)])
            
    
    # clean up dataset and collapse by equal mixing
    estimation_sample = estimation_sample.drop(columns=['acc_veh_count','driver_type'])
    estimation_sample.columns = estimation_sample.columns.droplevel(level='veh_no2')
    if 'all' not in equal_mixing:
        estimation_sample = estimation_sample.groupby(equal_mixing).sum()
    else:
        estimation_sample = estimation_sample.sum().to_frame().transpose()
    print('Rows of estimation sample after collapsing by equal mixing: ')
    print(len(estimation_sample.index))
    if 'all' not in equal_mixing:
        # toss observations where there are no (one-vehicle, drunk) or no (one-vehicle, sober) crashes [won't converge otherwise]
        estimation_sample['a_miss'] = 0
        for dt in range(1,num_driver_types+1): 
            estimation_sample.loc[estimation_sample['a_' + str(dt)] == 0,'a_miss'] = 1
        estimation_sample = estimation_sample[estimation_sample['a_miss'] == 0]
        estimation_sample = estimation_sample.drop(columns=['a_miss'])
        print('Rows of estimation sample after tossing out rows with zero single-car observations of either type: ')
        print(len(estimation_sample.index))
    
    print('Final estimation sample: ')
    print(estimation_sample.describe())

    end = time.time()
    print("Time to build estimation sample: " + str(end-start))
    return estimation_sample

    
def lnfactorial(n):
    n_calc = int(n)
    lnf = 0
    for i in range(1,n_calc+1):
        lnf += numpy.log(i)
    return lnf

# calculate boostrap standard error from bootstrap estimates
def bs_se(theta_bs, axis=None):
    return numpy.power(numpy.divide(numpy.power((numpy.subtract(theta_bs,numpy.divide(theta_bs.sum(axis),numpy.size(theta_bs,axis)))),2).sum(axis),(numpy.size(theta_bs,axis)-1)),0.5)