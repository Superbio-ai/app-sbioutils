import subprocess
import time
import sys
import json
from sbioapputils.app_runner.workflow_utils import create_directories, validate_request, parse_workflow
from sbioapputils.app_runner.app_runner_utils import AppRunnerUtils

#for demo / testing purposes:
from sbioapputils.app_runner.dev_utils import run_pre_demo_steps, run_post_demo_steps


def _process_stage(stage_name, stage_value, config):
    print(f'Stage {stage_name} starting')
    start_time = time.time()
    sub_process_list = ['python', 'app/' + stage_value['file']]
    for key, value in config.items():
        sub_process_list.append("--" + key)
        sub_process_list.append(str(value))
    for key, value in config['input_files'].items():
        sub_process_list.append("--" + key)
        sub_process_list.append(str(value))
    process = subprocess.Popen(sub_process_list, stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(line.rstrip())

    if process.returncode is not None:
        print(f"Error occurred in subprocess {stage_name}")
        print(process.returncode)
        raise Exception(f"Error occurred in subprocess {stage_name}, with code {process.returncode}")

    end_time = time.time()
    print(f'Stage {stage_name} completed in {end_time - start_time} seconds')


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

        
def main():
    workflow_filename = sys.argv[1]
    
    try:
        #demo code
        request, stages, parameters =  run_pre_demo_steps(workflow_filename)
        _, _ = parse_workflow(request)
        print(f'Demo config has been parsed: {request}')
        
        create_directories(request, parameters)        
        print('Directories Created')
        
        output_errors = validate_request(request, parameters)
        if output_errors:
            raise Exception(f"Invalid json request:\n {output_errors}")
        print('Job is running')
        
        for stage_name, stage_value in stages.items():
            _process_stage(stage_name, stage_value, request)
            
        run_post_demo_steps(workflow_filename)
        
    except Exception as e:
        err = str(e)
        print(f"Demo job ended with exception {err}")
        

if __name__ == '__main__':
    main()
