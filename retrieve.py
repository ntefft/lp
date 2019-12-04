# -*- coding: utf-8 -*-
"""
Created on Tue May  7 09:52:37 2019

@author: Nathan Tefft

This script connects to the NHTSA's FTP server and retrieves the annual zip files containing the FARS data. The files are stored in a 
data folder for later extraction.
"""

# import necessary packages
import ftplib, os, sys

"""
   USER-DEFINED ATTRIBUTES 
   
1) The years over which FARS datasets are retrieved. 
    The default values are 1975 (the first year of FARS) to 2017 (the latest available year)
    
2) The directory to which the data folder containing the FARS data files will exist.
    The user MUST set the 'parent' directory. 
    There is NO DEFAULT. 
    Failure to provide a parent will cause a syntax error
    We recommend wherever the GitHub repository is cloned.
    Data will then be placed into the subfolder .\GitHub\lpdt\data
"""

# FARS data range
firstYear = 1975
latestYear = 2017

# Parent directory
parent_dir = 


""" Retrieval Script """

# change working directory to GitHub path
if not os.path.exists(parent_dir + '\\GitHub\\lpdt'):
        os.makedirs(parent_dir + '\\GitHub\\lpdt')
os.chdir(parent_dir + '\\GitHub\\lpdt')

# connect to NHTSA's FTP server
ftp = ftplib.FTP('ftp.nhtsa.dot.gov')
ftp.login()

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
    
print("Retrieval of FARS data from " + str(firstYear) + " to " + str(latestYear) + " successfully completed.")