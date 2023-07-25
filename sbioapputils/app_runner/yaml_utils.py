import json
import os
import yaml
from .templates import csv_template, image_template, sc_template, default_template


def get_yaml(workflow_loc):
    """Helper function to parse the workflow configuration."""    
    with open(workflow_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    return yaml_dict


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
    

def define_settings_from_yaml(workflow_loc, out_dir = None):
    '''
    _define_files_from_yaml is a helper function that returns a list of input file elements based on the information in the YAML file. Each input file element is a dictionary that specifies the properties of an input file that can be uploaded to the web application. The function checks the type of the input file (table, image, or single cell) and uses a corresponding template from the templates module to set the default values for the file properties.

    define_settings_from_yaml is the main function that reads a YAML file and returns a JSON string containing the configuration settings for the web application. The function first loads the YAML file using yaml.safe_load. It then calls _define_files_from_yaml to get a list of input file elements, and constructs a dictionary containing the configuration settings. The dictionary has two main keys: "settingsConfig" and "resultsConfig".

    The "settingsConfig" dictionary contains information about the input parameters that can be set by the user. It has three keys: "disabledFields", "inputsRequireFiles", and "parameters". "disabledFields" is a list of input parameter names that should be disabled (i.e., not editable) in the web application. "inputsRequireFiles" is a list of input parameter names that require a file to be uploaded. "parameters" is a dictionary containing information about each input parameter. Each key in "parameters" is the name of an input parameter, and each value is a dictionary containing information about the parameter such as its title, type, default value, and so on.

    The "resultsConfig" dictionary contains information about the output generated by the web application. It has two keys: "description" and "saveModel". "description" is a string that describes the output, and "saveModel" is a boolean value that indicates whether the output should be saved as a model.

    Finally, the function returns a JSON string representation of the "settingsConfig" and "resultsConfig" dictionaries using the json.dumps function.
    '''
    yaml_dict = get_yaml(workflow_loc)
    
    parameters = yaml_dict['parameters']
    
    # Input parameters
    inputs_require_files = []
    input_parameters = []
        
    for key, parameter in parameters.items():
        if parameter.get('user_defined'):
            if parameter['user_defined'] == 'True':
                if not parameter.get('tooltip'):
                    parameter['tooltip'] = key
                if not parameter.get('title'):
                    parameter['title'] = key
                    
                # Numeric settings
                if parameter.get('type'):
                    if parameter['type'] in ['int', 'float']:
                        input_parameters = _define_from_numeric(parameter, key, input_parameters)
                    
                    elif parameter['type'] == 'str':
                        input_parameters, inputs_require_files = _define_from_string(parameter, key, input_parameters, inputs_require_files)
                else:
                    raise Exception(f"Please define 'type' for parameter {key}")
 
    input_files = _define_files_from_yaml(yaml_dict)
    
    workflow_filename = workflow_loc.split('/')[-1]
    
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
    
    if out_dir:
        with open(out_dir + 'app_settings.json', 'w') as f:
            json.dumps(app_settings, f)
            
    return json.dumps(app_settings)


def payload_from_yaml(workflow_loc, config_only = False, out_dir = None):
    """
    Returns a JSON string of the results_for_payload dictionary and a list of additional artifacts.
    
    This can be used to populate a default json file for results

    Parameters:
    yaml_dict (dict): yaml dict containing output settings.

    Returns:
    Tuple containing the JSON string of results_for_payload dictionary and the list of additional artifacts.
    """
    yaml_dict = get_yaml(workflow_loc)
    
    if yaml_dict['output_settings'].get('folder') and not config_only:
        results_for_payload, additional_artifacts = payload_from_folder(yaml_dict['output_settings']['folder'], yaml_dict)
    else:
        results_for_payload, additional_artifacts = payload_from_config(yaml_dict)
    
    if out_dir:
        with open(out_dir + 'payload.json', 'w') as f:
            json.dumps(results_for_payload, f)
        with open(out_dir + 'additional.json', 'w') as f:
            json.dumps(additional_artifacts, f)
            
    return results_for_payload, additional_artifacts
    

def _generate_carousel(carousel_settings_dict):
    full_files = []
    for carousel in carousel_settings_dict.keys():
        carousel_files = []
        for output_key, output_value in carousel_settings_dict[carousel].items():
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
    output_settings = yaml_dict['output_settings']
    
    if output_settings.get('images'):
        results_for_payload['images'] = _generate_carousel(carousel_settings_dict=output_settings['images'])
        
    if output_settings.get('figures'):
        results_for_payload['figures'] = _generate_carousel(carousel_settings_dict=output_settings['figures'])
        
    if output_settings.get('tables'):
        results_for_payload['tables'] = _generate_carousel(carousel_settings_dict=output_settings['tables'])
        
    if output_settings.get('download'):
        full_files = []
        for output_file in output_settings['download'].keys():
            full_files.append({'file': output_settings['download'][output_file]['file'],
                                 'title': output_settings['download'][output_file]['title']})
        results_for_payload['download'] = full_files
        
    additional_artifacts = []
    if output_settings.get('artifacts'):
        for output_file, output_value in output_settings['artifacts'].items():
            additional_artifacts.append(output_value['file'])        
        
    return results_for_payload, additional_artifacts


def _generate_file_dict(file_list):
    full_files = []
    for file in file_list:
        if file[0]=='/':
            file = file[1:]
        full_files.append({'file': file, 'title': file.split('/')[-1].split('.')[0]})
    return full_files
    

def payload_from_folder(folder_loc, yaml_dict):
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
    
    output_settings = yaml_dict['output_settings']
    #override get from folder if config provided in yaml
    if output_settings.get('images'):
        results_for_payload['images'] = _generate_carousel(carousel_settings_dict=output_settings['images'])
    else:
        results_for_payload['images'] = [_generate_file_dict(images)]
        
    if output_settings.get('figures'):
        results_for_payload['figures'] = _generate_carousel(carousel_settings_dict=output_settings['figures'])
    else:
        results_for_payload['figures'] = [_generate_file_dict(figures)]
        
    if output_settings.get('tables'):
        results_for_payload['tables'] = _generate_carousel(carousel_settings_dict=output_settings['tables'])
    else:
        results_for_payload['tables'] = [_generate_file_dict(tables)]
        
    if output_settings.get('download'):
        full_files = []
        for output_file in output_settings['download'].keys():
            full_files.append({'file': output_settings['download'][output_file]['file'],
                                 'title': output_settings['download'][output_file]['title']})
        results_for_payload['download'] = full_files
    
    return results_for_payload, additional_artifacts            