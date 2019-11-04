# -*- coding: utf-8 -*-
"""
Created on Tue May  7 09:52:37 2019

@author: Nathan Tefft
"""

import ftplib
import os
import sys

# change director to GitHub path
os.chdir(sys.path[0] + '\\Documents\\GitHub\\lp')

# connect to NHTSA's FTP server
ftp = ftplib.FTP('ftp.nhtsa.dot.gov')
ftp.login()

firstYear = 1975
latestYear = 2017

# retrieve each annual zipped files and store them in the data folder 
for yr in range(firstYear,latestYear+1):
    print("Retrieving data for " + str(yr) + ".")
    filenameLocal = 'data\\FARS' + str(yr) + '.zip'
    if not os.path.exists(os.path.dirname(filenameLocal)):
        os.makedirs(os.path.dirname(filenameLocal))
    
    ftp.cwd('\\fars\\' + str(yr) + '\\National')
    fileLocal = open(filenameLocal, 'wb')
    ftp.retrbinary('RETR FARS' + str(yr) + 'NationalCSV.zip', fileLocal.write)
    fileLocal.close()