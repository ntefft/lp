# -*- coding: utf-8 -*-
"""
Created on Tue May  7 09:52:37 2019

@author: ntefft
"""

import ftplib
import os
import sys

# path for Spyder or Jupyter Notebooks
if os.path.exists(sys.path[0] + '\\Documents\\GitHub\\lpdt'):
    os.chdir(sys.path[0] + '\\Documents\\GitHub\\lpdt')
else:
    os.chdir(sys.path[0])

ftp = ftplib.FTP('ftp.nhtsa.dot.gov')
ftp.login()

firstYear = 1975
latestYear = 2017

# first fetch the accident, person, and vehicle files
for yr in range(firstYear,latestYear+1):
    print("Fetching data for " + str(yr) + ".")
    filenameLocal = 'data\\FARS' + str(yr) + '.zip'
    if not os.path.exists(os.path.dirname(filenameLocal)):
        os.makedirs(os.path.dirname(filenameLocal))
    
    ftp.cwd('\\fars\\' + str(yr) + '\\National')
    fileLocal = open(filenameLocal, 'wb')
    ftp.retrbinary('RETR FARS' + str(yr) + 'NationalCSV.zip', fileLocal.write)
    fileLocal.close()