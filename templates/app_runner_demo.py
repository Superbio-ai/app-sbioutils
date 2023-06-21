import subprocess
import time
import sys
from sbioapputils.app_runner.workflow_utils import create_directories, validate_request, parse_workflow

#for demo / testing purposes:
from sbioapputils.app_runner.dev_utils import run_pre_demo_steps, run_post_demo_steps
import os


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

        
def _set_environ():
    with open("/app/.env") as file:
        for item in file:
            items = item.split('=')
            if len(items)==2:
                os.environ[items[0]] = items[1].strip('\n')
                
                
def main():
    workflow_filename = sys.argv[1]
    _set_environ()
    try:
        #demo code
        print(f"Workflow filename: {workflow_filename}")
        request, stages, parameters =  run_pre_demo_steps(workflow_filename)
        print(f"Workflow name: {request['workflow_name']}")
        _, _ = parse_workflow(request)
        request['workflow_filename'] = workflow_filename
        print(f'Demo config has been parsed: {request}')
        
        create_directories(request, parameters)        
        print('Directories Created')
        
        output_errors = validate_request(request, parameters)
        if output_errors:
            raise Exception(f"Invalid json request:\n {output_errors}")
        print('Job is running')
        
        for stage_name, stage_value in stages.items():
            _process_stage(stage_name, stage_value, request)
            
        run_post_demo_steps(request, workflow_filename)
        
    except Exception as e:
        err = str(e)
        print(f"Demo job ended with exception {err}")
        

if __name__ == '__main__':
    main()
