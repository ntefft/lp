# lp: Dunn, Richard A. and Nathan Tefft. Replicating the Levitt and Porter Estimates of Drunk Driving. Journal of Applied Econometrics, forthcoming.

This repo contains scripts implementing the estimation methods developed by Levitt and Porter (2001), hereafter LP. The scripts allow for direct download and extraction of the raw data from the Fatality Analysis Reporting System (FARS) from the National Highway Transportation Safety Administration (NHTSA), estimation of the maximum likelihood model, and replication of LP.

To replicate LP, run the following scripts, in order:

  1. retrieve.py to retrieve and save the raw data from NHTSA's FTP site. If this automated download process stops working (because of NHTSA web site changes), you can manually obtain the National FARS datasets between 1975 and 2017 from NHTSA's website (NHTSA, 1975-2017). The extract.py file (below) will look for them in the replication\data folder.
  2. extract.py (in the "replication" folder) to extract and harmonize relevant estimation variables across survey years. The combined accident, vehicle, and person files are stored in the replication\data folder.
  3. replicate.py (in the "replication" folder) to generate summary statistics and estimation results that replicate LP.

This repo has been designated a "template" so that you can easily copy it and generate your own project based on the estimation methods coded herein. Please note that the code has only been thoroughly tested for the purpose of replicating LP, so any departure from the models presented in the replication may require substantial additional code modifications and/or testing. If you would like your new project to receive any updates to our original lp code, we recommend creating your project as follows:

  1. Click on the "Use this template" button when viewing the lp repo on GitHub.com, and follow GitHub's instructions for creating a new copy of the lp repo.
  2. Use a command line, e.g. Git Bash, to add the original lp repo as the upstream repo: enter "cd [new-repo]" and then "git remote add upstream https://github.com/ntefft/lp.git".
  3. Perform a first pull request by entering "git pull upstream master --allow-unrelated-histories". This will align the commit histories so that subsequent pulls should be straightforward.
  4. Anytime you wish to subsequently pull updates made to the lp repo, enter "git pull upstream master".
  5. If you want to maintain updates to the replication code without automatically merging them into your code, you can create a copy of the "replication" folder, rename it, and then edit the contained scripts for your new project. 

References

Levitt, Steven D., and Jack Porter. How Dangerous are Drinking Drivers? Journal of Political Economy, 2001, 109(6), pgs. 1198-1237.

National Highway Transportation Safety Administration (NHTSA). 1975–2017. Fatality Analysis Reporting System. U. S. Department of Transportation, https://www.nhtsa.gov/node/97996/251 (accessed May 15, 2020).
