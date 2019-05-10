# -*- coding: utf-8 -*-
"""
Created on Fri May 10 11:41:35 2019

@author: ntefft
"""

import numpy, pandas

# function that identifies a vehicle's driver as drunk, depending on Levitt & Porter definition of interest
def driver_drinking_status(df_vehicle, df_person, definition = 'mi', bac_threshold = 0.08):
    df_veh_driver = df_vehicle.merge(df_person.loc[df_person['seat_pos']==11],how='left',on=['year','st_case','veh_no'],validate='1:m') # keep only drivers from the person file and merge them in
    df_veh_driver = df_veh_driver.loc[~df_veh_driver.index.duplicated()] # drop the first of duplicate drivers (when there were two persons in the driver seat)
    
    # DRINKING DEFINITIONS
    # mi: use multiple imputation values
    # police_report_only: police officer report [0 if nondrinking, 1 if drinking, 8 if not reported, 9 if unknown] (definition 1 in L&P, 2001; what LP say they use)
    # any_evidence: drinking if any evidence, not drinking otherwise (definition 2 in paper; what LP actually use)
    # police_report_primary: officer report primary, missing values adjusted by BAC test (definition 3 in paper)
    # bac_test_primary: BAC test primary (definition 4 in paper)
    # impaired_vs_sober: Legal impairment based on tested BAC, compared against not drinking (intermediate values dropped...this is the supplemental analysis in LP)
    
    bac_threshold_scaled = bac_threshold*100 # need to scale the threshold to match how the data are stored
    
    if definition == 'mi':
        df_driver_drink_status = df_veh_driver[['mibac1','mibac2','mibac3','mibac4','mibac5','mibac6','mibac7','mibac8','mibac9','mibac10']] > bac_threshold_scaled        
        df_driver_drink_status = df_driver_drink_status.astype('int')
        df_driver_drink_status = df_driver_drink_status.rename(columns={'mibac1':'drink_status1','mibac2':'drink_status2','mibac3':'drink_status3','mibac4':'drink_status4','mibac5':'drink_status5','mibac6':'drink_status6','mibac7':'drink_status7','mibac8':'drink_status8','mibac9':'drink_status9','mibac10':'drink_status10',}) # rename columns 
    elif definition == 'police_report_only':
        df_driver_drink_status = df_veh_driver[['drinking']]
        df_driver_drink_status = df_driver_drink_status.rename(columns={'drinking':'drink_status'}) # rename columns   
    elif definition == 'any_evidence':
        df_driver_drink_status = df_veh_driver[['dr_drink']]
        df_driver_drink_status = df_driver_drink_status.rename(columns={'dr_drink':'drink_status'}) # rename columns   
    elif definition == 'police_report_primary':
        df_driver_drink_status = df_veh_driver[['drinking','alcohol_test_result']]
        df_driver_drink_status['drink_status'] = df_driver_drink_status['drinking']
        df_driver_drink_status.loc[df_driver_drink_status['alcohol_test_result']==0 & (df_driver_drink_status['drinking'].isin([8,9]) | df_driver_drink_status['drinking'].isna()), 'drink_status'] = 0
        df_driver_drink_status.loc[df_driver_drink_status['alcohol_test_result']>0 & (df_driver_drink_status['drinking'].isin([8,9]) | df_driver_drink_status['drinking'].isna()), 'drink_status'] = 1         
        df_driver_drink_status = df_driver_drink_status[['drink_status']]
    elif definition == 'bac_test_primary':
        df_driver_drink_status = df_veh_driver[['drinking','alcohol_test_result']]
        df_driver_drink_status['drink_status'] = df_driver_drink_status['drinking']
        df_driver_drink_status.loc[df_driver_drink_status['alcohol_test_result']==0, 'drink_status'] = 0
        df_driver_drink_status.loc[df_driver_drink_status['alcohol_test_result']>bac_threshold_scaled, 'drink_status'] = 1
        df_driver_drink_status = df_driver_drink_status[['drink_status']]
    elif definition == 'impaired_vs_sober':
        df_driver_drink_status = df_veh_driver[['dr_drink','alcohol_test_result']]
        df_driver_drink_status['drink_status'] = numpy.nan
        df_driver_drink_status.loc[(df_driver_drink_status['alcohol_test_result']==0) | (df_driver_drink_status['dr_drink']==0), 'drink_status'] = 0
        df_driver_drink_status.loc[(df_driver_drink_status['alcohol_test_result']>=bac_threshold_scaled) & (df_driver_drink_status['dr_drink']!=0), 'drink_status'] = 1
        df_driver_drink_status = df_driver_drink_status[['drink_status']]
    
    return df_driver_drink_status

#test = driver_drinking_status(df_vehicle, df_person, definition = 'impaired_vs_sober')
#test.describe()
#test['drink_status'].value_counts()
