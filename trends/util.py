# -*- coding: utf-8 -*-
"""
Created on Fri May 10 11:41:35 2019

@author: Nathan Tefft

This is a collection of utility functions that are to be used for the Levitt and Porter (2001) replication.
"""
# import necessary packages
import numpy,pandas,time
import estimate

# returns a dataframe of drivers, from the person file. Defaults to drop crashes with multiple drivers in at least one of the driver's seats.
def get_driver(df_person, keep_duplicated = False, keep_per_no = False):
    df_driver = df_person.loc[df_person['seat_pos']==11] # keep only drivers from the person file
    # either don't keep duplicate drivers, or drop the first or last of the duplicates
    df_driver = df_driver.loc[~df_driver.index.droplevel(['per_no']).duplicated(keep_duplicated)]
    if keep_per_no == False:
        df_driver = df_driver.droplevel(['per_no'])
    return df_driver
    
# identifies a vehicle's driver as drinking, depending on drinking definition of interest
# for multiple imputation, returns a dataframe with a drink_status for each MI replicate
def veh_dr_drinking_status(df_vehicle, df_driver, drinking_definition, bac_threshold, mireps):
    df_veh_driver = df_vehicle.merge(df_driver,how='left',left_index=True,right_index=True,validate='1:m') # merge in drivers from person file    
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
        df_driver_drink_status = df_driver_drink_status.mask((df_driver_drink_status.isna()).to_numpy() & (driver_bac==0).to_numpy(), 0)
        df_driver_drink_status = df_driver_drink_status.mask((df_driver_drink_status.isna()).to_numpy() & (driver_bac>bac_threshold_scaled).to_numpy(), 1)
    elif drinking_definition == 'bac_test_primary': # definition 4 in Levitt & Porter (2001)
        if mireps == False:
            df_driver_drink_status = df_veh_driver['drinking']
        else:
            df_driver_drink_status = pandas.concat([df_veh_driver['drinking']]*mireps,axis=1)
        df_driver_drink_status = df_driver_drink_status.mask((driver_bac==0).to_numpy(), 0)
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
        df_driver_drink_status = df_driver_drink_status.mask((driver_bac>=bac_threshold_scaled).to_numpy() & (~driver_bac.isna()).to_numpy() & (dr_drink!=0).to_numpy(), 1)
    
    if mireps == False:
        df_driver_drink_status = df_driver_drink_status.rename('drink_status')
    else:
        for mirep in range(0,mireps):
            df_driver_drink_status.columns.values[mirep] = 'drink_status' + str(mirep+1)
    
    return df_driver_drink_status

# identifies accidents with missing data (that are relevant for exclusion from L&P estimation)
def accident_missing_data(df_accident,df_vehicle,df_driver,drinking_definition,bac_threshold,mireps):
    # collect missing info about the driver
    df_dr_miss = pandas.DataFrame(index=df_driver.index)
    df_dr_miss['miss_age'] = (df_driver['age'].isna()) | (df_driver['age'] < 13) # set child drivers as missing values
    df_dr_miss['miss_sex'] = df_driver['sex'].isna()
    
    # collect missing info about the vehicle
    df_veh_miss = pandas.DataFrame(index=df_vehicle.index)
    df_veh_miss['miss_minor_blemishes'] = (df_vehicle['prev_acc'].isna() | df_vehicle['prev_spd'].isna() | df_vehicle['prev_oth'].isna()) 
    df_veh_miss['miss_major_blemishes'] = (df_vehicle['prev_sus'].isna() | df_vehicle['prev_dwi'].isna()) 
    df_veh_miss['miss_any_blemishes'] = (df_veh_miss['miss_minor_blemishes'] | df_veh_miss['miss_major_blemishes']) 
    df_veh_miss['miss_drinking_status'] = pandas.DataFrame(veh_dr_drinking_status(df_vehicle, df_driver, drinking_definition, bac_threshold, mireps)).isna().any(axis='columns')
    
    # collect missing info about the accident
    df_acc_miss = pandas.DataFrame(index=df_accident.index)
    df_acc_miss['miss_hour'] = df_accident['hour'].isna()
    df_acc_miss['miss_day_week'] = df_accident['day_week'].isna()
    df_acc_miss['miss_state'] = df_accident['state'].isna()
    
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
                        mireps=False,summarize_sample=True):
    
    sum_stats = list() # list of summary stats, generated for paper table(s)
    sum_stats.append(first_year)
    sum_stats.append(last_year)
    
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
    analytic_sample = df_accident.loc[range(first_year,last_year+1)] # restrict sample to selected years
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
        print(len(analytic_sample.loc[analytic_sample['hour'].isna()]))
        print('Count of vehicles with missing hours: ')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.loc[analytic_sample['hour'].isna()].index)].index))   
        acc_veh_count = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
        acc_veh_count = acc_veh_count.rename('acc_veh_count')
        print('Count of accidents by vehicles per accident, before hours restriction:')
        print(acc_veh_count.value_counts())
        print('Proportion of accidents with 3 or more drivers, before hours restriction:')
        print(len(analytic_sample.merge(acc_veh_count.loc[acc_veh_count>=3],how='inner',on=['year','st_case']).index)/len(analytic_sample.index))
        print('Proportion of drivers in accidents with 3 or more drivers, before hours restriction:')
        print(len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.merge(acc_veh_count.loc[acc_veh_count>=3],how='inner',on=['year','st_case']).index)])/len(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)]))
        
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
    acc_veh_count = df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)].groupby(['year','st_case']).size() # series that counts vehicles in each accident
    acc_veh_count = acc_veh_count.rename('acc_veh_count')
    analytic_sample = analytic_sample.merge(acc_veh_count.loc[acc_veh_count<=2],how='inner',on=['year','st_case'])
    if summarize_sample == True:    
        print('Count of accidents after vehicle count sample restriction: ')
        print(len(analytic_sample.index))
        print('Count of drivers after vehicle count sample restriction: ')
        tmp_driver = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)])
        print(len(tmp_driver.index))
        print('Count and proportion of drivers with drinking==8 or drinking==9 after vehicle count sample restriction: ')
        print(len(tmp_driver.loc[tmp_driver['drinking'].isin([8,9])]))
        print(len(tmp_driver.loc[tmp_driver['drinking'].isin([8,9])])/len(tmp_driver))
        print('Proportion of all drivers involved in all fatal crashes lacking a police evaluation: ')
        tmp_all_driver = get_driver(df_person)
        print(len(tmp_all_driver.loc[tmp_all_driver['drinking'].isin([8,9]) | tmp_all_driver['drinking'].isna()])/len(tmp_all_driver))        
        if mireps == False: # can only obtain single driver BAC if not MI (and BAC is never missing for MI)
            print('Count and proportion of drivers missing BAC test after vehicle count sample restriction: ')
            tmp_driver['driver_bac'] = tmp_driver['alcohol_test_result']
            print(len(tmp_driver.loc[tmp_driver['driver_bac'].isna()]))
            print(len(tmp_driver.loc[tmp_driver['driver_bac'].isna()])/len(tmp_driver))
            print('Cross-tabulation of police evaluation and BAC test result: ')
            tmp_driver['bac_gt0_na'] = tmp_driver['driver_bac']
            tmp_driver.loc[tmp_driver['bac_gt0_na']>0,'bac_gt0_na'] = 1
            tmp_driver.loc[tmp_driver['bac_gt0_na'].isna(),'bac_gt0_na'] = 2
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
        tmp_driver_veh['at_flag'].loc[(tmp_driver_veh['dr_drink'] == 1) & (tmp_driver_veh['driver_bac'].isna())] = 0
        tmp_driver_veh['at_flag'].loc[(tmp_driver_veh['dr_drink'] == 1) & (~tmp_driver_veh['driver_bac'].isna())] = 1
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
                                             drinking_definition, bac_threshold, mireps)
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
        for item in analytic_sample['acc_veh_count'].value_counts().tolist():
            sum_stats.append(item)
        tmp_driver = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)])
        tmp_vehicle = df_vehicle[df_vehicle.index.isin(tmp_driver.index)]
        tmp_driver_veh = get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)]).merge(df_vehicle,how='inner',on=['year','st_case','veh_no'])        
        # for summary stats table, report statistics without using MI
        tmp_driver_veh['drink_status_nomi'] = numpy.nan
        tmp_driver_veh.loc[veh_dr_drinking_status(tmp_vehicle, tmp_driver, drinking_definition, bac_threshold, mireps=False)==0,'drink_status_nomi'] = 0
        tmp_driver_veh.loc[veh_dr_drinking_status(tmp_vehicle, tmp_driver, drinking_definition, bac_threshold, mireps=False)==1,'drink_status_nomi'] = 1
        sum_stats.append((tmp_driver_veh['drink_status_nomi']==1).mean())
        sum_stats.append((tmp_driver_veh['drink_status_nomi']==0).mean())
        sum_stats.append((tmp_driver_veh['drink_status_nomi'].isna()).mean())
        if mireps == False:
            tmp_driver_veh['drink_status'] = veh_dr_drinking_status(tmp_vehicle, tmp_driver, drinking_definition, bac_threshold, mireps)
        else:
            # Note that "drink_status" here is the mean across multiply imputed values for MI
            tmp_driver_veh['drink_status'] = veh_dr_drinking_status(tmp_vehicle, tmp_driver, drinking_definition, bac_threshold, mireps).mean(axis='columns')
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
        # Note that for MI, average (vote) across MI replicates to determine whether driver is drinking
        print('Percentage of fatal one-car crashes with zero or one drinking driver: ')
        print((round(tmp_driver_veh[tmp_driver_veh.index.droplevel('veh_no').isin(analytic_sample.loc[analytic_sample['acc_veh_count']==1].index)]['drink_status'].groupby(['year','st_case']).mean()).value_counts().to_numpy()/len(analytic_sample.loc[analytic_sample['acc_veh_count']==1])))
        for item in (round(tmp_driver_veh[tmp_driver_veh.index.droplevel('veh_no').isin(analytic_sample.loc[analytic_sample['acc_veh_count']==1].index)]['drink_status'].groupby(['year','st_case']).mean()).value_counts().to_numpy()/len(analytic_sample.loc[analytic_sample['acc_veh_count']==1])).tolist():
            sum_stats.append(item)
        print('Percentage of fatal two-car crashes with zero, one, or two drinking drivers: ')
        print((round(2*tmp_driver_veh[tmp_driver_veh.index.droplevel('veh_no').isin(analytic_sample.loc[analytic_sample['acc_veh_count']==2].index)]['drink_status'].groupby(['year','st_case']).mean())/2).value_counts().to_numpy()/len(analytic_sample.loc[analytic_sample['acc_veh_count']==2]))
        for item in ((round(2*tmp_driver_veh[tmp_driver_veh.index.droplevel('veh_no').isin(analytic_sample.loc[analytic_sample['acc_veh_count']==2].index)]['drink_status'].groupby(['year','st_case']).mean())/2).value_counts().to_numpy()/len(analytic_sample.loc[analytic_sample['acc_veh_count']==2])).tolist():
            sum_stats.append(item)
    # generate weekend variable
    analytic_sample['weekend'] = ((analytic_sample['day_week'] == 6) & (analytic_sample['hour'] >= 20)) | (analytic_sample['day_week'] == 7) | ((analytic_sample['day_week'] == 1) & (analytic_sample['hour'] <= 4))
    if summarize_sample == True:    
        print('Count of weekdays vs weekend days: ')
        print(analytic_sample['weekend'].value_counts())
        
    # now merge in driver-level drink_status, to be available for building the estimation sample
    df_acc_drink_count = veh_dr_drinking_status(df_vehicle[df_vehicle.index.droplevel('veh_no').isin(analytic_sample.index)], 
                                             get_driver(df_person[df_person.index.droplevel(['veh_no','per_no']).isin(analytic_sample.index)]), 
                                             drinking_definition, bac_threshold, mireps)
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
    
    # add summary stats attribute for building tables
    analytic_sample.sum_stats = sum_stats
    analytic_sample.sum_stats_labels = ['Number of fatal one-car crashes','Number of fatal two-car crashes','Reported to be drinking by police','Reported to not be drinking by police',
                                        'Drinking status unreported by police','One drinking driver','One sober driver','One drinking, one sober driver','Two sober drivers','Two drinking drivers']
    
    return analytic_sample

def calc_drinking_externality(df_accident,df_vehicle,df_person,equal_mixing,bac_threshold,mireps,bsreps):
    # should bootstrap using each MI replicate, then combine results as MI estimates and MI SE: https://arxiv.org/pdf/1602.07933v1.pdf
    
    # test code    
    equal_mixing=['year','state','weekend','hour']
    bac_threshold=0
    mireps=10
    bsreps=10

#    period_params = period_params.rename(columns={'end_5yr_window':'year'}).set_index(['year'])
    # data for the windows over which externalities will be calculated
    # here, the end year of the calculation window, and vehicle miles traveled from NHTSA
    df_window = pandas.DataFrame(data={'year':[1987,1992,1997,2002,2007,2012,2017], 
                                       'annual_vmt':[1924330000000,2247150000000,2560370000000,2829340000000,3003200000000,2938500000000,3208500000000]})
    dot_vsl = 9600000 # using most recent DOT VSL value
    df_window = df_window.set_index(['year'])
    bac_threshold_scaled = int(bac_threshold*100) # need to scale the threshold to match how the data are stored

    # list of variables to return with MI estimates and standard errors
    results_vars = ['fat_sob_driver_acc_any_dds','fat_sob_nonveh_acc_any_dds','ec_ca_deaths_wo_own_adj']
    # for each mirep, store bootstrapped estimates and standard errors, for the 2-d array of parameters
    bs_estimates = numpy.zeros((mireps,2,len(df_window.index),len(results_vars)))
    # estimates and standard errors, calculated from bootstrapped estimates, for the 2-d array of parameters
    mi_estimates = numpy.zeros((2,len(df_window.index),len(results_vars)))
    for miidx in range(0,mireps):    
        print('Generating results for MI replicate ' + str(miidx+1))
        # for the given MI replicate build bootstrap estimates and standard errors
        bs_results = numpy.zeros((bsreps,len(df_window.index),len(results_vars)))
        for bsidx in range(0,bsreps):   
            df_externality = pandas.DataFrame(index=df_accident.index)
            if bsidx>0: # draw random samples within each year for bootstrapping
                df_externality = df_externality.sample(frac=1,replace=True)
            
            # estimate relative risks and prevalence for each window year
            df_window_estimates = df_window.merge(pandas.DataFrame(index=df_window.index,columns=['theta','lambda','prevalence'],dtype=numpy.float64),on=['year'])
            for wyr in df_window.index.to_numpy():
                analytic_sample = get_analytic_sample(df_externality.merge(df_accident,on=['year','st_case']),
                        df_vehicle,df_person,(wyr-4),wyr,20,4,'impaired_vs_sober',
                        bac_threshold=bac_threshold,state_year_prop_threshold=1,mireps=mireps,summarize_sample=False)
                # because we're bootstrapping the entire calculation, hack fit_model by just estimating 1 bootstrap replicate
                mod_res,model_llf,model_df_resid = estimate.fit_model(analytic_sample,equal_mixing,2,bsreps=1,mirep=(miidx+1))
                df_window_estimates.at[wyr,'theta'] = mod_res[0][0][0]
                df_window_estimates.at[wyr,'lambda'] = mod_res[0][1][0]
                df_window_estimates.at[wyr,'prevalence'] = mod_res[0][2][0]/(1+mod_res[0][2][0]) # N is converted to prevalence
            
            # merge in relevant person info (don't need any vehicle info, and it makes merging more challenging)
            df_externality = df_externality.merge(df_person.reset_index().set_index(['year','st_case'])[['veh_no','per_no','seat_pos','inj_sev','mibac' + str(miidx+1)]],how='inner',on=['year','st_case']).reset_index().set_index(['year','st_case','veh_no','per_no'])
            # after person merge, assign count of vehicles
            df_externality['veh_count'] = df_externality.index.droplevel(['year','st_case','per_no'])
            df_externality['veh_count'] = df_externality['veh_count'].groupby(['year','st_case']).max() # number of vehicles involved in accident
            # keep only those accidents that involved at least one vehicle
            df_externality = df_externality.loc[df_externality['veh_count']>0]
        
            # now merge in analysis window data
            # restrict only to accidents that are in the end of analysis window years
            df_externality = df_externality.reset_index().set_index(['year']).merge(df_window_estimates,on=['year']).reset_index().set_index(['year','st_case','veh_no','per_no'])
        
            # note that many of the created variables below do not precisely handle missing values...
            # this is because we sum them at the end, so "False" or zero values are simply not included in the sums
            # person identified as drinking if the majority of considered MI replicates indicate it
            df_externality['per_drinking'] = df_externality['mibac' + str(miidx+1)]>bac_threshold_scaled
            df_externality['fatality'] = (df_externality['inj_sev']==4) # is a fatality
            df_externality['driver'] = (df_externality['seat_pos']==11) # is a driver
            df_externality['dd'] = (df_externality['per_drinking'] & df_externality['driver']) # is a drinking driver
            df_externality['acc_num_dds'] = df_externality['dd'].groupby(['year','st_case']).sum() # number of drinking drivers in accident
            df_externality['acc_any_dds'] = (df_externality['acc_num_dds']>0) # accident with at least one drinking driver
            df_externality['veh_num_dds'] = df_externality['dd'].astype(int).groupby(['year','st_case','veh_no']).sum() # number of drinking drivers in a vehicle
            df_externality['sd'] = (~df_externality['per_drinking'] & df_externality['driver']) # is a sober driver
            df_externality['acc_num_sds'] = df_externality['sd'].groupby(['year','st_case']).sum() # number of sober drivers in accident
            df_externality['fat_acc_any_dds'] = (df_externality['acc_any_dds'] & df_externality['fatality']) # fatality in an accident with at least one drinking driver    
            df_externality['fat_sob_nonveh_acc_any_dds'] = (df_externality['fatality'] & (df_externality['seat_pos']==0) & df_externality['acc_any_dds'] & ~df_externality['per_drinking']) # SOBER NON-VEHICLE OCCUPANT (PEDESTRIANS, CYCLISTS, ETC) KILLED IN ACCIDENT INVOLVING DRUNK DRIVER
            df_externality['fat_sob_driver_acc_any_dds'] = (df_externality['fatality'] & df_externality['acc_any_dds'] & (df_externality['veh_num_dds']==0)) # DEATH IN NON-DRINKING DRIVER VEHICLE IN ACCIDENT INVOLVING DRUNK DRIVER
            df_externality['acc_num_fsndds'] = df_externality['fat_sob_nonveh_acc_any_dds'].groupby(['year','st_case']).sum() # NUMBER OF SOBER NON-VEHICLE OCCUPANTS (PEDESTRIANS, CYCLISTS, ETC) KILLED IN ACCIDENT INVOLVING DRUNK DRIVER
            df_externality['acc_any_fsndds'] = (df_externality['acc_num_fsndds']>0) # IS AN ACCIDENT WITH AT LEAST ONE SOBER NON-VEHICLE OCCUPANT (PEDESTRIANS, CYCLISTS, ETC) KILLED INVOLVING DRUNK DRIVER
        
            # collapse counts by accidents
            df_externality = pandas.concat([df_externality[['veh_count','acc_num_dds','acc_any_dds','acc_num_sds','acc_any_fsndds','lambda','theta','prevalence','annual_vmt']].groupby(['year','st_case']).mean(),
                                                df_externality[['fatality','driver','dd','fat_acc_any_dds','fat_sob_nonveh_acc_any_dds','fat_sob_driver_acc_any_dds']].groupby(['year','st_case']).sum()],axis='columns')
            df_externality = df_externality.loc[~((df_externality['acc_num_dds']==0) & (df_externality['acc_num_sds']==0))] # drop accidents with driverless cars
            
            # create counterfactual avoidable weights for drinking drivers
            df_externality['cf_wt'] = numpy.nan
            df_externality.loc[(df_externality['acc_num_dds']>0) & (df_externality['veh_count']>1),'cf_wt'] = df_externality['acc_num_dds']*(df_externality['theta'] - 1)/(df_externality['theta']*df_externality['acc_num_dds'] + df_externality['acc_num_sds']) # COUNTERFACTUAL AVOIDABLE WEIGHT FOR MULTI-VEHICLE CRASHES AND AT LEAST ONE DRINKING DRIVER
            df_externality.loc[(df_externality['acc_num_dds']>0) & (df_externality['veh_count']==1),'cf_wt'] = (df_externality['lambda'] - 1)/df_externality['lambda'] # COUNTERFACTUAL AVOIDABLE WEIGHT FOR SINGLE-VEHICLE CRASHES WITH A DRINKING DRIVER
            
            # construct aggregated results table
            agg_results = pandas.concat([df_externality[['lambda','theta','prevalence','annual_vmt']].groupby(['year']).mean(),                                
                                        df_externality[['fat_acc_any_dds','fat_sob_nonveh_acc_any_dds','fat_sob_driver_acc_any_dds']].multiply(df_externality['cf_wt'],axis='index').groupby(['year']).sum(),
                                        df_externality[['acc_any_dds','acc_any_fsndds']].groupby(['year']).sum()],                        
                                        axis='columns')    
                
            agg_results['annual_drinking_vmt'] = 0.16*agg_results['annual_vmt']*agg_results['prevalence'] # PROPORTION OF MILES DRIVEN ASSUMED BY DRUNK DRIVERS, RESTRICTING ONLY TO NIGHT MILES
            
            agg_results['ca_deaths_w_own_adj'] = agg_results['fat_sob_nonveh_acc_any_dds'] + agg_results['fat_acc_any_dds'] # COUNTERFACTUAL AVOIDABLE DEATHS, ASSUMING THAT OWN CAR DEATHS ARE COUNTABLE
            agg_results['vsl_ca_deaths_w_own_adj'] = agg_results['ca_deaths_w_own_adj']*dot_vsl # VSL OF COUNTERFACTUAL AVOIDABLE DEATHS, ASSUMING THAT OWN CAR DEATHS ARE COUNTABLE
            agg_results['ec_ca_deaths_w_own_adj'] = agg_results['vsl_ca_deaths_w_own_adj']/agg_results['annual_drinking_vmt'] # EXTERNAL COST OF COUNTERFACTUAL AVOIDABLE DEATHS, ASSUMING THAT OWN CAR DEATHS ARE COUNTABLE
            
            agg_results['ca_deaths_wo_own_adj'] = agg_results['fat_sob_nonveh_acc_any_dds'] + agg_results['fat_sob_driver_acc_any_dds'] # COUNTERFACTUAL AVOIDABLE DEATHS, ASSUMING THAT OWN CAR DEATHS AREN'T COUNTABLE
            agg_results['vsl_ca_deaths_wo_own_adj'] = agg_results['ca_deaths_wo_own_adj']*dot_vsl # VSL OF COUNTERFACTUAL AVOIDABLE DEATHS, ASSUMING THAT OWN CAR DEATHS AREN'T COUNTABLE
            agg_results['ec_ca_deaths_wo_own_adj'] = agg_results['vsl_ca_deaths_wo_own_adj']/agg_results['annual_drinking_vmt'] # EXTERNAL COST OF COUNTERFACTUAL AVOIDABLE DEATHS, ASSUMING THAT OWN CAR DEATHS AREN'T COUNTABLE
        
            agg_results['ca_acc'] = agg_results['acc_any_dds'] + agg_results['acc_any_fsndds'] # TOTAL NUMBER OF ACCIDENTS INVOLVING DRUNK DRIVERS
            
            bs_results[bsidx] = agg_results[results_vars].to_numpy()
        bs_estimates[miidx,0] = bs_results[0] # the first rep are estimates from original sample
        bs_estimates[miidx,1] = estimate.bs_se(bs_results,axis=0) # standard errors
    
    mi_estimates = estimate.mi_theta_se(bs_estimates)
    return mi_estimates