import logging
import subprocess
import traceback
import time
import sys
import json

from sbioapputils.app_runner_utils import AppRunnerUtils
from sbioapputils.workflow_utils import validate_config


def _process_stage(stage, stages, config):
    logging.info(f'Stage {stage} starting')
    start_time = time.time()
    sub_process_list = ['python', "app/" + stages[stage]['file']]
    for key, value in config.items():
        sub_process_list.append("--" + key)
        sub_process_list.append(str(value))
    process = subprocess.Popen(sub_process_list, stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line:
            break
        logging.info(line.rstrip())

    if process.returncode is not None:
        logging.error(f"Error occurred in subprocess {stage}")
        logging.error(process.returncode)
        raise Exception(f"Error occurred in subprocess {stage}, with code {process.returncode}")

    end_time = time.time()
    logging.info(f'Stage {stage} completed in {end_time - start_time} seconds')


def main():
    job_log_file = 'job.log'
    AppRunnerUtils.set_logging(job_log_file)
    job_id = sys.argv[1]
    try:
        request = AppRunnerUtils.get_job_config(job_id)
        config, workflow_name, stages, parameters = validate_config(request, job_id)
        logging.info(f'Job config: {config}')
        AppRunnerUtils.set_job_running(job_id)
        logging.info(f'Job {job_id} is running')
        for stage in stages.keys():
            _process_stage(stage, stages, config)

        # upload results
        with open('results_for_payload.json', 'r') as f:
            results_for_payload = json.load(f)
        AppRunnerUtils.upload_results(job_id, results_for_payload)

        # if any additional files/artifacts to be uploaded
        with open('results_for_upload.json', 'r') as f:
            results_for_upload = json.load(f)
        for element in results_for_upload:
            AppRunnerUtils.upload_file(job_id, element)
        AppRunnerUtils.set_job_completed(job_id, results_for_payload)

    except Exception as e:
        err = str(e)
        AppRunnerUtils.set_job_failed(job_id, err)
        logging.error(traceback.format_exc())
    finally:
        # upload log files to S3
        AppRunnerUtils.upload_file(job_id, job_log_file)


if __name__ == '__main__':
    main()