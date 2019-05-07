# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:29:49 2019

@author: ntefft
"""

import os
import sys
import pandas
import simpledbf
import zipfile

# path for Spyder or Jupyter Notebooks
if os.path.exists(sys.path[0] + '\\Documents\\GitHub\\lpdt'):
    os.chdir(sys.path[0] + '\\Documents\\GitHub\\lpdt')
else:
    os.chdir(sys.path[0])

firstYear = 1983
#latestYear = 2017
latestYear = 1983

archive = zipfile.ZipFile('data\\FSAS1983.zip', 'r')
acc_file = archive.read('ACCIDENT.SSD')
acc_df = simpledbf.Dbf5('data\\acc1983.dbf').to_dataframe()



for yr in range(firstYear,latestYear+1):