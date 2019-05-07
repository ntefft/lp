# -*- coding: utf-8 -*-
"""
Created on Tue May  7 09:52:37 2019

@author: ntefft
"""

import ftplib
import os
import sys

os.chdir(sys.path[0] + '/Documents/GitHub/lpdt')

ftp = ftplib.FTP('ftp.nhtsa.dot.gov')
ftp.login()

firstYear = 1983
latestYear = 2017
for yr in range(firstYear,latestYear+1):
    filenameLocal = 'data/FSAS' + str(yr) + '.zip'
    if not os.path.exists(os.path.dirname(filenameLocal)):
        os.makedirs(os.path.dirname(filenameLocal))
    if yr <= 2011:
        ftp.cwd('/fars/' + str(yr) + '/SAS') 
    elif yr == 2012:
        ftp.cwd('/fars/' + str(yr) + '/National/SAS')
    else:
        ftp.cwd('/fars/' + str(yr) + '/National')
    
    if yr <= 1998:        
        filenameFetch = 'FSAS' + str(yr-1900) + '.zip'
    elif yr == 1999:
        filenameFetch = 'FARS99.zip'
    elif yr == 2000:        
        filenameFetch = 'FSAS00.zip'
    elif yr >= 2001 and yr <= 2012:
        filenameFetch = 'FSAS' + str(yr) + '.zip'
    else:
        filenameFetch = 'FARS' + str(yr) + 'NationalSAS.zip'
        
    fileLocal = open(filenameLocal, 'wb')
    ftp.retrbinary('RETR ' + filenameFetch, fileLocal.write)
    fileLocal.close()