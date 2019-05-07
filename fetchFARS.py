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

firstYear = 1983
latestYear = 2017
for yr in range(firstYear,latestYear+1):
    filenameLocal = 'data\\FARS' + str(yr) + '.zip'
    if not os.path.exists(os.path.dirname(filenameLocal)):
        os.makedirs(os.path.dirname(filenameLocal))
    
    if yr <= 2011:
        ftp.cwd('\\fars\\' + str(yr) + '\\DBF')
    elif yr == 2012:
        ftp.cwd('\\fars\\' + str(yr) + '\\National\\DBF')
    else:
        ftp.cwd('\\fars\\' + str(yr) + '\\National')
    
    if yr <= 1993:
        filenameFetch = 'FARS' + str(yr) + '.zip'
    elif yr >= 1994 and yr <= 1999:
        filenameFetch = 'FARSDBF' + str(yr-1900) + '.zip'
    elif yr == 2000:
        filenameFetch = 'FARSDBF00.zip'
    elif yr >= 2001 and yr <= 2012:
        filenameFetch = 'FARS' + str(yr) + '.zip'
    elif yr >= 2013 and yr <= 2014:
        filenameFetch = 'FARS' + str(yr) + 'NationalDBF.zip'
    else:
        filenameFetch = 'FARS' + str(yr) + 'NationalCSV.zip'
    
    fileLocal = open(filenameLocal, 'wb')
    ftp.retrbinary('RETR ' + filenameFetch, fileLocal.write)
    fileLocal.close()