import yaml
import os
import json
from .templates import csv_template, image_template, sc_template, default_template
from pyflakes.api import isPythonFile, checkPath
from pyflakes.reporter import _makeDefaultReporter
import pycodestyle
import sys
from credentials import get_credentials


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
            

def validate_yaml_stages(yaml_dict, style_check = False):
    """Validating parameters from workflow yaml"""
    stages_in = yaml_dict['stages']
    stages = ['/app' + stage for stage in stages_in]
    
    valid_check = True
    invalid_stage = []
    invalid_path = []
    code_errors = []
    
    for key in stages.keys():

        #catch common yaml formating errors and check target is a python file
        for subkey, value in stages[key].items():
            if ":" in subkey:
                invalid_stage.append({key : subkey})
            elif not isPythonFile(value):
                invalid_path.append({key : subkey})
    
        #checking for code errors in scripts
        defaultReporter = _makeDefaultReporter()
        error_flag = checkPath(value, reporter = defaultReporter)
        if error_flag:
            code_errors.append(value)
    
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
        for key in stages.keys():
            style_errors = _run_pycodestyle(stages[key]['file'])
            if style_errors:
                print(f"Style errors with file {stages[key]['file']}:")
                print(style_errors)
            
    return valid_check
            
            
def validate_yaml_parameters(yaml_dict):
    """Validating parameters from workflow yaml"""
    # Check all required parameters are provided
    
    parameters = yaml_dict['parameters']
    valid_check = True
    no_default = []
    no_type = []
    bad_formating = []
    
    for key in parameters.keys():

        # Check if default is present
        if not parameters[key].get('default'):
            no_default.append(key)

        # Check if type is present
        if not parameters[key].get('type'):
            no_type.append(key)
        
        #catch common yaml formating errors
        for subkey in parameters[key].keys():
            if ":" in subkey:
                bad_formating.append({key : subkey})
                
    if no_type:
        valid_check = False
        print('Some parameters do not have their datatype specified: {}'.format(no_type))
        
    if no_default:
        valid_check = False
        print(f"These parameters do not have a default specified: {no_default}")
    
    if bad_formating:
        valid_check = False
        print(f"These parameters are not formatted correctly in yaml: {bad_formating}. Please ensure no ':' values are included in keys and there is space between keys and values")
        
    return valid_check
    
    
def _define_files_from_yaml(yaml_dict):
    
    input_files = []
    if yaml_dict['input_settings'].get('upload_options'):
        for key in yaml_dict['input_settings']['upload_options'].keys():
            if yaml_dict['input_settings']['upload_options'][key]['type'] == 'table':
                input_element = csv_template.copy()
            elif yaml_dict['input_settings']['upload_options'][key]['type'] == 'image':
                input_element = image_template.copy()
            elif yaml_dict['input_settings']['upload_options'][key]['type'] == 'single_cell':
                input_element = sc_template.copy()
            else:
                print("No template is available for this data modality. Some parts of the uploadOptions configuration may need to be entered manually")
                input_element = default_template.copy()
                if yaml_dict['input_settings'].get('data_structure'):
                    input_element['dataStructure'] = yaml_dict['input_settings']['data_structure']
                if yaml_dict['input_settings'].get('file_extensions'):
                    input_element['allowedFormats']['fileExtensions'] = yaml_dict['input_settings']['file_extensions']
                    strout = ' or '.join(map(str, yaml_dict['input_settings']['file_extensions']))
                    input_element['allowedFormats']['title'] = strout

            input_element['name'] = key
            input_element['title'] = yaml_dict['input_settings']['upload_options'][key]['title']
            if yaml_dict['input_settings']['upload_options'][key].get('demo_path'):
                input_element['demoDataDetails'] = {
                    'description':yaml_dict['input_settings']['upload_options'][key]['demo_description'],
                    'filePath':yaml_dict['input_settings']['upload_options'][key]['demo_path'],
                    'fileName':yaml_dict['input_settings']['upload_options'][key]['demo_path'].split('/')[-1],
                    'fileSource':[{                        'title': 'Data Source',                        'url':yaml_dict['input_settings']['upload_options'][key]['url']}]
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
    

def define_settings_from_yaml(yaml_dict):
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
        "description": "No description provided",
        "saveModel": False
    }
    
    if yaml_dict.get('output_settings'):
        if yaml_dict['output_settings'].get('description'):
            results_config['description'] = yaml_dict['output_settings']['description']
        if yaml_dict['output_settings'].get('save_model'):
            results_config['saveModel'] = (yaml_dict['output_settings']['save_model'] == "True")
    
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

    return json.dumps(results_for_payload), additional_artifacts
    

def _generate_carousel(output_settings_dict, result_type_key):
    full_files = []
    for carousel in output_settings_dict[result_type_key].keys():
        carousel_files = []
        for output_file in output_settings_dict[result_type_key][carousel].keys():
            carousel_files.append({'file': output_settings_dict[result_type_key][carousel][output_file]['file'],
                                    'title': output_settings_dict[result_type_key][carousel][output_file]['title']})
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
        for output_file in yaml_dict['output_settings']['artifacts'].keys():
            additional_artifacts.append(yaml_dict['output_settings']['artifacts'][output_file]['file'])
        
    return results_for_payload, additional_artifacts


def _generate_file_dict(file_list):
    full_files = []
    for file in file_list:
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
            additional_artifacts.append(folder_loc + file)

    if len(images) > 0:
        results_for_payload['images'] = _generate_file_dict(images)
    if len(tables) > 0:
        results_for_payload['tables'] = _generate_file_dict(tables)
    if len(figures) > 0:
        results_for_payload['figures'] = _generate_file_dict(figures)

    return results_for_payload, additional_artifacts            


def run_pre_demo_steps(workflow_filename: str):
    workflow_loc = '/app/' + workflow_filename
    yaml_dict = get_yaml(workflow_loc)
    
    print("Setting credentials")
    get_credentials()
    
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
        
    #set defaults where not present
    for key in yaml_dict['parameters'].keys():
        # Check if default is present
        if key not in request:
            try:
                request[key] = yaml_dict['parameters'][key]['default']
            except:
                print(f"Default not set for parameter {key}. Will this cause issues?")
    
    #set input files to the demo files
    request['input_files']={}
    if yaml_dict['input_settings']['upload_options']:
        for key in yaml_dict['input_settings']['upload_options']:
            try:
                request['input_files'][key] = yaml_dict['input_settings']['upload_options'][key]['demo_path']
            except:
                print(f"Demo path not set for input upload_option {key}. Will this cause issues?")
    else:
        print("No input data settings detected. Is this correct?")
    
    return(request, yaml_dict['stages'], yaml_dict['parameters'])


def run_post_demo_steps(workflow_filename: str):
    workflow_loc = '/app/' + workflow_filename
    yaml_dict = get_yaml(workflow_loc)
    
    print("Template for settingsConfig in UI:")
    settingsConfig = define_settings_from_yaml(yaml_dict)
    print(settingsConfig)
    
    print("Generating output payload:")
    results_for_payload, results_for_upload = payload_from_yaml(yaml_dict)
    print(results_for_payload)
    print("Additional artifacts for upload:")
    print(results_for_upload)