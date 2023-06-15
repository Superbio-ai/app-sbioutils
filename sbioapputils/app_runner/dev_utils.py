import yaml
import os
import json
from .templates import csv_template, image_template, sc_template, default_template
from pyflakes.api import isPythonFile, checkPath
from pyflakes.reporter import _makeDefaultReporter
import pycodestyle
import sys


def get_yaml(workflow_loc):
    """Helper function to parse the workflow configuration."""    
    with open(workflow_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    return yaml_dict


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
    
    
def _define_files_from_yaml(yaml_dict):
    
    input_files = []
    if yaml_dict.get('input_settings'):
        for key, input_values in yaml_dict['input_settings'].items():
            if input_values['type'] == 'table':
                input_element = csv_template.copy()
            elif input_values['type'] == 'image':
                input_element = image_template.copy()
            elif input_values['type'] == 'single_cell':
                input_element = sc_template.copy()
            else:
                print("No template is available for this data modality. Some parts of the uploadOptions configuration may need to be specified manually")
                input_element = default_template.copy()
                if input_values.get('data_structure'):
                    input_element['dataStructure'] = input_values['data_structure']
                if input_values.get('file_extensions'):
                    input_element['allowedFormats']['fileExtensions'] = input_values['file_extensions']
                    strout = ' or '.join(map(str, input_values['file_extensions']))
                    input_element['allowedFormats']['title'] = strout

            input_element['name'] = key
            input_element['title'] = input_values['title']
            if input_values.get('demo_path'):
                input_element['demoDataDetails'] = {
                    'description':input_values['demo_description'],
                    'filePath':input_values['demo_path'],
                    'fileName':input_values['demo_path'].split('/')[-1],
                    'fileSource':[{                        'title': 'Data Source',                        'url':input_values['url']}]
                    }
            input_files.append(input_element)
    return input_files
 

def _define_from_numeric(para_dict, key, input_parameters):
    
    if para_dict['type'] == 'int':
        input_type = 'integer'
    else:
        input_type = 'float'
    input_parameters.append({
        "name": key,
        "title": para_dict['title'],
        "tooltip": para_dict['tooltip'],
        "type": input_type,
        "default_value": para_dict['default'],
        "input_type": "slider",
        "increment": para_dict['increment'],
        "max_value": para_dict['max_value'],
        "max_value_included": True,
        "min_value": para_dict['min_value'],
        "min_value_inclusive": True
    })
    return(input_parameters)
    

def _define_from_string(para_dict, key, input_parameters, inputs_require_files):
    
    if para_dict.get('from_data'):
        if para_dict['from_data'] == 'True':
            # Create data-defined settings
            input_parameters.append({
                "name": key,
                "title": para_dict['title'],
                "tooltip": para_dict['tooltip'],
                "type": 'str',
                "default_value":{'label': para_dict['default'],'value': para_dict['default']},
                "input_type": "dropdown",
                "options": []
            })
            inputs_require_files.append(key)
            dropdown = False
        else:
            dropdown = True
    else:
        dropdown = True
            
    # Category settings
    if dropdown:
        option_list = []
        for option in para_dict['options']:
            option_list.append({"label": option, "value": option})
        input_parameters.append({
            "name": key,
            "title": para_dict['title'],
            "tooltip": para_dict['tooltip'],
            "type": 'str',
            "default_value":{'label': para_dict['default'],'value': para_dict['default']},
            "input_type": "dropdown",
            "options": option_list
        })
    return(input_parameters, inputs_require_files)
    

def define_settings_from_yaml(yaml_dict, workflow_filename):
    '''
    _define_files_from_yaml is a helper function that returns a list of input file elements based on the information in the YAML file. Each input file element is a dictionary that specifies the properties of an input file that can be uploaded to the web application. The function checks the type of the input file (table, image, or single cell) and uses a corresponding template from the templates module to set the default values for the file properties.

    define_settings_from_yaml is the main function that reads a YAML file and returns a JSON string containing the configuration settings for the web application. The function first loads the YAML file using yaml.safe_load. It then calls _define_files_from_yaml to get a list of input file elements, and constructs a dictionary containing the configuration settings. The dictionary has two main keys: "settingsConfig" and "resultsConfig".

    The "settingsConfig" dictionary contains information about the input parameters that can be set by the user. It has three keys: "disabledFields", "inputsRequireFiles", and "parameters". "disabledFields" is a list of input parameter names that should be disabled (i.e., not editable) in the web application. "inputsRequireFiles" is a list of input parameter names that require a file to be uploaded. "parameters" is a dictionary containing information about each input parameter. Each key in "parameters" is the name of an input parameter, and each value is a dictionary containing information about the parameter such as its title, type, default value, and so on.

    The "resultsConfig" dictionary contains information about the output generated by the web application. It has two keys: "description" and "saveModel". "description" is a string that describes the output, and "saveModel" is a boolean value that indicates whether the output should be saved as a model.

    Finally, the function returns a JSON string representation of the "settingsConfig" and "resultsConfig" dictionaries using the json.dumps function.
    '''
    
    parameters = yaml_dict['parameters']
    
    # Input parameters
    inputs_require_files = []
    input_parameters = []
        
    for key in parameters.keys():
        if parameters[key].get('user_defined'):
            if parameters[key]['user_defined'] == 'True':
                if not parameters[key].get('tooltip'):
                    parameters[key]['tooltip'] = key
                if not parameters[key].get('title'):
                    parameters[key]['title'] = key
                    
                # Numeric settings
                if parameters[key].get('type'):
                    if parameters[key]['type'] in ['int', 'float']:
                        input_parameters = _define_from_numeric(parameters[key], key, input_parameters)
                    
                    elif parameters[key]['type'] == 'str':
                        input_parameters, inputs_require_files = _define_from_string(parameters[key], key, input_parameters, inputs_require_files)
                else:
                    raise Exception(f"Please define 'type' for parameter {key}")
 
    input_files = _define_files_from_yaml(yaml_dict)
    
    #including workflow name
    input_parameters.append({
           "default_value": workflow_filename,
           "hidden": True,
           "input_type": "user_input",
           "name": "workflow_name",
           "title": "workflow_name",
           "tooltip": "workflow_name",
           "type": "text"
        })
    
    settings_config = {
        "disabledFields": inputs_require_files,
        "inputsRequireFiles": inputs_require_files,
        "parameters": {
            "header": "Set Parameters",
            "inputs": input_parameters
        },
        "uploadOptions": input_files
    }
    
    # Output parameters
    results_config = {
        "description": "No description provided"
    }
    
    if yaml_dict.get('output_settings'):
        if yaml_dict['output_settings'].get('description'):
            results_config['description'] = yaml_dict['output_settings']['description']
    
    app_settings = {
        "resultsConfig": results_config,
        "settingsConfig": settings_config
    }
            
    return json.dumps(app_settings)


def payload_from_yaml(yaml_dict):
    """
    Returns a JSON string of the results_for_payload dictionary and a list of additional artifacts.
    
    This can be used to populate a default json file for results

    Parameters:
    yaml_dict (dict): yaml dict containing output settings.

    Returns:
    Tuple containing the JSON string of results_for_payload dictionary and the list of additional artifacts.
    """
    
    if yaml_dict['output_settings'].get('folder'):
        results_for_payload, additional_artifacts = payload_from_folder(yaml_dict['output_settings']['folder'])
    else:
        results_for_payload, additional_artifacts = payload_from_config(yaml_dict)
    
    return results_for_payload, additional_artifacts
    

def _generate_carousel(output_settings_dict, result_type_key):
    full_files = []
    for carousel in output_settings_dict[result_type_key].keys():
        carousel_files = []
        for output_key, output_value in output_settings_dict[result_type_key][carousel].items():
            file = output_value['file']
            if file[0]=='/':
                file = file[1:] 
            carousel_files.append({'file': file,
                                    'title': output_value['title']})
        full_files.append(carousel_files)
    return full_files
    
    
def payload_from_config(yaml_dict):    
    print("Generating payload from output config")
    results_for_payload = {}
    
    if yaml_dict['output_settings'].get('images'):
        results_for_payload['images'] = _generate_carousel(output_settings_dict=yaml_dict['output_settings'], result_type_key='images')
        
    if yaml_dict['output_settings'].get('figures'):
        results_for_payload['figures'] = _generate_carousel(output_settings_dict=yaml_dict['output_settings'], result_type_key='figures')
        
    if yaml_dict['output_settings'].get('tables'):
        results_for_payload['tables'] = _generate_carousel(output_settings_dict=yaml_dict['output_settings'], result_type_key='tables')
        
    if yaml_dict['output_settings'].get('download'):
        full_files = []
        for output_file in yaml_dict['output_settings']['download'].keys():
            full_files.append({'file': yaml_dict['output_settings']['download'][output_file]['file'],
                                 'title': yaml_dict['output_settings']['download'][output_file]['title']})
        results_for_payload['download'] = full_files
        
    additional_artifacts = []
    if yaml_dict['output_settings'].get('artifacts'):
        for output_file, output_value in yaml_dict['output_settings']['artifacts'].items():
            additional_artifacts.append(output_value['file'])        
        
    return results_for_payload, additional_artifacts


def _generate_file_dict(file_list):
    full_files = []
    for file in file_list:
        if file[0]=='/':
            file = file[1:]
        full_files.append({'file': file, 'title': file.split('/')[-1].split('.')[0]})
    return full_files
    

def payload_from_folder(folder_loc):
    print("No payload config detected. Generating payload from output folder contents")
    # Based on contents of a given folder instead
    results_for_payload = {}
    folder_contents = os.listdir(folder_loc)

    tables = []
    images = []
    figures = []
    additional_artifacts = []
    for file in folder_contents:
        file_ext = file.split('.')[-1]
        if file_ext in ['csv', 'tsv', 'txt']:
            tables.append(folder_loc + file)
        elif file_ext in ['jpg', 'png']:
            images.append(folder_loc + file)
        elif file_ext in ['html']:
            figures.append(folder_loc + file)
        elif len(file.split('.')) > 1:
            if os.path.isdir(file):
                for sub_element in os.listdir(file):
                    additional_artifacts.append(folder_loc + file + '/' + sub_element)
            else:
                additional_artifacts.append(folder_loc + file)

    results_for_payload['images'] = [_generate_file_dict(images)]
    results_for_payload['tables'] = [_generate_file_dict(tables)]
    results_for_payload['figures'] = [_generate_file_dict(figures)]
    
    return results_for_payload, additional_artifacts            


def run_pre_demo_steps(workflow_filename: str):
    workflow_loc = '/app/' + workflow_filename
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
    
    print("Generating demo configuration dictionary")
    request = {'job_id':'test'}
    request['workflow_name'] = workflow_filename.split('.')[0]
        
    #set defaults where not present
    for key, value in yaml_dict['parameters'].items():
        # Check if default is present
        if key not in request:
            try:
                request[key] = value['default']
            except:
                print(f"Default not set for parameter {key}. Will this cause issues?")
    
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
    
    return(request, yaml_dict['stages'], yaml_dict['parameters'])


def run_post_demo_steps(request: dict, workflow_filename: str):
    workflow_loc = '/app/' + workflow_filename
    yaml_dict = get_yaml(workflow_loc)
    
    print("Template for settingsConfig in UI:")
    settingsConfig = define_settings_from_yaml(yaml_dict, workflow_filename)
    print(settingsConfig)
    
    print("Generating output payload:")
    results_for_payload, results_for_upload = payload_from_yaml(yaml_dict)
    print(results_for_payload)
    print("Additional artifacts for upload:")
    print(results_for_upload)
    
    # printing folder contents to aid in showing locations of outputs
    parameters = yaml_dict['parameters']
    for key in parameters.keys():
        if (parameters[key]['type']=='path'):
            print(f'Contents of {key} directory after processing, with location {request[key]}:')
            print(os.listdir(request[key]))
            