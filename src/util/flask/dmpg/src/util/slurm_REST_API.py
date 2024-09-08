import requests

SLURM_USERNAME = "fegladen"
SLURM_ACCOUNT = "l_mkt_wi_buscherm_proj"
SLURM_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjM0ODgxODMsImlhdCI6MTcyMzQ3ODE4NCwic3VuIjoiZmVnbGFkZW4ifQ.Ut3bBSiLMGK27hYODNc4lkfj6I6Z3LH5T6a5jBMVlek"
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


# Ausführen des Python-Skripts
python3 /home/fegladen/src/SEP/test.py
python3_exit_code=$?
job_name=$SLURM_JOB_NAME
# Festlegen der Job-ID und des Exit-Codes
job_id=$SLURM_JOB_ID
exit_code=$python3_exit_code
echo "name: $SLURM_JOB_NAME"

# Bestimmen des Job-Status basierend auf dem Exit-Code
if [ $exit_code -eq 0 ]; then
    status="SUCCESS"
else
    status="FAILURE"
fi



# Festlegen der Ausgabedatei
output_file="/home/fegladen/src/SEP/$job_id.txt"

# Schreiben der Job-ID und des Status in die Datei
echo "Job Name: $SLURM_JOB_NAME" > $output_file
echo "Job ID: $job_id" >> $output_file
echo "Status: $status" >> $output_file

echo "Job $job_id is $status"
""",
        "environment":  [ "/cluster/user/$USER/venvs/DMPG/" ],
        "account": SLURM_ACCOUNT,
        "current_working_directory": f"/home/fegladen/src/SEP",
    }
}

response = requests.post(submit_url, headers=headers, json=job_data)

if response.status_code == 200:
    job_id = response.json().get('job_id')
    print(f"Successfully submitted job. Job ID: {job_id}")
else:
    print(f"Failed to submit job. Status code: {response.status_code}")
    print(response.text)