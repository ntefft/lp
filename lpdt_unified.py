# -*- coding: utf-8 -*-
"""
Created on Wed May 15 11:37:00 2019

@author: ntefft
"""

import os, sys, pandas, lpdtutil # import packages

# path for Spyder or Jupyter Notebooks
if os.path.exists(sys.path[0] + '\\Documents\\GitHub\\lpdt'):
    os.chdir(sys.path[0] + '\\Documents\\GitHub\\lpdt')
else:
    os.chdir(sys.path[0])

# read in FARS data
df_accident = pandas.read_csv('data\\df_accident.csv')
df_accident.set_index(['year','st_case'],inplace=True) # set the index
df_vehicle = pandas.read_csv('data\\df_vehicle.csv')
df_vehicle.set_index(['year','st_case','veh_no'],inplace=True) # set the index
df_person = pandas.read_csv('data\\df_person.csv')
df_person.set_index(['year','st_case','veh_no','per_no'],inplace=True) # set the index

# get estimation sample
test_est_sample = lpdtutil.get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=1983, last_year=2017)