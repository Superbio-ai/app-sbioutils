import argparse
import os
import yaml
from pathlib import Path
import shutil


def parse_workflow(request):
    """Helper function to parse the workflow configuration."""
    workflow_loc = "app/workflow.yml"
    if request.get('workflow_name'):
        src_file = f"app/{request['workflow_name']}.yml"
        if (os.path.exists(workflow_loc)) and not (os.path.samefile(src_file, workflow_loc)):
            os.remove(workflow_loc)
        shutil.copy(src_file,workflow_loc)
        
    with open(workflow_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    stages = yaml_dict['stages']
    parameters = yaml_dict['parameters']
    
    return stages, parameters


def dir_path(string):
    """Function to check if the specified string is a directory."""
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def set_numeric(request, parameters):
    """Request from FE, and parameters from workflow yaml"""
    
    #set numeric where required
    for key in parameters.keys():
        if eval(parameters[key]['type'])==int:
            request[key] = int(request[key])
        elif eval(parameters[key]['type'])==float:
            request[key] = float(request[key])
        
    return(request)


def set_defaults(request, parameters, job_id):
    """Request from FE, and parameters from workflow yaml"""
    request['job_id'] = job_id
    
    #set defaults where not present
    for key in parameters.keys():
        # Check if default is present
        if key not in request:
            request[key] = parameters[key]['default']
        
    return(request)
            

def create_directories(request, parameters):
    """Request from FE, and parameters from workflow yaml"""
    
    #set defaults where not present
    for key in parameters.keys():
            
        # Create directory if Path type
        if (parameters[key]['type']==Path):
            print(f"{key} is path")
            if not os.path.exists(request[key]):
                os.mkdir(request[key])
        else:
            print(f"{key} is NOT a path")


def validate_request(request, parameters):
    """Validating request against workflow yaml"""
    
    wrong_data_types = []
    invalid_value = []

    for key in parameters.keys():
        
        # Check if type is present
        if not isinstance(request[key], eval(parameters[key]['type'])):
            if eval(parameters[key]['type'])==Path:
                if not request[key].startswith("/"):
                    wrong_data_types.append(key)
            else:
                wrong_data_types.append(key)

        if parameters[key].get('user_defined') == 'True':
            if parameters[key]['type'] in ['int', 'float']:
                # Check between min and max
                if parameters[key].get('max_value'):
                    if float(request[key]) > float(parameters[key]['max_value']):
                        invalid_value.append(key)
                if parameters[key].get('min_value'):
                    if float(request[key]) < float(parameters[key]['min_value']):
                        invalid_value.append(key)

            elif eval(parameters[key]['type']) == 'str':
                dropdown = not parameters[key].get('from_data') == 'True'
                # Category settings
                if dropdown:
                    if request[key] not in parameters[key]['options']:
                        invalid_value.append(key)
    output_errors = ""
    if wrong_data_types:
        output_errors = output_errors + f"These parameters have an invalid data type: {wrong_data_types} \n"
        
    if invalid_value:
        output_errors = output_errors + f"These parameters have invalid values (out of specified range of allowed values): {invalid_value} \n"
        
    return output_errors


def parse_arguments():
    # Load workflow configuration
    workflow_loc = "app/workflow.yml"
        
    with open(workflow_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    
    parameters = yaml_dict['parameters']

    # Create an argument parser
    parser = argparse.ArgumentParser(add_help=False, conflict_handler='resolve')

    # Loop over the parameters in the workflow configuration
    for key in parameters.keys():
        # If the parameter type is float, add a float argument to the parser
        if parameters[key]['type'] == 'float':
            parser.add_argument(f"--{key}", type=float)
        # If the parameter type is int, add an integer argument to the parser
        elif parameters[key]['type'] == 'int':
            parser.add_argument(f"--{key}", type=int)
        # Otherwise, add a string argument to the parser
        else:
            parser.add_argument(f"--{key}")
    
    #loop over input files as well
    for key in yaml_dict['input_settings']['upload_options']:
        parser.add_argument(f"--{key}", type=str)

    # Parse the arguments
    args, unknown = parser.parse_known_args()
    
    return args
