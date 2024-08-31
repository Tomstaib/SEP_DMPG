import requests

SLURM_USERNAME = "thoadelt"
SLURM_ACCOUNT = "l_mkt_wi_buscherm_proj"
SLURM_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjM0OTc5MjksImlhdCI6MTcyMzQ4NzkzMCwic3VuIjoidGhvYWRlbHQifQ.3afoWqIw046lTTLmf73FGoKFn3HDXCTbPVzhnMI0JFo"
JOB_NAME = "ComputeNode1"
base_url = "https://slurm.hpc.hs-osnabrueck.de/slurm/v0.0.39"
submit_url = f"{base_url}/job/submit"
headers = {
    "X-SLURM-USER-NAME": SLURM_USERNAME,
    "X-SLURM-USER-TOKEN": SLURM_JWT
}

job_data = {
    "job": {
        "name": JOB_NAME,
        "ntasks": 1,
        "time_limit": {"minutes": 10},
        "partition": "compute",
        "script": """#!/bin/bash
        
#SBATCH --job-name={JOB_NAME}
#SBATCH --output=output.log
#SBATCH --error=error.log
#SBATCH --cpus-per-task=16
#SBATCH --account={SLURM_ACCOUNT}
#SBATCH --export=ALL,JOB_NAME={JOB_NAME}

source /cluster/user/{SLURM_USERNAME}/venvs/DMPG/bin/activate

export PYTHONPATH=$PYTHONPATH:/home/{SLURM_USERNAME}/DMPG

python3 /home/{SLURM_USERNAME}/DMPG/src/models/main.py
python3_exit_code=$?

# Festlegen der Job-ID und des Exit-Codes
job_id=$SLURM_JOB_ID
exit_code=$python3_exit_code

# Determine the job status based on the exit code
if [ $exit_code -eq 0 ]; then
 status="SUCCESS"
else
 status="FAILURE"
fi

# Specify the output file
output_file="/home/{SLURM_USERNAME}/job_status_$job_id.txt"

# Write the Job ID and status to the file
echo "Job ID: $job_id" > $output_file
echo "Status: $status" >> $output_file
echo "Job name: {JOB_NAME}" >> $output_file

echo "Job $job_id is $status"
""".format(JOB_NAME=JOB_NAME, SLURM_ACCOUNT=SLURM_ACCOUNT, SLURM_USERNAME=SLURM_USERNAME),
        "environment":  [ "PATH=/bin/:/usr/bin/:/sbin/" ],
        "account": SLURM_ACCOUNT,
        "current_working_directory": f"/home/{SLURM_USERNAME}/DMPG/src"
    }
}


response = requests.post(submit_url, headers=headers, json=job_data)

if response.status_code == 200:
    job_id = response.json().get('job_id')
    print(f"Successfully submitted job. Job ID: {job_id}")
else:
    print(f"Failed to submit job. Status code: {response.status_code}")
    print(response.text)
