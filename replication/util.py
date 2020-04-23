# -*- coding: utf-8 -*-
"""
Created on Fri May 10 11:41:35 2019

@author: Nathan Tefft

This is a collection of utility functions that are to be used for the Levitt and Porter (2001) replication.
"""
# import necessary packages
import numpy,pandas,time

# returns a dataframe of drivers, from the person file. Defaults to drop crashes with multiple drivers in at least one of the driver's seats.
def get_driver(df_person, keep_duplicated = False, keep_per_no = False):
    df_driver = df_person.loc[df_person['seat_pos']==11] # keep only drivers from the person file
    # either don't keep duplicate drivers, or drop the first or last of the duplicates
    df_driver = df_driver.loc[~df_driver.index.droplevel(['per_no']).duplicated(keep_duplicated)]
    if keep_per_no == False:
        df_driver = df_driver.reset_index().set_index(['year','st_case','veh_no']).drop(['per_no'],axis=1)
    return df_driver
    
# identifies a vehicle's driver as drinking, depending on drinking definition of interest
# for multiple imputation, returns a dataframe with a drink_status for each MI replicate
def veh_dr_drinking_status(df_vehicle, df_driver, drinking_definition, bac_threshold, mireps, drop_below_threshold):
    df_veh_driver = df_vehicle.merge(df_driver,how='left',left_index=True,right_index=True) # merge in drivers from person file    
    bac_threshold_scaled = bac_threshold*100 # need to scale the threshold to match how the data are stored
    if mireps == False:
        driver_bac = df_veh_driver['alcohol_test_result']
    else:
        driver_bac = df_veh_driver.loc[:,'mibac1':'mibac' + str(mireps)] # replace the alcohol test result with the multiply imputed value
    
    # DRINKING DEFINITIONS
    # police_report_only: police officer report [0 if nondrinking, 1 if drinking, 8 if not reported, 9 if unknown] (definition 1 in L&P, 2001; what LP say they use)
    # any_evidence: drinking if any evidence, not drinking otherwise (definition 2 in paper; what LP actually use)
    # police_report_primary: officer report primary, missing values adjusted by BAC test (definition 3 in paper)
    # bac_test_primary: BAC test primary (definition 4 in paper)
    # impaired_vs_sober: Legal impairment based on tested BAC, compared against not drinking (intermediate values dropped...this is the supplemental analysis in LP)

    if drinking_definition == 'police_report_only': # definition 1 in Levitt & Porter (2001)
        if mireps == False:
            df_driver_drink_status = df_veh_driver['drinking']
        else:
            df_driver_drink_status = pandas.concat([df_veh_driver['drinking']]*mireps,axis=1)
        df_driver_drink_status = df_driver_drink_status.replace({8:numpy.nan, 9:numpy.nan})
    elif drinking_definition == 'any_evidence': # definition 2 in Levitt & Porter (2001)
        if mireps == False:
            df_driver_drink_status = df_veh_driver['dr_drink']
        else:
            df_driver_drink_status = pandas.concat([df_veh_driver['dr_drink']]*mireps,axis=1)
    elif drinking_definition == 'police_report_primary': # definition 3 in Levitt & Porter (2001)
        if mireps == False:
            df_driver_drink_status = df_veh_driver['drinking']
        else:
            df_driver_drink_status = pandas.concat([df_veh_driver['drinking']]*mireps,axis=1)
        df_driver_drink_status = df_driver_drink_status.replace({8:numpy.nan, 9:numpy.nan})
        if drop_below_threshold == False:
            df_driver_drink_status = df_driver_drink_status.mask((df_driver_drink_status.isnull()).to_numpy() & (driver_bac<=bac_threshold_scaled).to_numpy(), 0)
        else:
            df_driver_drink_status = df_driver_drink_status.mask((df_driver_drink_status.isnull()).to_numpy() & (driver_bac==0).to_numpy(), 0)
        df_driver_drink_status = df_driver_drink_status.mask((df_driver_drink_status.isnull()).to_numpy() & (driver_bac>bac_threshold_scaled).to_numpy(), 1)
    elif drinking_definition == 'bac_test_primary': # definition 4 in Levitt & Porter (2001)
        if mireps == False:
            df_driver_drink_status = df_veh_driver['drinking']
        else:
            df_driver_drink_status = pandas.concat([df_veh_driver['drinking']]*mireps,axis=1)
        if drop_below_threshold == False:
            df_driver_drink_status = df_driver_drink_status.mask((driver_bac<=bac_threshold_scaled).to_numpy(), 0)
        else:
            df_driver_drink_status = df_driver_drink_status.mask((driver_bac==0).to_numpy(), 0)
            df_driver_drink_status = df_driver_drink_status.mask((driver_bac>0).to_numpy() & (driver_bac<=bac_threshold_scaled).to_numpy(), numpy.nan)
        df_driver_drink_status = df_driver_drink_status.mask((driver_bac>bac_threshold_scaled).to_numpy(), 1)
        df_driver_drink_status = df_driver_drink_status.replace({8:numpy.nan, 9:numpy.nan})        
    elif drinking_definition == 'impaired_vs_sober': # definition 5 in Levitt & Porter (2001)
        df_driver_drink_status = pandas.Series(index=df_veh_driver.index)
        if mireps == False:
            df_driver_drink_status = pandas.Series(index=df_veh_driver.index)
            dr_drink = df_veh_driver['dr_drink']
        else:
            df_driver_drink_status = pandas.DataFrame(index=df_veh_driver.index)
            for mirep in range(0,mireps):
                df_driver_drink_status['drink_status' + str(mirep+1)] = numpy.nan
            dr_drink = pandas.concat([df_veh_driver['dr_drink']]*mireps,axis=1)
        df_driver_drink_status = df_driver_drink_status.mask((driver_bac==0).to_numpy() | (dr_drink==0).to_numpy(), 0)
        df_driver_drink_status = df_driver_drink_status.mask((driver_bac!=0).to_numpy() & (~driver_bac.isnull()).to_numpy() & (driver_bac>=bac_threshold_scaled).to_numpy(), 1)
    elif drinking_definition == 'bac_test_only': # new definition that should be used when running MI with BAC only
        if mireps == False:
            df_driver_drink_status = pandas.Series(index=df_veh_driver.index,data=numpy.nan)
        else:
            df_driver_drink_status = pandas.DataFrame(index=df_veh_driver.index)
            for mirep in range(0,mireps):
                df_driver_drink_status['drink_status' + str(mirep+1)] = numpy.nan
        if drop_below_threshold == False:
            df_driver_drink_status = df_driver_drink_status.mask((driver_bac<=bac_threshold_scaled).to_numpy(), 0)
        else:
            df_driver_drink_status = df_driver_drink_status.mask((driver_bac==0).to_numpy(), 0)
        df_driver_drink_status = df_driver_drink_status.mask((driver_bac>bac_threshold_scaled).to_numpy(), 1)
    
    if mireps == False:
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    else:
        for mirep in range(0,mireps):
            df_driver_drink_status.columns.values[mirep] = 'drink_status' + str(mirep+1)
    
    return df_driver_drink_status


# identifies accidents with missing data (that are relevant for exclusion from L&P estimation)
def accident_missing_data(df_accident,df_vehicle,df_driver,drinking_definition,bac_threshold,mireps,drop_below_threshold):
    # collect missing info about the driver
    df_dr_miss = pandas.DataFrame(index=df_driver.index)
    df_dr_miss['miss_age'] = (df_driver['age'].isnull()) | (df_driver['age'] < 13) # set child drivers as missing values
    df_dr_miss['miss_sex'] = df_driver['sex'].isnull()
    
    # collect missing info about the vehicle
    df_veh_miss = pandas.DataFrame(index=df_vehicle.index)
    df_veh_miss['miss_minor_blemishes'] = (df_vehicle['prev_acc'].isnull() | df_vehicle['prev_spd'].isnull() | df_vehicle['prev_oth'].isnull()) 
    df_veh_miss['miss_major_blemishes'] = (df_vehicle['prev_sus'].isnull() | df_vehicle['prev_dwi'].isnull()) 
    df_veh_miss['miss_any_blemishes'] = (df_veh_miss['miss_minor_blemishes'] | df_veh_miss['miss_major_blemishes']) 
    df_veh_miss['miss_drinking_status'] = pandas.DataFrame(veh_dr_drinking_status(df_vehicle, df_driver, drinking_definition, bac_threshold, mireps, drop_below_threshold)).isnull().any(axis='columns')
    
    # collect missing info about the accident
    df_acc_miss = pandas.DataFrame(index=df_accident.index)
    df_acc_miss['miss_hour'] = df_accident['hour'].isnull()
    df_acc_miss['miss_day_week'] = df_accident['day_week'].isnull()
    df_acc_miss['miss_state'] = df_accident['state'].isnull()
    
    df_return_miss = df_acc_miss.merge(df_veh_miss.merge(df_dr_miss,how='left',on=['year','st_case','veh_no']),how='left',on=['year','st_case']).groupby(['year','st_case']).any()
    # flag anything missing excluding drinking status
    df_return_miss['miss_any_excl_drink_stat'] = df_return_miss.drop(columns=['miss_drinking_status']).any(axis='columns')
    # flag anything missing
    df_return_miss['miss_any'] = df_return_miss.any(axis='columns')
    
    return df_return_miss

# from the extracted FARS variables, builds the analytic sample of accident-vehicle-drivers
# allows several parameters to be set for selecting the analytic sample to be used
def get_analytic_sample(df_accident,df_vehicle,df_person,first_year,last_year,earliest_hour, 
                        latest_hour,drinking_definition,bac_threshold,state_year_prop_threshold,
                        mireps=False,summarize_sample=True,drop_below_threshold=True):

    # start timer and summarize the initial data
    start = time.time()
    print("Building the analytic sample...")
    if summarize_sample == True:
        print('Count of all accidents: ')
        print(len(df_accident.index))
        print('Count of all vehicles: ')
        print(len(df_vehicle.index))
        print('Count of all drivers: ')
        print(len(get_driver(df_person)))
        
    # implement year range sample restriction
    analytic_sample = df_accident[df_accident.index.droplevel('st_case').isin(range(first_year,last_year+1))] # restrict sample to selected years
    if summarize_sample == True:
        print('Count of accidents after year sample restriction: ')
        print(len(analytic_sample.index))
        print('Count of vehicles after year sample restriction: ')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)].index))
        
    # drop accidents that include any vehicles that don't have a driver (all acidents must be complete with all vehicles having a driver)
    analytic_sample = analytic_sample[~analytic_sample.index.isin(df_vehicle[~df_vehicle.index.isin(get_driver(df_person).index)].index.droplevel(['veh_no']))]
    if summarize_sample == True:    
        print('Count of accidents after excluding accidents with no recorded drivers: ')
        print(len(analytic_sample.index))
        print('Count of vehicles after excluding accidents with no recorded drivers: ')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)].index))
        print('Count of accidents with missing hours: ')
        print(len(analytic_sample.loc[analytic_sample['hour'].isnull()]))
        print('Count of vehicles with missing hours: ')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.loc[analytic_sample['hour'].isnull()].index)].index))   
        acc_veh_count = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
        acc_veh_count = acc_veh_count.rename('acc_veh_count')
        print('Count of accidents by vehicles per accident, before hours restriction:')
        print(acc_veh_count.value_counts())
        print('Proportion of accidents with 3 or more drivers, before hours restriction:')
        print(len(analytic_sample[analytic_sample.index.isin(acc_veh_count.loc[acc_veh_count>=3].index)])/len(analytic_sample.index))
        print('Proportion of drivers in accidents with 3 or more drivers, before hours restriction:')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample[analytic_sample.index.isin(acc_veh_count.loc[acc_veh_count>=3].index)].index)])/len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)]))
        
    # implement hours range restriction
    if earliest_hour > latest_hour: # wrap selected hours across midnight, and keep that sample
        analytic_sample = analytic_sample.loc[(analytic_sample['hour']>=earliest_hour) | (analytic_sample['hour']<=latest_hour)]
    else: # get simple range of hours, and keep that sample
        analytic_sample = analytic_sample.loc[(analytic_sample['hour']>=earliest_hour) & (analytic_sample['hour']<=latest_hour)]
    if summarize_sample == True:    
        print('Count of accidents after hour sample restriction: ')
        print(len(analytic_sample.index))
        print('Count of vehicles after hour sample restriction: ')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)].index))      
        print('Count of accidents by vehicles per accident, after hours restriction:')
        acc_veh_count = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
        acc_veh_count = acc_veh_count.rename('acc_veh_count')
        print(acc_veh_count.value_counts())
        print('Proportion of accidents with 3 or more drivers, after hours restriction:')
        print(len(analytic_sample.merge(acc_veh_count.loc[acc_veh_count>=3],how='inner',on=['year','st_case']).index)/len(analytic_sample.index))
        print('Proportion of drivers in accidents with 3 or more drivers, before hours restriction:')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.merge(acc_veh_count.loc[acc_veh_count>=3],how='inner',on=['year','st_case']).index)])/len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)]))
        
    # implement restriction only keeping accidents that have 1 or 2 involved vehicles
    analytic_sample['acc_veh_count'] = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
    analytic_sample = analytic_sample.loc[analytic_sample['acc_veh_count']<=2]
    if summarize_sample == True:    
        print('Count of accidents after vehicle count sample restriction: ')
        print(len(analytic_sample.index))
        print('Count of drivers after vehicle count sample restriction: ')
        tmp_driver = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)])
        print(len(tmp_driver.index))
        print('Count and proportion of drivers with drinking==8 or drinking==9 after vehicle count sample restriction: ')
        print(len(tmp_driver.loc[tmp_driver['drinking'].isin([8,9])]))
        print(len(tmp_driver.loc[tmp_driver['drinking'].isin([8,9])])/len(tmp_driver))
        print('Count of accidents by vehicles per accident, after vehicle count restriction:')
        acc_veh_count = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
        acc_veh_count = acc_veh_count.rename('acc_veh_count')
        print(acc_veh_count.value_counts())
        tmp_driver1 = tmp_driver.merge(acc_veh_count.loc[acc_veh_count==1],how='inner',on=['year','st_case'])
        print('Proportion of one-vehicle crashes with driver lacking a police evaluation: ')
        print(len(tmp_driver1.loc[tmp_driver1['drinking'].isin([8,9]) | tmp_driver1['drinking'].isnull()])/len(tmp_driver1))
        print('Proportion of one-vehicle crashes with driver lacking a BAC test result: ')
        print(len(tmp_driver1.loc[tmp_driver1['alcohol_test_result'].isnull()])/len(tmp_driver1))
        print('Proportion of one-vehicle crashes with driver lacking a police evaluation and BAC test result: ')
        print(len(tmp_driver1.loc[(tmp_driver1['drinking'].isin([8,9]) | tmp_driver1['drinking'].isnull()) & tmp_driver1['alcohol_test_result'].isnull()])/len(tmp_driver1))
        tmp_driver2 = tmp_driver.merge(acc_veh_count.loc[acc_veh_count==2],how='inner',on=['year','st_case'])
        print('Proportions of two-vehicle crashes with driver(s) lacking a police evaluation: ')
        print((tmp_driver2['drinking'].isin([8,9]) | tmp_driver2['drinking'].isnull()).groupby(['year','st_case']).mean().value_counts()/len(tmp_driver2.groupby(['year','st_case']).mean()))
        print('Proportions of two-vehicle crashes with driver(s) lacking a BAC test result: ')
        print((tmp_driver2['alcohol_test_result'].isnull()).groupby(['year','st_case']).mean().value_counts()/len(tmp_driver2.groupby(['year','st_case']).mean()))       
        print('Proportions of two-vehicle crashes with driver(s) lacking a police evaluation and a BAC test result: ')
        print(((tmp_driver2['drinking'].isin([8,9]) | tmp_driver2['drinking'].isnull()) & tmp_driver2['alcohol_test_result'].isnull()).groupby(['year','st_case']).mean().value_counts()/len(tmp_driver2.groupby(['year','st_case']).mean()))
        print('Proportion of all drivers involved in all fatal crashes lacking a police evaluation: ')
        tmp_all_driver = get_driver(df_person)
        print(len(tmp_all_driver.loc[tmp_all_driver['drinking'].isin([8,9]) | tmp_all_driver['drinking'].isnull()])/len(tmp_all_driver))        
        if mireps == False: # can only obtain single driver BAC if not MI (and BAC is never missing for MI)
            print('Count and proportion of drivers missing BAC test after vehicle count sample restriction: ')
            tmp_driver['driver_bac'] = tmp_driver['alcohol_test_result']
            print(len(tmp_driver.loc[tmp_driver['driver_bac'].isnull()]))
            print(len(tmp_driver.loc[tmp_driver['driver_bac'].isnull()])/len(tmp_driver))
            print('Cross-tabulation of police evaluation and BAC test result: ')
            tmp_driver['bac_gt0_na'] = tmp_driver['driver_bac']
            tmp_driver.loc[tmp_driver['bac_gt0_na']>0,'bac_gt0_na'] = 1
            tmp_driver.loc[tmp_driver['bac_gt0_na'].isnull(),'bac_gt0_na'] = 2
            print(pandas.crosstab(tmp_driver['bac_gt0_na'],tmp_driver['drinking'],margins=True))
            print(pandas.crosstab(tmp_driver['bac_gt0_na'],tmp_driver['drinking'],margins=True).apply(lambda r: r/len(tmp_driver)))
       
    if (drinking_definition == 'impaired_vs_sober') & (mireps == False): # not applicable to MI
        # calculate how many are dropped according to the following supplemental analysis under definition 5:
        # page 1214, paragraph 2: "we exclude all crashes occurring in states that do not test at least 95 percent of those judged to have been drinking 
        # by the police in our sample in that year (regardless of whether the motorist in question was tested). This requirement excludes more than 80 percent 
        # of the fatal crashes in the sample."
        tmp_driver_veh = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)]).merge(df_vehicle,how='inner',on=['year','st_case','veh_no'])
        tmp_driver_veh['at_flag'] = numpy.nan
        tmp_driver_veh['driver_bac'] = tmp_driver_veh['alcohol_test_result']
        tmp_driver_veh['at_flag'].loc[(tmp_driver_veh['dr_drink'] == 1) & (tmp_driver_veh['driver_bac'].isnull())] = 0
        tmp_driver_veh['at_flag'].loc[(tmp_driver_veh['dr_drink'] == 1) & (~tmp_driver_veh['driver_bac'].isnull())] = 1
        df_acc_at_flag = tmp_driver_veh.merge(analytic_sample[['state']],how='inner',on=['year','st_case'])
        df_acc_at_flag = df_acc_at_flag.reset_index().set_index(['year','st_case','state'])
        df_st_yr_prop_at = df_acc_at_flag[['at_flag']].groupby(['year','state']).mean()
        df_st_yr_prop_at['at_flag_prop'] = df_st_yr_prop_at['at_flag']
        analytic_sample = analytic_sample.reset_index().set_index(['year','state']) # reset index in order to select by state and year
        if summarize_sample == True:  
            print('Proportion of crashes occurring in states that do not test at least 95 percent of those judged to have been drinking: ')
            print(len(analytic_sample[analytic_sample.index.isin(df_st_yr_prop_at.loc[df_st_yr_prop_at['at_flag_prop']<0.95].index)])/len(analytic_sample)) 
        analytic_sample = analytic_sample[analytic_sample.index.isin(df_st_yr_prop_at.loc[df_st_yr_prop_at['at_flag_prop']>=0.95].index)]
        analytic_sample = analytic_sample.reset_index().set_index(['year','st_case'])
        
    # get dataframe of booleans indicating whether each variable has missing data (or all of them are missing)
    df_acc_miss_flag = accident_missing_data(analytic_sample, df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)],
                                             get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)]),
                                             drinking_definition, bac_threshold, mireps, drop_below_threshold)
    if summarize_sample == True:    
        print('Proportion of accidents missing information about various and any characteristics:')
        print(df_acc_miss_flag.mean())
    
    # only keep accidents in state-years that have a proportion of missing data that is above the given threshold
    df_acc_miss_flag_plus = analytic_sample[['state']].merge(df_acc_miss_flag,how='inner',on=['year','st_case'])
    df_st_yr_prop_miss = df_acc_miss_flag_plus[['state','miss_any']].groupby(['year','state']).mean()
    analytic_sample = analytic_sample.reset_index().set_index(['year','state']) # reset index in order to select by state and year
    analytic_sample = analytic_sample[analytic_sample.index.isin(df_st_yr_prop_miss.loc[df_st_yr_prop_miss['miss_any']<=state_year_prop_threshold].index)]
    analytic_sample = analytic_sample.reset_index().set_index(['year','st_case'])
    if summarize_sample == True:    
        print('Count of accidents after state-year missing proportion sample restriction: ')
        print(len(analytic_sample.index))

    # only keep remaining accidents that don't have missing data
    analytic_sample = analytic_sample[analytic_sample.index.isin(df_acc_miss_flag.loc[df_acc_miss_flag['miss_any']==False].index)]
    if summarize_sample == True:    
        print('Count of accidents after missing data sample restriction: ')
        print(len(analytic_sample.index))

    # generate statistics for Table 4 of replication
    if summarize_sample == True:    
        print('Count of one- and two-car accidents: ')
        print(analytic_sample['acc_veh_count'].value_counts())
        tmp_driver = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)])
        tmp_vehicle = df_vehicle[df_vehicle.index.isin(tmp_driver.index)]
        tmp_driver_veh = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)]).merge(df_vehicle,how='inner',on=['year','st_case','veh_no'])        
        if mireps == False:
            tmp_driver_veh['drink_status'] = veh_dr_drinking_status(tmp_vehicle, tmp_driver, drinking_definition, bac_threshold, mireps, drop_below_threshold)
        else:
            # Note that "drink_status" here is the mean across multiply imputed values for MI
            tmp_driver_veh['drink_status'] = veh_dr_drinking_status(tmp_vehicle, tmp_driver, drinking_definition, bac_threshold, mireps, drop_below_threshold).mean(axis='columns')
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
        print(tmp_driver_veh[tmp_driver_veh.index.droplevel('veh_no').isin(analytic_sample.loc[analytic_sample['acc_veh_count']==1].index)]['drink_status'].groupby(['year','st_case']).mean().value_counts()/len(analytic_sample.loc[analytic_sample['acc_veh_count']==1]))
        print('Percentage of fatal two-car crashes with zero, one, or two drinking drivers: ')
        print(tmp_driver_veh[tmp_driver_veh.index.droplevel('veh_no').isin(analytic_sample.loc[analytic_sample['acc_veh_count']==2].index)]['drink_status'].groupby(['year','st_case']).mean().value_counts()/len(analytic_sample.loc[analytic_sample['acc_veh_count']==2]))
    
    # generate weekend variable
    analytic_sample['weekend'] = ((analytic_sample['day_week'] == 6) & (analytic_sample['hour'] >= 20)) | (analytic_sample['day_week'] == 7) | ((analytic_sample['day_week'] == 1) & (analytic_sample['hour'] <= 4))
    if summarize_sample == True:    
        print('Count of weekdays vs weekend days: ')
        print(analytic_sample['weekend'].value_counts())
        
    # now merge in driver-level drink_status, to be available for building the estimation sample
    df_acc_drink_count = veh_dr_drinking_status(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)], 
                                             get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)]), 
                                             drinking_definition, bac_threshold, mireps, drop_below_threshold)
    analytic_sample = analytic_sample.merge(df_acc_drink_count.reset_index().set_index(['year','st_case']),how='left',on=['year','st_case'])
    analytic_sample = analytic_sample.reset_index().set_index(['year','st_case','veh_no'])    
    
    # code driver types as types 1 & 2 in the two-type case, or 1, 2, 3, & 4 in the four-type case
    if mireps==False:
       analytic_sample['drink_status'] = analytic_sample['drink_status'].replace({0:1, 1:2}) # driver type 1 if non-drinker, driver type 2 if drinker
       analytic_sample = analytic_sample.rename(columns={'drink_status':'driver_type'})
    else:
        for mirep in range(0,mireps):
            analytic_sample['drink_status'+str(mirep+1)] = analytic_sample['drink_status'+str(mirep+1)].replace({0:1, 1:2}) # driver type 1 if non-drinker, driver type 2 if drinker
            analytic_sample = analytic_sample.rename(columns={'drink_status'+str(mirep+1):'driver_type'+str(mirep+1)})
    
    end = time.time()
    print("Time to build analytic sample: " + str(end-start))
    return analytic_sample