import argparse
import os
import warnings
import yaml


def _parse_workflow(request):
    """Helper function to parse the workflow configuration."""
    if request.get('workflow_name'):
        workflow_loc = f"app/{request['workflow_name']}.yml"
    else:
        workflow_loc = "app/workflow.yml"
        
    with open(workflow_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    name = yaml_dict['name']
    stages = yaml_dict['stages']
    parameters = yaml_dict['parameters']
    return name, stages, parameters


def dir_path(string):
    """Function to check if the specified string is a directory."""
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def validate_config(request, job_id):
    """Function to validate the request config."""
    name, stages, parameters = _parse_workflow(request)
    for key, value in request['input_files'].items():
        request[key] = value
    request['job_id'] = job_id

    # Check all required parameters are provided
    no_default = []
    default = {}
    no_type = []
    wrong_data_types = []
    invalid_value = []

    for key, parameter_value in parameters.items():
        request_value = request[key]

        # Check if type is present
        if not parameter_value.get('type'):
            no_type.append(key)
        else:
            # Check if type is correct
            try:
                if not isinstance(request_value, parameter_value['type']):
                    wrong_data_types.append(key)
            # On error if config[key] not present
            except KeyError:
                pass

        # Check if default is present
        if not parameter_value.get('default'):
            no_default.append(key)
        else:
            default[key] = parameter_value['default']
            # Set defaults if not present
            if not request.get(key):
                request_value = parameter_value['default']

        if parameter_value.get('user_defined'):
            if parameter_value['user_defined'] == 'True':
                if parameter_value['type'] in ['int', 'float']:
                    # Check between min and max
                    if parameter_value.get('max_value'):
                        if request_value > parameter_value['max_value']:
                            invalid_value.append(key)
                    if parameter_value.get('min_value'):
                        if request_value < parameter_value['min_value']:
                            invalid_value.append(key)

                elif parameter_value['type'] == 'str':
                    if parameter_value.get('from_data'):
                        if parameter_value['from_data'] == 'True':
                            dropdown = False
                        else:
                            dropdown = True
                    else:
                        dropdown = True

                    # Category settings
                    if dropdown:
                        if request_value not in parameter_value['options']:
                            invalid_value.append(key)

        # Create directory if needed
        try:
            if str(request_value)[-1] == '/':
                if not os.path.exists(request_value):
                    os.mkdir(request_value)
                    #print("Directory '% s' created" % request_value)
        except KeyError:
            pass

    if not all(param in request.keys() for param in no_default):
        raise Exception(f"These required parameters are not specified: {no_default}")

    if not all(param in request.keys() for param in no_type):
        raise Exception(f"These parameters have an incorrect data type: {wrong_data_types}")

    if no_type:
        warnings.warn('Some parameters do not have their datatype specified: {}'.format(no_type))

    if invalid_value:
        raise Exception(f"These parameters have invalid values (out of specified range of allowed values): {invalid_value}")
        
    return request, name, stages, parameters


def parse_arguments():
    # Load workflow configuration
    name, stages, parameters = _parse_workflow()

    # Create an argument parser
    parser = argparse.ArgumentParser(add_help=False, conflict_handler='resolve')

    # Loop over the parameters in the workflow configuration
    for key, parameter_value in parameters.items():
        # If the parameter type is float, add a float argument to the parser
        if parameter_value['type'] == 'float':
            parser.add_argument(f"--{key}", type=float)
        # If the parameter type is int, add an integer argument to the parser
        elif parameter_value['type'] == 'int':
            parser.add_argument(f"--{key}", type=int)
        # Otherwise, add a string argument to the parser
        else:
            parser.add_argument(f"--{key}")

    # Parse the arguments
    args, unknown = parser.parse_known_args()

    return(args)