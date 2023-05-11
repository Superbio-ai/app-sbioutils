import argparse
import os
import warnings
import yaml


def _parse_workflow():
    """Helper function to parse the workflow configuration."""
    with open("app/workflow.yml", "r") as stream:
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
    name, stages, parameters = _parse_workflow()
    for key, value in request['input_files'].items():
        request[key] = value
    request['job_id'] = job_id

    # Check all required parameters are provided
    no_default = []
    default = {}
    no_type = []
    wrong_data_types = []
    invalid_value = []

    for key in parameters.keys():

        # Check if type is present
        if not parameters[key].get('type'):
            no_type.append(key)
        else:
            # Check if type is correct
            try:
                if not isinstance(request[key], parameters[key]['type']):
                    wrong_data_types.append(key)
            # On error if config[key] not present
            except KeyError:
                pass

        # Check if default is present
        if not parameters[key].get('default'):
            no_default.append(key)
        else:
            default[key] = parameters[key]['default']
            # Set defaults if not present
            if not request.get(key):
                request[key] = parameters[key]['default']

        if parameters[key].get('user_defined'):
            if parameters[key]['user_defined'] == 'True':
                if parameters[key]['type'] in ['int', 'float']:
                    # Check between min and max
                    if parameters[key].get('max_value'):
                        if (request[key] > parameters[key]['max_value']):
                            invalid_value.append(key)
                    if parameters[key].get('min_value'):
                        if (request[key] < parameters[key]['min_value']):
                            invalid_value.append(key)

                elif parameters[key]['type'] == 'str':
                    if parameters[key].get('from_data'):
                        if parameters[key]['from_data'] == 'True':
                            dropdown = False
                        else:
                            dropdown = True
                    else:
                        dropdown = True

                    # Category settings
                    if dropdown:
                        if request[key] not in parameters[key]['options']:
                            invalid_value.append(key)

        # Create directory if needed
        try:
            if str(request[key])[-1] == '/':
                if not os.path.exists(request[key]):
                    os.mkdir(request[key])
                    #print("Directory '% s' created" % request[key])
        except KeyError:
            pass

    if not all(param in request.keys() for param in no_default):
        raise Exception(f"These required parameters are not specified: {no_default}")

    if not all(param in request.keys() for param in no_type):
        raise Exception(f"These parameters have an incorrect data type: {wrong_data_types}")

    if no_type:
        warnings.warn('Some parameters do not have their datatype specified: {}'.format(no_type))

    if invalid_value > 0:
        raise Exception(f"These parameters have invalid values (out of specified range of allowed values): {invalid_value}")
        
    return request, name, stages, parameters


def parse_arguments():
    # Load workflow configuration
    name, stages, parameters = _parse_workflow()

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

    # Parse the arguments
    args, unknown = parser.parse_known_args()

    return(args)