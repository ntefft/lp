# -*- coding: utf-8 -*-
"""
Created on Wed May 15 11:37:00 2019

@author: ntefft
"""

import os, sys, numpy, pandas # import packages

# path for Spyder or Jupyter Notebooks
if os.path.exists(sys.path[0] + '\\Documents\\GitHub\\lpdt'):
    os.chdir(sys.path[0] + '\\Documents\\GitHub\\lpdt')
else:
    os.chdir(sys.path[0])
    
import lpdtutil

# read in FARS data
df_accident = pandas.read_csv('data\\df_accident.csv')
df_accident.set_index(['year','st_case'],inplace=True) # set the index
df_vehicle = pandas.read_csv('data\\df_vehicle.csv')
df_vehicle.set_index(['year','st_case','veh_no'],inplace=True) # set the index
df_person = pandas.read_csv('data\\df_person.csv')
df_person.set_index(['year','st_case','veh_no','per_no'],inplace=True) # set the index

# get estimation sample
A = lpdtutil.get_lpdt_estimation_sample(df_accident, df_vehicle, df_person, first_year=1983, last_year=2017, equal_mixing=['year','weekend','hour'])

# define the log-likehood for the model
# A is the set of accident data
# N[i] is the proportion of crashes of type i, relative to type 1
# thet[i] is the two-car crash relative risk of type i, relative to type 1
# lamb[i] is the one-car crash relative risk of type i, relative to type 1
def _ll_lpdt(A, thet, lamb, num_driver_types):
    # first substitute in for N values: incorporate information from single car crashes using the fact that larger observed quantities of one type suggest more drivers on the road of that type
    N = numpy.array()
    N[1] = 1
    for dt in range(2,num_driver_types+1):
        N[dt] = (1/lamb[dt])*(A['a_' + str(dt)]/A['a_1'])

    # build the probability values for accidents of each type: first build the probability denominator
    p_denom = 0
    for dto in range(1,num_driver_types+1):
        for dti in range(1,num_driver_types+1):
            p_denom += N[dto]*N[dti]*(thet[dto]+thet[dti])
    
    # next build the set of probabilities and add accidents
    for dto in range(1,num_driver_types+1):
        for dti in range(1,num_driver_types+1):
            if dti >= dto:
                p[dto][dti] = N[dto]*N[dti]*(thet[dto]+thet[dti])/p_denom
                if dti != dto:
                    p[dto][dti] = 2*p[dto][dti] # after eliminating the duplicates, need to add in the probability of observing the two types reversed
    
    # finally construct the likelihood function
    lnf = lpdtutil.lnfactorial(A['a_2veh_total']) # natural log of the factorial
    for dto in range(1,num_driver_types+1):
        for dti in range(1,num_driver_types+1):
            if dti >= dto:
                lnf += A['a_' + str(dto) + '_' + str(dti)]*log(p[dto][dti])
    
    ll = lnf
    return ll
    