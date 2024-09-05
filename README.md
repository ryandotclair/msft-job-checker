# Purpose
The default Microsoft career site's job alert feature doesn't take into account IC or M levels. This simple script scrapes all job postings via the public API, filters on the specific IC or M level you're interested in, and alerts you via the Pushover.net service (which has a mobile app) if there's any new job listings.

# Requirements
- [Pushover.net](https://Pushover.net) (30 day free trial, then a one-time $5 charge for lifetime access)
- Docker

# Installation Steps
- Register an "app" with pushover.net (you'll need that token, as well as your pushover.net user token)
- git clone this repo
- Run `docker build -t msft-monitor .`
> Note: If docker run fails with an error about "PermissionError: [Errno 1] Operation not permitted", which happened on my rasberry pi4, to get past it I downgraded libseccomp library. Steps:
>   - Run `wget http://ftp.us.debian.org/debian/pool/main/libs/libseccomp/libseccomp2_2.5.1-1~bpo10+1_armhf.deb` 
>   - Run `sudo apt install ./libseccomp2_2.5.1-1~bpo10+1_armhf.deb`

# Usage
To run the script stand-alone, simply run `docker run -it -e APP_TOKEN="<app_token>" -e USER_TOKEN="<user_token>" -v .:/appdata msft-monitor` from a folder you want the two job files to be generated at (jobs.new.txt [what's latest list of jobs] and jobs.txt [list of jobs already known])

> Note: 
> - You'll need to plug in Pushover.net's app and user token. The App token is created when you register a new app. The User token is tied to your user.
> - Script looks specifically for /appdata folder in the container, and it only works when data persists across runs (read: must use -v)
> - I've included a jobs.sh file that you can point contab to (example of it running every hour example on a pi4: `0 * * * * /bin/bash /home/pi/jobs/jobs.sh`)... be sure to update the tokens and the path you want the files to live in. This script also assumes you've done the docker build command on the machine.

# Behavior
- 3 Files get generated from this script:
  - `jobs.txt` holds the "last run" and is used to compare against the newest job grab
  - `jobs.new.txt` hold the latest job listing. If there's a job in this file that's not in the jobs.txt file, then that job's URL gets pushed to your phone
  - `jobs.log` stores all the logs, and should automatically get pruned if it exceeds 1MB
- By default this checks for all jobs in the US that are 100% remote and are full time. Lines 38 and 82 in job.py is where you can adjust these to narrow the scope.