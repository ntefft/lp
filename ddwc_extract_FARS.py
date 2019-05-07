# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:29:49 2019

@author: ntefft
"""

import os
import sys
import numpy
import pandas
import simpledbf
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
#latestYear = 2017
latestYear = 1983

acc_file = zipfile.ZipFile('data\\FARS1983.zip', 'r').extract('acc1983.dbf',path='data')
df = simpledbf.Dbf5('data\\acc1983.dbf').to_dataframe()
df.columns = df.columns.str.lower() # convert all columns to lower case
df.set_index('st_case',inplace=True) # set the index as st_case
df.index = df.index.astype(int)

df['year'] = pandas.to_numeric(df['year']) # make sure year is stored as numeric
df.loc[df.year<100, 'year'] = df.loc[df.year<100, 'year'] + 1900 # convert from 2-digit to 4-digit years, when necessary
df.loc[df.hour==99, 'hour'] = numpy.nan
df.loc[df.hour==24, 'hour'] = 0
df.loc[df.day_week==9, 'day_week'] = numpy.nan
df['quarter'] = numpy.ceil(df['month']/3) # create quarter variable

df = df.merge(df_states,how='left',left_on='state',right_index=True) # merge in state abbreviations

# keep variables to be used from the accidents file
df = df[['state','state_abbr','year','quarter','day_week','hour','persons']]

for yr in range(firstYear,latestYear+1):