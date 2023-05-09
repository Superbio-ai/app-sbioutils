from typing import List

import yaml
import os
import json
from templates import csv_template, image_template, sc_template, default_template









def _define_files_from_yaml(yaml_dict: dict):
    input_files = []
    upload_options = get_nested_value(yaml_dict, [INPUT_SETTINGS_STR, UPLOAD_OPTIONS_STR])
    if not upload_options:
        return None
    for key, value in upload_options.items():
        template = TYPE_TEMPLATE_MAP.get(value[TYPE_STR])
        if template:
            input_element = TYPE_TEMPLATE_MAP.get(value[TYPE_STR]).copy()
        else:
            print("No template is available for this data modality. "
                  "Some parts of the uploadOptions configuration may need to be entered manually")
            input_element = _create_custom_modality(yaml_dict)

        input_element['name'] = key
        input_element['title'] = value[TITLE_STR]
        if value.get(DEMO_PATH_STR):
            input_element['demoDataDetails'] = {
                'description': value['demo_description'],
                'filePath': value['demo_path'],
                'fileName': value['demo_path'].split('/')[-1],
                'fileSource': [{'title': 'Data Source', 'url': value['url']}]
            }
        input_files.append(input_element)
    return input_files


def _create_custom_modality(yaml_dict):
    input_element = default_template.copy()
    data_structure = get_nested_value(yaml_dict, [INPUT_SETTINGS_STR, DATA_STRUCTURE_STR])
    if data_structure:
        input_element['dataStructure'] = data_structure
    file_extensions = get_nested_value(yaml_dict, [INPUT_SETTINGS_STR, FILE_EXTENSIONS_STR])
    if file_extensions:
        input_element['allowedFormats']['fileExtensions'] = file_extensions
        input_element['allowedFormats']['title'] = ' or '.join(map(str, file_extensions))
    return input_element
 

def define_settings_from_yaml(yaml_loc):
    '''
    _define_files_from_yaml is a helper function that returns a list of input file elements based on the information in the YAML file. Each input file element is a dictionary that specifies the properties of an input file that can be uploaded to the web application. The function checks the type of the input file (table, image, or single cell) and uses a corresponding template from the templates module to set the default values for the file properties.

    _define_settings_from_yaml is the main function that reads a YAML file and returns a JSON string containing the configuration settings for the web application. The function first loads the YAML file using yaml.safe_load. It then calls _define_files_from_yaml to get a list of input file elements, and constructs a dictionary containing the configuration settings. The dictionary has two main keys: "settingsConfig" and "resultsConfig".

    The "settingsConfig" dictionary contains information about the input parameters that can be set by the user. It has three keys: "disabledFields", "inputsRequireFiles", and "parameters". "disabledFields" is a list of input parameter names that should be disabled (i.e., not editable) in the web application. "inputsRequireFiles" is a list of input parameter names that require a file to be uploaded. "parameters" is a dictionary containing information about each input parameter. Each key in "parameters" is the name of an input parameter, and each value is a dictionary containing information about the parameter such as its title, type, default value, and so on.

    The "resultsConfig" dictionary contains information about the output generated by the web application. It has two keys: "description" and "saveModel". "description" is a string that describes the output, and "saveModel" is a boolean value that indicates whether the output should be saved as a model.

    Finally, the function returns a JSON string representation of the "settingsConfig" and "resultsConfig" dictionaries using the json.dumps function.
    '''
    with open(yaml_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
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
                        if parameters[key]['type'] == 'int':
                            input_type = 'integer'
                        else:
                            input_type = 'float'
                        input_parameters.append({
                            "name": key,
                            "title": parameters[key]['title'],
                            "tooltip": parameters[key]['tooltip'],
                            "type": input_type,
                            "default_value": parameters[key]['default'],
                            "input_type": "slider",
                            "increment": parameters[key]['increment'],
                            "max_value": parameters[key]['max_value'],
                            "max_value_included": True,
                            "min_value": parameters[key]['min_value'],
                            "min_value_inclusive": True
                        })
                    
                    elif parameters[key]['type'] == 'str':
                        if parameters[key].get('from_data'):
                            if parameters[key]['from_data'] == 'True':
                                # Create data-defined settings
                                input_parameters.append({
                                    "name": key,
                                    "title": parameters[key]['title'],
                                    "tooltip": parameters[key]['tooltip'],
                                    "type": 'str',
                                    "default_value":{'label': parameters[key]['default'],'value': parameters[key]['default']},
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
                            for option in parameters[key]['options']:
                                option_list.append({"label": option, "value": option})
                            input_parameters.append({
                                "name": key,
                                "title": parameters[key]['title'],
                                "tooltip": parameters[key]['tooltip'],
                                "type": 'str',
                                "default_value":{'label': parameters[key]['default'],'value': parameters[key]['default']},
                                "input_type": "dropdown",
                                "options": option_list
                            })
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


def payload_from_yaml(yaml_loc):
    """
    Returns a JSON string of the results_for_payload dictionary and a list of additional artifacts.

    Parameters:
    yaml_loc (str): Path to the YAML file containing the workflow configuration.

    Returns:
    Tuple containing the JSON string of results_for_payload dictionary and the list of additional artifacts.
    """

    # Load workflow configuration
    with open(yaml_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    if yaml_dict['output_settings'].get('folder'):
        results_for_payload, additional_artifacts = _payload_from_folder(yaml_dict['output_settings']['folder'])
    else:
        results_for_payload, additional_artifacts = _payload_from_config(yaml_dict)

    return json.dumps(results_for_payload), additional_artifacts
    

def _payload_from_config(yaml_dict):    
    results_for_payload = {}
    
    if yaml_dict['output_settings'].get('images'):
        full_files = []
        for carousel in yaml_dict['output_settings']['images'].keys():
            carousel_files = []
            for output_file in yaml_dict['output_settings']['images'][carousel].keys():
                carousel_files.append({'file': yaml_dict['output_settings']['images'][carousel][output_file]['file'],
                                        'title': yaml_dict['output_settings']['images'][carousel][output_file]['title']})
            full_files.append(carousel_files)
        results_for_payload['images'] = full_files
        
    if yaml_dict['output_settings'].get('figures'):
        full_files = []
        for carousel in yaml_dict['output_settings']['figures'].keys():
            carousel_files = []
            for output_file in yaml_dict['output_settings']['figures'][carousel].keys():
                carousel_files.append({'file': yaml_dict['output_settings']['figures'][carousel][output_file]['file'],
                                        'title': yaml_dict['output_settings']['figures'][carousel][output_file]['title']})
            full_files.append(carousel_files)
        results_for_payload['figures'] = full_files
        
    if yaml_dict['output_settings'].get('tables'):
        full_files = []
        for carousel in yaml_dict['output_settings']['tables'].keys():
            carousel_files = []
            for output_file in yaml_dict['output_settings']['tables'][carousel].keys():
                carousel_files.append({'file': yaml_dict['output_settings']['tables'][carousel][output_file]['file'],
                                        'title': yaml_dict['output_settings']['tables'][carousel][output_file]['title']})
            full_files.append(carousel_files)
        results_for_payload['tables'] = full_files
        
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


def _payload_from_folder(folder_loc):
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
        full_files = []
        for image in images:
            full_files.append({'file': image, 'title': image.split('/')[-1].split('.')[0]})
        results_for_payload['images'] = [full_files]
    if len(tables) > 0:
        full_files = []
        for table in tables:
            full_files.append({'file': table, 'title': table.split('/')[-1].split('.')[0]})
        results_for_payload['tables'] = [full_files]
    if len(figures) > 0:
        full_files = []
        for figure in figures:
            full_files.append({'file': figure, 'title': figure.split('/')[-1].split('.')[0]})
        results_for_payload['figures'] = [full_files]

    return results_for_payload, additional_artifacts
