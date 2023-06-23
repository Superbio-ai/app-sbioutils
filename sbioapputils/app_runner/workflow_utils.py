import argparse
import os
import yaml
import shutil


def parse_workflow(request):
    """Helper function to parse the workflow configuration."""
    workflow_loc = "app/workflow.yml"
    if request.get('workflow_name'):
        src_file = f"app/{request['workflow_name']}.yml"
        if src_file!=workflow_loc:
            shutil.copy(src_file,workflow_loc)
            print(f"Workflow moved from app/{request['workflow_name']}.yml to app/workflow.yml")
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
    for key, parameter in parameters.items():
        if parameter['type'] == 'int':
            request[key] = int(request[key])
        elif parameter['type'] == 'float':
            request[key] = float(request[key])
        
    return(request)


def set_defaults(request, parameters, job_id):
    """Request from FE, and parameters from workflow yaml"""
    request['job_id'] = job_id
    
    #set defaults where not present
    for key, parameter in parameters.items():
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
    
    return(request)
            

def create_directories(request, parameters):
    """Request from FE, and parameters from workflow yaml"""
    
    #set defaults where not present
    for key, parameter in parameters.items():
            
        # Create directory if Path type
        if (parameter['type']=='path'):
            request[key] = request[key].replace("//","/")
            if not os.path.exists(request[key]):
                os.mkdir(request[key])
    return(request)
        

def validate_request(request, parameters):
    """Validating request against workflow yaml"""
    
    wrong_data_types = []
    invalid_value = []

    for key, parameter in parameters.items():
        
        # Check if type is present
        if parameter['type'] in ['int', 'float', 'str']:
            if (not isinstance(request[key], eval(parameter['type']))) and (request[key] != None):
                wrong_data_types.append(key)
        if parameter['type']=='path':
            if not request[key].startswith("/"):
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
                dropdown = not parameter.get('from_data') == 'True'
                # Category settings
                if dropdown:
                    if request[key] not in parameter['options']:
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

    parameters['workflow_name'] = {'default':'workflow.yml', 'type':'str'}
    
    # Loop over the parameters in the workflow configuration
    for key, parameter in parameters.items():
        # If the parameter type is float, add a float argument to the parser
        if parameter['type'] == 'float':
            parser.add_argument(f"--{key}", type=float)
        # If the parameter type is int, add an integer argument to the parser
        elif parameter['type'] == 'int':
            parser.add_argument(f"--{key}", type=int)
        # Otherwise, add a string argument to the parser
        else:
            parser.add_argument(f"--{key}")
    
    #loop over input files as well
    for key in yaml_dict['input_settings']:
        parser.add_argument(f"--{key}", type=str)

    # Parse the arguments
    args, unknown = parser.parse_known_args()
    
    return args


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