import requests

SLURM_USERNAME = "fegladen"
SLURM_ACCOUNT = "l_mkt_wi_buscherm_proj"
SLURM_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjMyMDY5NDgsImlhdCI6MTcyMzE5Njk0OSwic3VuIjoiZmVnbGFkZW4ifQ.70UsHoJc13j45xlB5hmaTX3YN9DzbfUCJ6O5a4j-MxE"

base_url = "https://slurm.hpc.hs-osnabrueck.de/slurm/v0.0.39"
submit_url = f"{base_url}/job/submit"
headers = {
    "X-SLURM-USER-NAME": SLURM_USERNAME,
    "X-SLURM-USER-TOKEN": SLURM_JWT
}

job_data = {
    "job": {
        "name": "rest_test_job",
        "ntasks": 1,
        "time_limit": {"minutes": 10},
        "partition": "compute",
        "script": "#!/bin/bash\nhostname",
        "environment":  [ "PATH=/bin/:/usr/bin/:/sbin/" ],
        "account": SLURM_ACCOUNT,
        "current_working_directory": f"/cluster/user/{SLURM_USERNAME}"
    }
}

response = requests.post(submit_url, headers=headers, json=job_data)

if response.status_code == 200:
    job_id = response.json().get('job_id')
    print(f"Successfully submitted job. Job ID: {job_id}")
else:
    print(f"Failed to submit job. Status code: {response.status_code}")
    print(response.text)