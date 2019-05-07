# -*- coding: utf-8 -*-
"""
Created on Tue May  7 09:52:37 2019

@author: ntefft
"""

import ftplib

ftp = ftplib.FTP('ftp.nhtsa.dot.gov')
ftp.login()
ftp.cwd("/fars") 


for yr in range(1975,1975):
    handle = open(path.rstrip("/") + "/" + filename.lstrip("/"), 'wb')
    ftp.retrbinary('RETR %s' % filename, handle.write)

latestYear = 2017
for yr in range(1975,latestYear+1):
    print(yr)
    

