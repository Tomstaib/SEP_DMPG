from typing import Any
import requests
from requests import Response


def submit_slurm_job(slurm_username: str, slurm_account: str, slurm_jwt: str,
                     job_name: str, base_url: str, model_script: str, replications: int,
                     time_limit_minutes: int = 10, partition: str = "compute", cpus_per_task: int = 4):
    """
    Sends a slurm job to Slurm for computation via REST-API

    :param slurm_username: The Slurm username.
    :param slurm_account: The Slurm account.
    :param slurm_jwt: The JWT token for authentication.
    :param job_name: The name of the job (of the ComputeNode).
    :param base_url: The base URL of the Slurm REST API.
    :param model_script: The path to the model script.
    :param replications: The number of replications to pass to the model.
    :param time_limit_minutes: The time limit of the job in minutes. Defaults to 10.
    :param partition: The partition where the job will run. Defaults to "compute".
    :param cpus_per_task: Number of CPUs per task. Defaults to 4.

    :return: A message indicating success with the job ID or an error message.
    """

    submit_url: str = f"{base_url}/job/submit"

    headers: dict[str, Any] = {
        "X-SLURM-USER-NAME": slurm_username,
        "X-SLURM-USER-TOKEN": slurm_jwt
    }

    current_working_directory = f"/home/{slurm_username}/DMPG/src"

    job_data: dict[str, Any] = prepare_job_data(job_name=job_name, slurm_account=slurm_account,
                                                slurm_username=slurm_username, cpus_per_task=cpus_per_task,
                                                model_script=model_script, replications=replications,
                                                time_limit_minutes=time_limit_minutes, partition=partition,
                                                current_working_directory=current_working_directory, )

    try:
        response: Response = requests.post(submit_url, headers=headers, json=job_data)

        if response.status_code == 200:
            job_id = response.json().get('job_id')
            return f"Successfully submitted job. Job ID: {job_id}"
        else:
            return f"Failed to submit job. Status code: {response.status_code}\n{response.text}"

    except requests.RequestException as e:
        return f"Request failed: {str(e)}"


def prepare_job_data(job_name: str, slurm_account: str, slurm_username: str, cpus_per_task: int,
                     model_script: str, replications: int, time_limit_minutes: int, partition: str,
                     current_working_directory: str) -> dict[str, Any]:
    """
    Prepare the job data for the Slurm REST API.

    :param job_name: The name of the job.
    :param slurm_account: The Slurm account.
    :param slurm_username: The Slurm username.
    :param cpus_per_task: Number of CPUs per task.
    :param model_script: The path to the model script.
    :param replications: The number of replications.
    :param time_limit_minutes: The time limit of the job in minutes.
    :param partition: The partition where the job will run.
    :param current_working_directory: The working directory for the job.

    :return: The job data dictionary.
    """
    script: str = generate_job_script(job_name=job_name, slurm_account=slurm_account, slurm_username=slurm_username,
                                      cpus_per_task=cpus_per_task, model_script=model_script, replications=replications,
                                      time_limit_minutes=time_limit_minutes)

    job_data: dict[str, dict[str, list[str] | str | dict[str, int] | int]] = {
        "job": {
            "name": job_name,
            "ntasks": 1,
            "cpus_per_task": cpus_per_task,
            "time_limit": {"minutes": time_limit_minutes},
            "partition": partition,
            "script": script,
            "environment": ["PATH=/bin/:/usr/bin/:/sbin/"],
            "account": slurm_account,
            "current_working_directory": current_working_directory,
        }
    }

    return job_data


def generate_job_script(job_name: str, slurm_account: str, slurm_username: str, cpus_per_task: int,
                        model_script: str, replications: int, time_limit_minutes: int) -> str:
    """
    Generate the Slurm job script.

    :param job_name: The name of the job.
    :param slurm_account: The Slurm account.
    :param slurm_username: The Slurm username.
    :param cpus_per_task: Number of CPUs per task.
    :param model_script: The path to the model script.
    :param replications: The number of replications.
    :param time_limit_minutes: The time limit of the job in minutes.

    :return: The job script as a string.
    """
    script: str = f"""#!/bin/bash

#SBATCH --job-name={job_name}
#SBATCH --output=output.log
#SBATCH --error=error.log
#SBATCH --cpus-per-task={cpus_per_task}
#SBATCH --account={slurm_account}
#SBATCH --export=ALL,JOB_NAME={job_name},REPLICATIONS={replications},TIME_LIMIT={time_limit_minutes}

job_id=$SLURM_JOB_ID
status="PENDING"

output_file="/home/{slurm_username}/job_status_$job_id.txt"

echo "Job ID: $job_id" > $output_file
echo "Status: $status" >> $output_file
echo "Job name: {job_name}" >> $output_file
echo "SLURM Username: {slurm_username}" >> $output_file
echo "SLURM Account: {slurm_account}" >> $output_file
echo "Replications: {replications}" >> $output_file
echo "Time Limit (minutes): {time_limit_minutes}" >> $output_file
echo "CPUs per Task: {cpus_per_task}" >> $output_file
echo "Model Script: {model_script}" >> $output_file

source /cluster/user/{slurm_username}/venvs/DMPG/bin/activate

export PYTHONPATH=$PYTHONPATH:/home/{slurm_username}/DMPG/

python3 /home/{slurm_username}/DMPG/src/models/model_builder.py --replications {replications} --config_path {model_script}
python3_exit_code=$?

exit_code=$python3_exit_code

if [ $exit_code -eq 0 ]; then
    status="SUCCESS"
else
    status="FAILURE"
fi

echo "Job $job_id is $status" >> $output_file

exit $exit_code
"""

    return script
