def create_slurm_script(job_name: str, output_file: str, error_file: str,
                        num_tasks: int, time_limit, num_cores: str,
                        account: str,  script_path: str):
    contents = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={output_file}
#SBATCH --error={error_file}
#SBATCH --ntasks={num_tasks}
#SBATCH --time={time_limit}
#SBATCH --cpus-per-task={num_cores}
#SBATCH --account {account}

# Command to execute Python script
python main.py
"""
    with open(script_path, 'w') as job_file:
        job_file.write(contents)
