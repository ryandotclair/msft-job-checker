import requests
import urllib3
import os
import logging
from logging.handlers import RotatingFileHandler

# Define various configs
hr_levels=["IC5","IC6","IC7"]
exclude_titles=["Software Engineer", "Scientist", "Research", "Architect", "Product Manager"]
max_log_size = 50 * 1024  # Limit it to 50KB
backup_count = 3  # Keep 3 backup files

# Define the file names
new_jobs_file = '/appdata/jobs.new.txt'
jobs_file = '/appdata/jobs.txt'

# Define Pushover.net tokens
user_token = os.getenv("USER_TOKEN")
app_token = os.getenv("APP_TOKEN")

# Define and configure logger
log_path = '/appdata/jobs.log'
logger = logging.getLogger(__name__)
logging.basicConfig(filename='jobs.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
file_handler = RotatingFileHandler(log_path, maxBytes=max_log_size, backupCount=backup_count)
file_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# Default URL is looking at US, remote only, full-time positions, filtered by most recent
url = f'https://gcsservices.careers.microsoft.com/search/api/v1/search?lc=United%20States&exp=Experienced%20professionals&et=Full-Time&ws=Up%20to%20100%25%20work%20from%20home&l=en_us&pg=1&pgSz=20&o=Recent'
headers = {
    'Accept': 'application/json, text/plain, */*'
}

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Send the GET request
response = requests.get(url, headers=headers, verify=False)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()

    # Access the list of jobs from the response
    all_jobs = data.get('operationResult', {}).get('result', {}).get('jobs', [])

    # Exclude the jobs that you don't want
    jobs = [job for job in all_jobs if not any(exclude in job.get('title', '') for exclude in exclude_titles)]

    # Get the total page size we will have to parse
    job_total = data.get('operationResult', {}).get('result', {}).get('totalJobs')
    total_pages = round(job_total / 20)
    print(f"total pages needed: {total_pages}")

    # Grab the Job IDs for follow up parsing of hr levels
    job_list=[]
    if jobs:
        for job in jobs:
            job_list.append(job.get('jobId'))
    else:
        print("No jobs found.")
    print(f"Total jobs found: {len(job_list)} on Page 1")
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")

# Check if multiple pages are required
if total_pages > 1:
    page=2
    while page <= total_pages:
        print(f"Scraping page {page}")
        # Grab the next page
        url = f'https://gcsservices.careers.microsoft.com/search/api/v1/search?lc=United%20States&exp=Experienced%20professionals&et=Full-Time&ws=Up%20to%20100%25%20work%20from%20home&l=en_us&pg={page}&pgSz=20&o=Recent'
        headers = {
            'Accept': 'application/json, text/plain, */*'
        }

        # Send the GET request
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Access the list of jobs from the response
            all_jobs = data.get('operationResult', {}).get('result', {}).get('jobs', [])

            # Exclude the jobs that you don't want
            jobs = [job for job in all_jobs if not any(exclude in job.get('title', '') for exclude in exclude_titles)]

            # Grab the Job IDs (or handle the data as needed)
            if jobs:
                for job in jobs:
                    job_list.append(job.get('jobId'))
            else:
                print("No jobs found.")
            print(f"Total jobs found: {len(job_list)} since page {page}")
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
        page += 1
print(f"Total jobs found: {len(job_list)}")

shorten_jobs={}
if job_list:
    for job in job_list:
        # Define the URL and headers
        url = f'https://gcsservices.careers.microsoft.com/search/api/v1/job/{job}?lang=en_us'
        headers = {
            'Accept': 'application/json, text/plain, */*'
        }

        # Send the GET request
        try:
            response = requests.get(url, headers=headers, verify=False)
        except Exception as e:
            print(e)
            continue

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Extract qualifications from the response
            qualifications = data.get('operationResult', {}).get('result', {}).get('qualifications', [])
            title = data.get('operationResult', {}).get('result', {}).get('title')
            # Print the qualifications
            for level in hr_levels:
                try:
                    if level in qualifications:
                        print(f"Job {job} meets {level} criteria!")
                        shorten_jobs[job]=title
                except ValueError:
                    print(f"Ran into qualifications issue for job {job}, skipping")
                    continue

        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")

if shorten_jobs:
    print(f"Jobs that meet hr level criteria: {len(shorten_jobs)}")
    with open(new_jobs_file, 'w') as file:
        for job,title in shorten_jobs.items():
        # Save the job paths to a file
            file.write(f"https://jobs.careers.microsoft.com/global/en/job/{job}, {title}\n")
    
    logger.info(f"jobs.new.txt file has been updated with a total of {len(shorten_jobs)} jobs!")

    # Read the contents of the files into sets
    with open(new_jobs_file, 'r') as f:
        new_jobs = set(f.read().splitlines())

    # Check if the old jobs file exists
    if not os.path.exists(jobs_file):
        # If it doesn't exist, create it by copying the new jobs file and "initialize" this script.
        with open(jobs_file, 'w') as f:
            f.write('\n'.join(sorted(new_jobs)))
        logger.info(f"{jobs_file} did not exist, so it was created with the contents of {new_jobs_file}.")
    else:     
        # If the old jobs file exists, read its contents into a set
        with open(jobs_file, 'r') as f:
            jobs = set(f.read().splitlines())

        # Check if the files match fully
        if new_jobs == jobs:
            logger.info("No new jobs!")
            # logger.info(f"Total jobs is {len(jobs)}")
        else:
            # Initiate an empty set to start capturing all the new jobs
            append_new_jobs=set()

            # Check for removed job listings, used only to notify in logs of it's removal.
            removed_jobs = jobs - new_jobs
            for job in removed_jobs:
                logger.info(f"Job listing removed! {job}")

            # Check for new job listings
            new_listings = new_jobs - jobs
            for job in new_listings:
                logger.warning(f"New job listing! {job}")
                # Send this to phone
                url = f"https://api.pushover.net/1/messages.json?token={app_token}&user={user_token}&message={job}&title=MSFT%20Job%20Alert!"

                response = requests.request("POST", url, verify=False)

                logger.info(response.text)
                append_new_jobs.add(job)
            
            # Update the old jobs file with the new jobs
            with open(jobs_file, 'a') as f:
                f.write('\n'.join(append_new_jobs) + '\n')