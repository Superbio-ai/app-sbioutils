import logging
import subprocess
import traceback
import time
import sys
import json
from sbioapputils.app_runner.app_runner_utils import AppRunnerUtils
from sbioapputils.app_runner.workflow_utils import parse_workflow, set_defaults, set_numeric, create_directories, validate_request


def _process_stage(stage_name, stage_value, config_subprocess_list):
    logging.info(f'Stage {stage_name} starting')
    start_time = time.time()
    sub_process_list = ['python', 'app/' + stage_value['file']] + config_subprocess_list
    process = subprocess.Popen(sub_process_list, stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line:
            break
        logging.info(line.rstrip())

    if process.returncode is not None:
        logging.error(f"Error occurred in subprocess {stage_name}")
        logging.error(process.returncode)
        raise Exception(f"Error occurred in subprocess {stage_name}, with code {process.returncode}")

    end_time = time.time()
    logging.info(f'Stage {stage_name} completed in {end_time - start_time} seconds')


def _upload_results(job_id: str):
    with open('results_for_payload.json', 'r') as f:
        results_for_payload = json.load(f)
    AppRunnerUtils.upload_results(job_id, results_for_payload)

    # if any additional files/artifacts to be uploaded
    with open('results_for_upload.json', 'r') as f:
        results_for_upload = json.load(f)
    for element in results_for_upload:
        AppRunnerUtils.upload_file(job_id, element)
    AppRunnerUtils.set_job_completed(job_id, results_for_payload)


def _get_config_subprocess_list(config: dict):
    config_subprocess_list = []
    for key, value in config.items():
        if not isinstance(value, dict):
            config_subprocess_list.append(f' --{key} {value}')
    for key, value in config['input_files'].items():
        config_subprocess_list.append(f' --{key} {value}')
    return config_subprocess_list


def main():
    job_log_file = 'job.log'
    AppRunnerUtils.set_logging(job_log_file)
    job_id = sys.argv[1]
    try:
        request = AppRunnerUtils.get_job_config(job_id)
        stages, parameters = parse_workflow(request)
        request = set_defaults(request, parameters, job_id)
        request = set_numeric(request, parameters)
        create_directories(request, parameters)
        logging.info('Workflow parsed')
        logging.info(f'Job config: {request}')
        
        output_errors = validate_request(request, parameters)
        if output_errors:
            raise Exception(f"Invalid json request:\n {output_errors}")
        
        AppRunnerUtils.set_job_running(job_id)
        logging.info(f'Job {job_id} is running')
        
        config_subprocess_list = _get_config_subprocess_list(request)
        for stage_name, stage_value in stages.items():
            _process_stage(stage_name, stage_value, config_subprocess_list)
        _upload_results(job_id)
        
    except Exception as e:
        err = str(e)
        AppRunnerUtils.set_job_failed(job_id, err)
        logging.error(traceback.format_exc())
        
    finally:
        # upload log files to S3
        AppRunnerUtils.upload_file(job_id, job_log_file)


if __name__ == '__main__':
    main()
