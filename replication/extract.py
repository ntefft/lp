# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:29:49 2019

@author: Nathan Tefft

This script extracts data from the raw FARS data files to be used for replicating Levitt & Porter (2001). Selected variables are included, 
and the data definitions are harmonized across years. Accident, vehicle, and person dataframes are constructed and stored in csv files 
for later use in the replication.
"""

# This script has been validated for FARS datasets from 1982 to 2017

earliestYear=1982
latestYear = 2017

# install and import necessary packages
    # not all packages are standard installs
    # for example, us is not included in anaconda
    # you may need to install some of these packages in the command line

import os, numpy, pandas, shutil, us, zipfile

"""
   USER-DEFINED ATTRIBUTES 
      
1) The years over which FARS datasets are extracted and processed. 
    The default values are 1982 to 2017 
        **FARS begins in 1975, but the first year of imputed BAC is 1982
          If the user-provided first year is before 1982:
              -First year is reset to 1982
              -A warning message will appear to alert the user, but the script will not break.
         **FARS is updated annually, but this script is only validated through 2017
          If the user-provided last year is after 2017:
              -Last year is reset to 2017
              -A warning message will appear to alert the user, but the script will not break.     
          
    
2) The working directory.
    The user MUST set their own working directory before running the script. 
    We recommend the folder of the cloned GitHub repository.
        For example, set the working directory to "C:\\Users\\JoeEconomist\\GitHub\\lp"
    Data will then be placed into the subfolder .\replication\data
"""

#os.chdir("C:\\Users\\dunnr\\Documents\\GitHub\\lpdt")

# FARS data range
firstYear = 1982
lastYear = 2017


if firstYear>lastYear:
    print('User selected lastYear earlier than firstYear. firstYear has been set to ' + str(earliestYear) + ' and lastYear has been set to ' + str(latestYear) +'.')
    firstYear = earliestYear
    lastYear = latestYear
if firstYear < earliestYear:
    print('User selected firstYear prior to ' + str(earliestYear) + '. firstYear has been set to ' + str(earliestYear) +'.')
    firstYear = earliestYear
if lastYear > latestYear:
    print('User selected lastYear after ' + str(latestYear) + '. lastYear has been set to ' + str(latestYear) +'.')
    lastYear = latestYear

# load US state abbreviations for later merge
df_states = pandas.DataFrame.from_dict(us.states.mapping('fips', 'abbr'),orient='index',columns=['state_abbr'])
df_states = df_states[df_states.index.notnull()]
df_states.index = df_states.index.astype(int)

# Initialize analytic dataframe for the accident, vehicle, and person datasets

#fars_datasets = ['accident', 'vehicle', 'person', 'Miper']

fars_datasets = ['accident', 'vehicle', 'person', 'Miper']
dataset_ids = ['st_case','veh_no','per_no', 'per_no']

df_list={}
for dataset in fars_datasets:
    df_list[dataset]=pandas.DataFrame()
    
# loop over years to be included in the replication analysis
for yr in range(firstYear,lastYear+1): 
    print('Extracting data from ' + str(yr) + '.' )
    
    # extract accident, vehicle, person, and multiple imputation files
    zipfile.ZipFile('data\\FARS' + str(yr) + '.zip', 'r').extractall(path='data\\extracted')
    # UTF-8 encoding errors are ignored because they don't impact the relevant variables
        
    df_list_yr={}
    index_list=['year']
    for (dataset, id) in zip(fars_datasets,dataset_ids):
        file = open('data\\extracted\\' + dataset + '.csv', errors='ignore')
        df_list_yr[dataset]=pandas.read_csv(file)
        file.close()
    
        df_list_yr[dataset].columns = df_list_yr[dataset].columns.str.lower() # make all columns lowercase
        df_list_yr[dataset]['year']=numpy.full(len(df_list_yr[dataset].index), yr) # standardize the year variable to 4 digits
        
        if not dataset == 'Miper':
            index_list.append(id)
        df_list_yr[dataset][index_list] = df_list_yr[dataset][index_list].astype('int') # set the indices as integers
        df_list_yr[dataset].set_index(index_list, inplace=True) # set the multiindex
        df_list_yr[dataset].index.set_names(index_list, inplace=True)  

    shutil.rmtree(path='data\\extracted') # clean up temporary extractions folder
    
    # Manipulating accident data
    df_list_yr['accident'].loc[df_list_yr['accident'].hour==99, 'hour'] = numpy.nan
    df_list_yr['accident'].loc[df_list_yr['accident'].hour==24, 'hour'] = 0
    df_list_yr['accident'].loc[df_list_yr['accident'].day_week==9, 'day_week'] = numpy.nan
    df_list_yr['accident']['quarter'] = numpy.ceil(df_list_yr['accident']['month']/3) # create quarter variable
    df_list_yr['accident'] = df_list_yr['accident'].merge(df_states,how='left',left_on='state',right_index=True) # merge in state abbreviations

    # keep relevant accident variables and append to accident dataframe
    df_list_yr['accident'] = df_list_yr['accident'][['state','state_abbr','quarter','day_week','hour','persons']]
    print('Count of crashes: ' + str(len(df_list_yr['accident'])))
    df_list['accident'] = df_list['accident'].append(df_list_yr['accident'])
    
    # Manipulating vehicle data
    if yr <= 2008: 
        df_list_yr['vehicle']['occupants'] = df_list_yr['vehicle']['ocupants']
    else:
        df_list_yr['vehicle']['occupants'] = df_list_yr['vehicle']['numoccs']
    if yr <= 2015:
        df_list_yr['vehicle'].loc[df_list_yr['vehicle'].occupants>=99, 'occupants'] = numpy.nan
    else:
        df_list_yr['vehicle'].loc[df_list_yr['vehicle'].occupants>=97, 'occupants'] = numpy.nan	
    for vt in ['acc','sus','dwi','spd','oth']:
        df_list_yr['vehicle'].loc[df_list_yr['vehicle']['prev_' + vt] > 97, 'prev_' + vt] = numpy.nan # previous violations

    # keep relevant vehicle variables and append to vehicle dataframe
    df_list_yr['vehicle'] = df_list_yr['vehicle'][['prev_acc','prev_sus','prev_dwi','prev_spd','prev_oth','dr_drink','occupants']]
    print('Count of vehicles: ' + str(len(df_list_yr['vehicle'])))
    df_list['vehicle'] = df_list['vehicle'].append(df_list_yr['vehicle'])
    
    # Manipulating person variables
    
    #standardize alcohol test result
    if yr <= 1990: 
        df_list_yr['person']['alcohol_test_result'] = df_list_yr['person']['test_res']
    else:
        df_list_yr['person']['alcohol_test_result'] = df_list_yr['person']['alc_res']
    
    if yr >= 2015:
        df_list_yr['person']['alcohol_test_result'] = df_list_yr['person']['alcohol_test_result']/10
    
    df_list_yr['person'].loc[df_list_yr['person'].alcohol_test_result>=95, 'alcohol_test_result'] = numpy.nan    
    
    
    for vn in ['alc_det','atst_typ','race']: # create variables if necessary
        if vn not in df_list_yr['person'].columns:
            df_list_yr['person'][vn] = numpy.nan
    
    if yr <= 2008:
        df_list_yr['person'].loc[df_list_yr['person'].age==99, 'age'] = numpy.nan # age
    else:
        df_list_yr['person'].loc[df_list_yr['person'].age>=998, 'age'] = numpy.nan # age
    
    df_list_yr['person']['age_lt15'] = df_list_yr['person']['age'] < 15 # less than 15 defined as child for our purposes
    df_list_yr['person'].loc[df_list_yr['person'].sex.isin([8,9]), 'sex'] = numpy.nan # sex
    df_list_yr['person'].loc[df_list_yr['person'].race==99, 'race'] = numpy.nan # race
    df_list_yr['person'].loc[df_list_yr['person'].seat_pos>=98, 'seat_pos'] = numpy.nan # seat position
    
    # clean mulptiple imputation variables, e.g. harmonize names, ensure correct datatypes, and record missing variables 
    df_list_yr['Miper'] = df_list_yr['Miper'].rename(columns={'p1':'mibac1','p2':'mibac2','p3':'mibac3','p4':'mibac4','p5':'mibac5','p6':'mibac6','p7':'mibac7','p8':'mibac8','p9':'mibac9','p10':'mibac10'}) # rename bac columns    
    df_list_yr['person'] = df_list_yr['person'].merge(df_list_yr['Miper'],how='left',on=['year','st_case','veh_no','per_no']) # merge multiply imputed bac values into person dataframe
    
    # keep relevant person variables and append to person dataframe
    df_list_yr['person'] = df_list_yr['person'][['seat_pos','drinking','alc_det','atst_typ','alcohol_test_result','race','age','age_lt15','sex','mibac1','mibac2','mibac3','mibac4','mibac5','mibac6','mibac7','mibac8','mibac9','mibac10']]
    print('Count of persons: ' + str(len(df_list_yr['person'])))
    df_list['person'] = df_list['person'].append(df_list_yr['person'])
    
# summarize the constructed dataframes and save to csv files
if not os.path.exists('replication\\data'):
    os.makedirs('replication\\data')
for dfn in ['accident', 'vehicle', 'person']:
    print('Describing dataframe ' + dfn)
    print(df_list[dfn].describe())
    df_list[dfn].to_csv('replication\\data\\df_' + dfn + '.csv')