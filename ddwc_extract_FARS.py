# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:29:49 2019

@author: ntefft
"""
import dbfread, os, sys, numpy, pandas, shutil, us, zipfile # import packages

# path for Spyder or Jupyter Notebooks
if os.path.exists(sys.path[0] + '\\Documents\\GitHub\\lpdt'):
    os.chdir(sys.path[0] + '\\Documents\\GitHub\\lpdt')
else:
    os.chdir(sys.path[0])

# load state abbreviations for merging in later
df_states = pandas.DataFrame.from_dict(us.states.mapping('fips', 'abbr'),orient='index',columns=['state_abbr'])
df_states = df_states[df_states.index.notnull()]
df_states.index = df_states.index.astype(int)

firstYear = 1983
#firstYear = 2017
latestYear = 2017

df_accident = pandas.DataFrame() # initialize analytic dataframe
df_vehicle = pandas.DataFrame() # initialize analytic dataframe
df_person = pandas.DataFrame() # initialize analytic dataframe

for yr in range(firstYear,latestYear+1): 
    print('Extracting data from ' + str(yr) + '.' )
    
    # extract accident, person, and vehicle files
    zipfile.ZipFile('data\\FARS' + str(yr) + '.zip', 'r').extractall(path='data\\extracted')
    if yr <= 1993:
        for ft in ['acc','veh','per']:
            vars()['df_' + ft + '_yr'] = pandas.DataFrame(dbfread.DBF('data\\extracted\\' + ft + str(yr) + '.dbf',char_decode_errors='replace'))
    elif 1994 <= yr <= 2014:
        df_acc_yr = pandas.DataFrame(dbfread.DBF('data\\extracted\\accident.dbf',char_decode_errors='replace'))
        df_veh_yr = pandas.DataFrame(dbfread.DBF('data\\extracted\\vehicle.dbf',char_decode_errors='replace'))
        df_per_yr = pandas.DataFrame(dbfread.DBF('data\\extracted\\person.dbf',char_decode_errors='replace'))
    else:
        df_acc_yr = pandas.read_csv('data\\extracted\\accident.csv')
        # need to remove non-utf-8 encoding errors
        veh_file = open('data\\extracted\\vehicle.csv',encoding='utf-8', errors='replace')
        df_veh_yr = pandas.read_csv(veh_file) 
        veh_file.close()
        df_per_yr = pandas.read_csv('data\\extracted\\person.csv')
        
    # extract multiple imputation files
    if yr <= 1993:
        zipfile.ZipFile('data\\MISEQL' + str(yr) + '.zip', 'r').extractall(path='data\\extracted')
        df_mi_yr = pandas.read_fwf('data\\extracted\\Miper'  + str(yr-1900) +  '.dat',widths=[4,7,3,2,4,2,2,2,2,2,2,2,2,2])
        df_mi_yr.columns = ['year','st_case','veh_no','per_no','p1','p2','p3','p4','p5','p6','p7','p8','p9','p10']
    elif 1994 <= yr <= 1997:
        df_mi_yr = pandas.DataFrame(dbfread.DBF('data\\extracted\\Miper'  + str(yr-1900) + '.dbf',char_decode_errors='replace'))
    elif 1998 <= yr <= 2008:
        df_mi_yr = pandas.DataFrame(dbfread.DBF('data\\extracted\\Miper.dbf',char_decode_errors='replace'))
    elif 2009 <= yr <= 2011:
        zipfile.ZipFile('data\\MIDBF' + str(yr) + '.zip', 'r').extractall(path='data\\extracted')
        df_mi_yr = pandas.DataFrame(dbfread.DBF('data\\extracted\\Miper.dbf',char_decode_errors='replace'))
    elif 2012 <= yr <= 2014:
        df_mi_yr = pandas.DataFrame(dbfread.DBF('data\\extracted\\Miper.dbf',char_decode_errors='replace'))
    else:
        df_mi_yr = pandas.read_csv('data\\extracted\\Miper.csv')
    
    for ft in ['acc','veh','per','mi']:
        vars()['df_' + ft + '_yr'].columns = vars()['df_' + ft + '_yr'].columns.str.lower() # convert all columns to lower case    
    shutil.rmtree(path='data\\extracted')

    # PREPARE THE ANNUAL ACCIDENT VARIABLES   
    df_acc_yr.set_index([numpy.full(len(df_acc_yr.index), yr),'st_case'],inplace=True) # set the multiindex as year and st_case
        
    df_acc_yr.loc[df_acc_yr.hour==99, 'hour'] = numpy.nan
    df_acc_yr.loc[df_acc_yr.hour==24, 'hour'] = 0
    df_acc_yr.loc[df_acc_yr.day_week==9, 'day_week'] = numpy.nan
    df_acc_yr['quarter'] = numpy.ceil(df_acc_yr['month']/3) # create quarter variable
    
    df_acc_yr = df_acc_yr.merge(df_states,how='left',left_on='state',right_index=True) # merge in state abbreviations
    
    # keep variables to be used from the accidents file
    df_acc_yr = df_acc_yr[['state','state_abbr','quarter','day_week','hour','persons']]
    df_accident = df_accident.append(df_acc_yr)

    # PREPARE THE ANNUAL VEHICLE VARIABLES
    df_veh_yr.set_index([numpy.full(len(df_veh_yr.index), yr),'st_case','veh_no'],inplace=True) # set the multiindex as year and st_case 
	
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
    df_per_yr.set_index([numpy.full(len(df_per_yr.index), yr),'st_case','veh_no','per_no'],inplace=True) # set the multiindex as year and year, st_case, veh_no, per_no 
               
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
    
    df_per_yr.loc[df_per_yr.age>=998, 'age'] = numpy.nan # age
    df_per_yr['age_lt15'] = df_per_yr['age'] < 15 # less than 15 defined as child for our purposes
    df_per_yr.loc[df_per_yr.sex.isin([8,9]), 'sex'] = numpy.nan # sex
    df_per_yr.loc[df_per_yr.race==99, 'race'] = numpy.nan # race
    
    df_mi_yr.set_index([numpy.full(len(df_mi_yr.index), yr),'st_case','veh_no','per_no'],inplace=True) # set the multiindex as year and year, st_case, veh_no, per_no 
    df_per_yr = df_per_yr.merge(df_mi_yr,how='left',left_index=True,right_index=True) # merge in multiply imputed bac values
    
    df_per_yr = df_per_yr[['drinking','alc_det','atst_typ','alcohol_test_result','race','rest_use','age','age_lt15','sex','p1','p2','p3','p4','p5','p6','p7','p8','p9','p10']]
    df_person = df_person.append(df_per_yr)
    
    for ft in ['acc','veh','per','mi']: # clean up memory
        del vars()['df_' + ft + '_yr']

df_accident_desc = df_accident.describe()
df_vehicle_desc = df_vehicle.describe()
df_person_desc = df_person.describe()

df_accident.to_csv('data\\df_accident.csv')
df_vehicle.to_csv('data\\df_vehicle.csv')
df_person.to_csv('data\\df_person.csv')