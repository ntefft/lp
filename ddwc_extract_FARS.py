# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:29:49 2019

@author: ntefft
"""

import dbfread
import os
import sys
import numpy
import pandas
import shutil
import us
import zipfile

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
latestYear = 2017

df = pandas.DataFrame() # initialize analytic dataframe

for yr in range(firstYear,latestYear+1): 
    print('Extracting data from ' + str(yr) + '.' )
    
    # extract accident, person, and vehicle files
    zipfile.ZipFile('data\\FARS' + str(yr) + '.zip', 'r').extractall(path='data\\extracted')
    if yr <= 1993:
        for ft in ['acc','veh','per']:
            vars()[ft + '_df'] = pandas.DataFrame(dbfread.DBF('data\\extracted\\' + ft + str(yr) + '.dbf',char_decode_errors='replace'))
    elif 1994 <= yr <= 2014:
        acc_df = pandas.DataFrame(dbfread.DBF('data\\extracted\\accident.dbf',char_decode_errors='replace'))
        veh_df = pandas.DataFrame(dbfread.DBF('data\\extracted\\vehicle.dbf',char_decode_errors='replace'))
        per_df = pandas.DataFrame(dbfread.DBF('data\\extracted\\person.dbf',char_decode_errors='replace'))
    else:
        acc_df = pandas.read_csv('data\\extracted\\accident.csv')
        # need to remove non-utf-8 encoding errors
        veh_file = open('data\\extracted\\vehicle.csv',encoding='utf-8', errors='replace')
        veh_df = pandas.read_csv(veh_file) 
        veh_file.close()
        per_df = pandas.read_csv('data\\extracted\\person.csv')
        
    # extract multiple imputation files
    if yr <= 1993:
        zipfile.ZipFile('data\\MISEQL' + str(yr) + '.zip', 'r').extractall(path='data\\extracted')
        mi_df = pandas.read_fwf('data\\extracted\\Miper'  + str(yr-1900) +  '.dat',widths=[4,7,3,2,4,2,2,2,2,2,2,2,2,2])
        mi_df.columns = ['year','st_case','veh_no','per_no','p1','p2','p3','p4','p5','p6','p7','p8','p9','p10']
    elif 1994 <= yr <= 1997:
        mi_df = pandas.DataFrame(dbfread.DBF('data\\extracted\\Miper'  + str(yr-1900) + '.dbf',char_decode_errors='replace'))
    elif 1998 <= yr <= 2008:
        mi_df = pandas.DataFrame(dbfread.DBF('data\\extracted\\Miper.dbf',char_decode_errors='replace'))
    elif 2009 <= yr <= 2011:
        zipfile.ZipFile('data\\MIDBF' + str(yr) + '.zip', 'r').extractall(path='data\\extracted')
        mi_df = pandas.DataFrame(dbfread.DBF('data\\extracted\\Miper.dbf',char_decode_errors='replace'))
    elif 2012 <= yr <= 2014:
        mi_df = pandas.DataFrame(dbfread.DBF('data\\extracted\\Miper.dbf',char_decode_errors='replace'))
    else:
        mi_df = pandas.read_csv('data\\extracted\\Miper.csv')
    
    for ft in ['acc','veh','per','mi']:
        vars()[ft + '_df'].columns = vars()[ft + '_df'].columns.str.lower() # convert all columns to lower case    
    shutil.rmtree(path='data\\extracted')



    df_yr = acc_df # start building main analytic dataframe
    df_yr.set_index('st_case',inplace=True) # set the index as st_case
    df_yr.index = df_yr.index.astype(int)
    
    df_yr['year'] = pandas.to_numeric(df_yr['year']) # make sure year is stored as numeric
    df_yr.loc[df_yr.year<100, 'year'] = df_yr.loc[df_yr.year<100, 'year'] + 1900 # convert from 2-digit to 4-digit years, when necessary
    df_yr.loc[df_yr.hour==99, 'hour'] = numpy.nan
    df_yr.loc[df_yr.hour==24, 'hour'] = 0
    df_yr.loc[df_yr.day_week==9, 'day_week'] = numpy.nan
    df_yr['quarter'] = numpy.ceil(df_yr['month']/3) # create quarter variable
    
    df_yr = df_yr.merge(df_states,how='left',left_on='state',right_index=True) # merge in state abbreviations
    
    # keep variables to be used from the accidents file
    df_yr = df_yr[['state','state_abbr','year','quarter','day_week','hour','persons']]

    df.append(df_yr)

