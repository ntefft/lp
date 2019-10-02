# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:29:49 2019

@author: ntefft
"""
#import dbfread, os, sys, numpy, pandas, shutil, us, zipfile # import packages
import os, sys, numpy, pandas, shutil, us, zipfile # import packages

# path for Spyder or Jupyter Notebooks
if os.path.exists(sys.path[0] + '\\Documents\\GitHub\\lpdt'):
    os.chdir(sys.path[0] + '\\Documents\\GitHub\\lpdt')
else:
    os.chdir(sys.path[0])

# load state abbreviations for merging in later
df_states = pandas.DataFrame.from_dict(us.states.mapping('fips', 'abbr'),orient='index',columns=['state_abbr'])
df_states = df_states[df_states.index.notnull()]
df_states.index = df_states.index.astype(int)

firstYear = 1982 # 1982 is the first for which multiple imputation files are available
#firstYear = 2016
latestYear = 2017

df_accident = pandas.DataFrame() # initialize analytic dataframe
df_vehicle = pandas.DataFrame() # initialize analytic dataframe
df_person = pandas.DataFrame() # initialize analytic dataframe

for yr in range(firstYear,latestYear+1): 
    print('Extracting data from ' + str(yr) + '.' )
    
    # extract accident, person, and vehicle files
    zipfile.ZipFile('data\\FARS' + str(yr) + '.zip', 'r').extractall(path='data\\extracted')

    # need to remove non-utf-8 encoding errors
    acc_file = open('data\\extracted\\accident.csv',encoding='utf-8', errors='replace')
    df_acc_yr = pandas.read_csv(acc_file)
    acc_file.close()
    # need to remove non-utf-8 encoding errors
    veh_file = open('data\\extracted\\vehicle.csv',encoding='utf-8', errors='replace')
    df_veh_yr = pandas.read_csv(veh_file) 
    veh_file.close()
    df_per_yr = pandas.read_csv('data\\extracted\\person.csv')
        
    # extract multiple imputation files  
    df_mi_yr = pandas.read_csv('data\\extracted\\Miper.csv')    
    
    for ft in ['acc','veh','per','mi']:
        vars()['df_' + ft + '_yr'].columns = vars()['df_' + ft + '_yr'].columns.str.lower() # convert all columns to lower case    
    shutil.rmtree(path='data\\extracted')

    # PREPARE THE ANNUAL ACCIDENT VARIABLES   
    df_acc_yr['st_case'] = df_acc_yr['st_case'].astype('int')
    df_acc_yr.set_index([numpy.full(len(df_acc_yr.index), yr),'st_case'],inplace=True) # set the multiindex as year and st_case
    df_acc_yr.index.set_names(['year','st_case'], inplace=True)
        
    df_acc_yr.loc[df_acc_yr.hour==99, 'hour'] = numpy.nan
    df_acc_yr.loc[df_acc_yr.hour==24, 'hour'] = 0
    df_acc_yr.loc[df_acc_yr.day_week==9, 'day_week'] = numpy.nan
    df_acc_yr['quarter'] = numpy.ceil(df_acc_yr['month']/3) # create quarter variable
    
    df_acc_yr = df_acc_yr.merge(df_states,how='left',left_on='state',right_index=True) # merge in state abbreviations
    
    # keep variables to be used from the accidents file
    df_acc_yr = df_acc_yr[['state','state_abbr','quarter','day_week','hour','persons']]
    df_accident = df_accident.append(df_acc_yr)

    # PREPARE THE ANNUAL VEHICLE VARIABLES
    df_veh_yr[['st_case','veh_no']] = df_veh_yr[['st_case','veh_no']].astype('int')
    df_veh_yr.set_index([numpy.full(len(df_veh_yr.index), yr),'st_case','veh_no'],inplace=True) # set the multiindex as year and st_case 
    df_veh_yr.index.set_names(['year','st_case','veh_no'], inplace=True)
	
    if yr <= 2008: # number of occupants
        df_veh_yr['occupants'] = df_veh_yr['ocupants']
    else:
        df_veh_yr['occupants'] = df_veh_yr['numoccs']
    if yr <= 2015:
        df_veh_yr.loc[df_veh_yr.occupants>=99, 'occupants'] = numpy.nan
    else:
        df_veh_yr.loc[df_veh_yr.occupants>=97, 'occupants'] = numpy.nan
	
    df_veh_yr.loc[df_veh_yr.mod_year.isin([0,99,9998,9999]), 'mod_year'] = numpy.nan # model year
    if yr <= 1997:
        df_veh_yr['mod_year'] = df_veh_yr['mod_year'] + 1900 # model year
	
    for vt in ['acc','sus','dwi','spd','oth']:
        df_veh_yr.loc[df_veh_yr['prev_' + vt] > 97, 'prev_' + vt] = numpy.nan # previous violations

    df_veh_yr = df_veh_yr[['prev_acc','prev_sus','prev_dwi','prev_spd','prev_oth','mod_year','dr_drink','occupants']]
    df_vehicle = df_vehicle.append(df_veh_yr)

    # PREPARE THE ANNUAL PERSON VARIABLES
    df_per_yr[['st_case','veh_no','per_no']] = df_per_yr[['st_case','veh_no','per_no']].astype('int')
    df_per_yr.set_index([numpy.full(len(df_per_yr.index), yr),'st_case','veh_no','per_no'],inplace=True) # set the multiindex as year and year, st_case, veh_no, per_no 
    df_per_yr.index.set_names(['year','st_case','veh_no','per_no'], inplace=True)           
    
    if yr <= 1990: # alcohol test results
        df_per_yr['alcohol_test_result'] = df_per_yr['test_res']
    else:
        df_per_yr['alcohol_test_result'] = df_per_yr['alc_res']
    if yr >= 2015:
        df_per_yr['alcohol_test_result'] = df_per_yr['alcohol_test_result']/10
    df_per_yr.loc[df_per_yr.alcohol_test_result>=95, 'alcohol_test_result'] = numpy.nan    
    
    for vn in ['alc_det','atst_typ','race','rest_use']: # create variables if necessary
        if vn not in df_per_yr.columns:
            df_per_yr[vn] = numpy.nan
    df_per_yr.loc[df_per_yr.rest_use>=98, 'rest_use'] = numpy.nan # restraint use
    
    if yr <= 2008:
        df_per_yr.loc[df_per_yr.age==99, 'age'] = numpy.nan # age
    else:
        df_per_yr.loc[df_per_yr.age>=998, 'age'] = numpy.nan # age
    df_per_yr['age_lt15'] = df_per_yr['age'] < 15 # less than 15 defined as child for our purposes
    df_per_yr.loc[df_per_yr.sex.isin([8,9]), 'sex'] = numpy.nan # sex
    df_per_yr.loc[df_per_yr.race==99, 'race'] = numpy.nan # race
    df_per_yr.loc[df_per_yr.seat_pos>=98, 'seat_pos'] = numpy.nan # seat position
    
    df_mi_yr[['st_case','veh_no','per_no']] = df_mi_yr[['st_case','veh_no','per_no']].astype('int')
    if 'year' in df_mi_yr.columns: # going to rest the index
       df_mi_yr.drop(columns='year',inplace=True) 
    df_mi_yr.set_index([numpy.full(len(df_mi_yr.index), yr),'st_case','veh_no','per_no'],inplace=True) # set the multiindex as year and year, st_case, veh_no, per_no 
    df_mi_yr.index.set_names(['year','st_case','veh_no','per_no'], inplace=True)
    df_per_yr = df_per_yr.merge(df_mi_yr,how='left',on=['year','st_case','veh_no','per_no']) # merge in multiply imputed bac values

    df_per_yr = df_per_yr.rename(columns={'p1':'mibac1','p2':'mibac2','p3':'mibac3','p4':'mibac4','p5':'mibac5','p6':'mibac6','p7':'mibac7','p8':'mibac8','p9':'mibac9','p10':'mibac10'}) # rename bac columns    
    df_per_yr = df_per_yr[['seat_pos','drinking','alc_det','atst_typ','alcohol_test_result','race','rest_use','age','age_lt15','sex','mibac1','mibac2','mibac3','mibac4','mibac5','mibac6','mibac7','mibac8','mibac9','mibac10']]
    df_person = df_person.append(df_per_yr)
    
    for ft in ['acc','veh','per','mi']: # clean up memory 
        del vars()['df_' + ft + '_yr']

df_accident_desc = df_accident.describe()
df_vehicle_desc = df_vehicle.describe()
df_person_desc = df_person.describe()

df_accident.to_csv('data\\df_accident.csv')
df_vehicle.to_csv('data\\df_vehicle.csv')
df_person.to_csv('data\\df_person.csv')