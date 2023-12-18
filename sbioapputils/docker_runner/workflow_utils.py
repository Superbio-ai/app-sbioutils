import argparse
import os
import yaml
   

def get_workflow_loc(job_id: str, request: dict):
    ################# NEW LOCATION IN BE NEEDS TO BE DEFINED - NEED TO PULL FROM S3 ########################
    #use workflow.yml by default, or if app only has one. Name them in request if there are multiple options.
    if 'workflow' in request:
        workflow_name = request['workflow']
    else:
        workflow_name = "workflow.yml"
    workflow_loc = f'workflows/{job_id}/{workflow_name}' 
    return workflow_name, workflow_loc
        
        
def parse_workflow(job_id: str, request: dict):
    """Helper function to parse the workflow configuration."""
    #use workflow.yml by default, or if app only has one. Name them in request if there are multiple options.

    _, workflow_loc = get_workflow_loc(job_id, request)
    #testing     workflow_loc = 'D:/git/app-sbioutils/templates/workflow_docker.yml'
    with open(workflow_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
                
    vm_config = yaml_dict['vm_config']
    stages = {}
    errors = ''
    for stage, parameters in yaml_dict['stages'].items():
        cmd_list = [f"ssh -i {vm_config['key_file']} {vm_config['target_ip']}",
                        f"docker exec {vm_config['container_name']}",
                        f"python {parameters['script']}"]
        
        request_default = set_defaults(parameters, request)
        request_numeric = set_numeric(parameters, request_default)
        errors = validate_request(parameters, request_numeric, errors)
        
        for key, value in parameters.items():
            if key in request_numeric.keys():
                cmd_list.append("--" + key)
                cmd_list.append(str(value))
        stages[stage] = ' '.join(cmd_list)
    
    return stages, errors


def dir_path(string):
    """Function to check if the specified string is a directory."""
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def set_numeric(parameters, request):
    """Request from FE, and parameters from workflow yaml"""
    
    #set numeric where required
    for key, parameter in parameters.items():
        if key != 'script':
            if parameter['type'] == 'int':
                request[key] = int(request[key])
            elif parameter['type'] == 'float':
                request[key] = float(request[key])
        
    return(request)


def set_defaults(parameters, request):
    
    #set defaults where not present
    for key, parameter in parameters.items():
        if key != 'script':
            # Check if default is present
            if key not in request:
                request[key] = parameter['default']

            #convert 'None' to None
            if request[key] == 'None':
                request[key] = None
            #convert to numeric
            elif parameter['type']=='int':
                request[key] = int(request[key])
            elif parameter['type']=='float':
                request[key] = float(request[key])

    return request
            

def validate_request(parameters, request, errors = ""):
    """Validating request against workflow yaml"""
    
    wrong_data_types = []
    invalid_value = []

    for key, parameter in parameters.items():
        if key != 'script':
            # Check if type is present
            if parameter['type'] in ['int', 'float', 'str']:
                if (not isinstance(request[key], eval(parameter['type']))) and (request[key] != None):
                    wrong_data_types.append(key)

            if parameter.get('user_defined') == 'True':
                if parameter['type'] in ['int', 'float']:
                    # Check between min and max
                    if parameter.get('max_value'):
                        if float(request[key]) > float(parameter['max_value']):
                            invalid_value.append(key)
                    if parameter.get('min_value'):
                        if float(request[key]) < float(parameter['min_value']):
                            invalid_value.append(key)

                elif parameter['type'] == 'str':
                    if parameter.get('options'):
                        if request[key] not in parameter['options']:
                            invalid_value.append(key)
    
    if wrong_data_types:
        errors = errors + f"These parameters have an invalid data type: {wrong_data_types} \n"
        
    if invalid_value:
        errors = errors + f"These parameters have invalid values (out of specified range of allowed values): {invalid_value} \n"
        
    return errors


def remove_empty_keys(yaml_dict):

    #removing empty keys, as otherwise an error in FE
    remove=[]
    for key, results in yaml_dict.items():
        if key != 'download':
            contents=0
            for car_contents in results:
                contents+=len(car_contents)
        else:
            contents =len(results)
        if contents==0:
            remove.append(key)
    
    for key in remove:
        print(f"No {key} found, so removing from payload")
        del yaml_dict[key]
    
    return(yaml_dict)        