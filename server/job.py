import requests


def submit_slurm_job(slurm_username, slurm_account, slurm_jwt, job_name, base_url, model_script, replications,
                     time_limit_minutes=10, partition="compute", cpus_per_task=4):
    """
    Sendet einen SLURM-Job zur Ausführung auf dem Cluster.

    :param slurm_username: Der Benutzername für SLURM
    :param slurm_account: Das SLURM-Konto
    :param slurm_jwt: Das JWT-Token für die Authentifizierung
    :param job_name: Der Name des Jobs
    :param base_url: Die Basis-URL der SLURM-API
    :param model_script: Das Python-Skript, das als Modell verwendet wird (z.B. main.py wird durch das Modell ersetzt)
    :param replications: Die Anzahl der Replikationen, die an das Modell übergeben werden
    :param time_limit_minutes: Zeitlimit des Jobs in Minuten (Standard: 10)
    :param partition: Die Partition, auf der der Job ausgeführt wird (Standard: "compute")
    :param cpus_per_task: Anzahl der CPUs pro Aufgabe (Standard: 4)
    :return: Die Job-ID bei erfolgreicher Einreichung oder die Fehlermeldung
    """

    submit_url = f"{base_url}/job/submit"

    headers = {
        "X-SLURM-USER-NAME": slurm_username,
        "X-SLURM-USER-TOKEN": slurm_jwt
    }

    # Definiere die Job-Daten mit der SLURM-Syntax
    job_data = {
        "job": {
            "name": job_name,
            "ntasks": 1,
            "cpus_per_task": 4,
            "time_limit": {"minutes": time_limit_minutes},
            "partition": partition,
            "script": """#!/bin/bash

#SBATCH --job-name={JOB_NAME}
#SBATCH --output=output.log
#SBATCH --error=error.log
#SBATCH --cpus-per-task={CPUS_PER_TASK}
#SBATCH --account={SLURM_ACCOUNT}
#SBATCH --export=ALL,JOB_NAME={JOB_NAME},REPLICATIONS={REPLICATIONS},TIME_LIMIT={TIME_LIMIT}

output_file="/home/{SLURM_USERNAME}/job_status_$job_id.txt"

echo "Job ID: $job_id" > $output_file
echo "Status: $status" >> $output_file
echo "Job name: {JOB_NAME}" >> $output_file
echo "SLURM Username: {SLURM_USERNAME}" 
echo "SLURM Account: {SLURM_ACCOUNT}" 
echo "Job name: {JOB_NAME}" 
echo "Replications: {REPLICATIONS}"
echo "Time Limit (minutes): {TIME_LIMIT}"
echo "CPUs per Task: {CPUS_PER_TASK}" 
echo "Model Script: {MODEL_SCRIPT}" 

echo "Job $job_id is $status"

source /cluster/user/{SLURM_USERNAME}/venvs/DMPG/bin/activate

export PYTHONPATH=$PYTHONPATH:/home/{SLURM_USERNAME}/DMPG/

python3 /home/{SLURM_USERNAME}/DMPG/src/models/model_builder.py --replications {REPLICATIONS} --config_path {MODEL_SCRIPT}
python3_exit_code=$?

job_id=$SLURM_JOB_ID
exit_code=$python3_exit_code

if [ $exit_code -eq 0 ]; then
 status="SUCCESS"
else
 status="FAILURE"
fi


""".format(JOB_NAME=job_name, SLURM_ACCOUNT=slurm_account, SLURM_USERNAME=slurm_username, CPUS_PER_TASK=cpus_per_task,
           MODEL_SCRIPT=model_script, REPLICATIONS=replications, TIME_LIMIT=time_limit_minutes
           ),
            "environment": ["PATH=/bin/:/usr/bin/:/sbin/"],
            "account": slurm_account,
            "current_working_directory": f"/home/{slurm_username}/DMPG/src"
        }
    }

    try:
        # Sende den POST-Request zum Einreichen des Jobs
        response = requests.post(submit_url, headers=headers, json=job_data)

        # Wenn erfolgreich, gib die Job-ID zurück
        if response.status_code == 200:
            job_id = response.json().get('job_id')
            return f"Successfully submitted job. Job ID: {job_id}"
        else:
            # Im Fehlerfall Statuscode und Antworttext zurückgeben
            return f"Failed to submit job. Status code: {response.status_code}\n{response.text}"

    except requests.RequestException as e:
        return f"Request failed: {str(e)}"

