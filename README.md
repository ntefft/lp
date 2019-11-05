# lp: Estimating the prevalence and relative risk of drunk driving

This repo contains scripts implementing the estimation methods first developed by Levitt and Porter (2001), hereafter LP. The scripts allow for direct download and extraction of data from the Fatality Analysis Reporting System (from the NHTSA), estimation of the maximum likelihood model, and specifically replicate LP.

The user should run scripts in the following order:
1. retrieveFars.py (in the "estimation" folder) to retrieve the raw dat from NHTSA.
2. lpExtractFARS.py (in the "estimation" folder) to extract and harmonize relevant estimation variables across survey years.
3. lpReplicate.py (in the "replication" forlder) to generate summary statistics and estimation results for replicating LP.

Other scripts may be generated that use the underlying data and coded estimation methods, similar to the replication script, for new projects.
