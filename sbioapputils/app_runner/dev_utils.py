import os
from os.path import exists
from pyflakes.api import isPythonFile, checkPath
from pyflakes.reporter import _makeDefaultReporter
import pycodestyle
import sys
from .yaml_utils import payload_from_yaml, get_yaml
import json


def _run_pycodestyle(filename):
    style_guide = pycodestyle.StyleGuide()
    sys.stdout = open(os.devnull, 'w')
    report = style_guide.check_files([filename])
    sys.stdout = sys.__stdout__
    errors = []
    for line_number, offset, code, text, doc in report._deferred_print:
        errors.append(f"Line : {line_number}. Error : {code}. {text}")
    return(errors)
            

def validate_yaml_stages(yaml_dict: dict, style_check = False):
    """Validating parameters from workflow yaml"""    
    valid_check = True
    invalid_stage = []
    invalid_path = []
    code_errors = []
    
    for key, stage in yaml_dict['stages'].items():
        
        #catch common yaml formating errors and check target is a python file
        for subkey in stage.keys():
            if ":" in subkey:
                invalid_stage.append({key : subkey})
                print(f"Stage {key} has an invalid file parameter formatting: check there is a space between all keys and values")
        if not isPythonFile('/app' + stage['file']):
            invalid_path.append(key)
            print(f"Stage {key} has an invalid path")
    
        #checking for code errors in scripts
        defaultReporter = _makeDefaultReporter()
        error_flag = checkPath('/app' + stage['file'], reporter = defaultReporter)
        if error_flag:
            code_errors.append(stage)
    
    if invalid_stage:
        valid_check = False
        print(f"These parameters are not formatted correctly in yaml: {invalid_stage}. Please ensure no ':' values are included in keys and there is space between keys and values")
    if invalid_path:
        valid_check = False
        print(f"These files do not appear to be python scripts: {invalid_path}.")
    if code_errors:
        valid_check = False
        print(f"Errors were found in these scripts: {code_errors}. Please check the printed messages to identify the errors")
    
    if style_check:
        for key, stage in yaml_dict['stages'].items():
            style_errors = _run_pycodestyle('/app' + stage['file'])
            if style_errors:
                print(f"Style errors with file {key}:")
                print(style_errors)
            
    return valid_check
            
            
def validate_yaml_parameters(yaml_dict: dict):
    """Validating parameters from workflow yaml"""
    # Check all required parameters are provided
    
    parameters = yaml_dict['parameters']
    valid_check = True
    no_default = []
    no_type = []
    bad_formating = []
    
    for key, parameter in parameters.items():

        # Check if default is present
        if 'default' not in parameter:
            no_default.append(key)

        # Check if type is present
        if not parameter.get('type'):
            no_type.append(key)
        
        #catch common yaml formating errors
        for subkey in parameter.keys():
            if ":" in subkey:
                bad_formating.append({key : subkey})
            elif ('default' in parameter) and (parameter.get('type')):
                if (parameter['type']=='path') and (parameter['default'][-1]!='/'):
                    bad_formating.append({key : subkey})
                    
    if no_type:
        valid_check = False
        print('Some parameters do not have their datatype specified: {}'.format(no_type))
        
    if no_default:
        valid_check = False
        print(f"These parameters do not have a default specified: {no_default}")
    
    if bad_formating:
        valid_check = False
        print(f"These parameters are not formatted correctly in yaml: {bad_formating}. Please ensure no ':' values are included in keys and there is space between keys and values. Also ensure that paths end with '/'")
        
    return valid_check
    
    
def run_pre_demo_steps(workflow_filename: str):
    workflow_loc = '/app/' + workflow_filename
    print(f"Expected workflow location: {workflow_loc}")
    yaml_dict = get_yaml(workflow_loc)
    
    print("Validating yaml stages")
    valid_check = validate_yaml_stages(yaml_dict, style_check = True)
    if valid_check:
        print("Stages have passed non-style checks")
    else:
        raise Exception("yaml stage checks failed. See errors above")
    
    print("Validating yaml parameters")
    valid_check = validate_yaml_parameters(yaml_dict)
    if valid_check:
        print("Parameters have passed checks")
    else:
        raise Exception("Yaml stage checks failed")
    
    if "JOB_CONFIG" in os.environ:
        print("Generating configuration dictionary from JOB_CONFIG")
        request =  eval(os.environ.get("JOB_CONFIG"))
        request['job_id'] = os.environ.get("JOB_ID")
    else:
        print("Generating configuration dictionary from defaults specified in yaml")
        request = {'job_id':'test'}
        
    #set defaults where not present
    for key, parameter in yaml_dict['parameters'].items():
        # Check if default is present
        if key not in request:
            try:    
                request[key] = parameter['default']
            except:
                print(f"Default not set for parameter {key}. Will this cause issues?")
        elif parameter['type']=='int':
            request[key] = int(request[key])
        elif parameter['type']=='float':
            request[key] = float(request[key])
    
    #set input files to the demo files
    request['input_files']={}
    if yaml_dict['input_settings']:
        for key in yaml_dict['input_settings']:
            try:
                request['input_files'][key] = yaml_dict['input_settings'][key]['demo_path']
            except:
                print(f"Demo path not set for input input_setting {key}. Will this cause issues?")
    else:
        print("No input data settings detected. Is this correct?")

    request['workflow_name'] = workflow_filename.split('.')[0]
    
    return(request, yaml_dict['stages'], yaml_dict['parameters'])


def run_post_demo_steps(request: dict, workflow_filename: str, payload_loc: str = '/app/results_for_payload.json', additional_artifacts_loc: str = '/app/results_for_upload.json'):
    workflow_loc = '/app/' + workflow_filename
    yaml_dict = get_yaml(workflow_loc)
    
    if exists(payload_loc) and exists(additional_artifacts_loc):
        print("Generating payload from custom json")
        with open('/app/results_for_payload.json', 'r') as f:
            results_for_payload = json.load(f)
        with open('/app/results_for_upload.json', 'r') as f:
            results_for_upload = json.load(f)
    
    else:
        print("Generating output payload from yaml (custom json not found)")
        results_for_payload, results_for_upload = payload_from_yaml(workflow_loc)
    print(results_for_payload)
    print("Additional artifacts for upload:")
    print(results_for_upload)
    
    # printing folder contents to aid in showing locations of outputs
    parameters = yaml_dict['parameters']
    for key in parameters.keys():
        if (parameters[key]['type']=='path'):
            print(f'Contents of {key} directory after processing, with location {request[key]}:')
            print(os.listdir(request[key]))
            