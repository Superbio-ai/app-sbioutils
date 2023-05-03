import yaml
import os
import json
import * from templates

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
                    'fileSource':[{
                        'title': 'Data Source',
                        'url':yaml_dict['input_settings']['upload_options'][key]['url']}]
                    }
            input_files.append(input_element)
    return(input_files)    


def define_settings_from_yaml(yaml_loc):
    
    #load workflow configuration
    with open(yaml_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    parameters = yaml_dict['parameters']
    
    ########## Input parameters #################
    inputsRequireFiles = []
    input_parameters = []
        
    for key in parameters.keys():
        if parameters[key].get('user_defined'):
            if parameters[key]['user_defined'] == 'True':
                if not parameters[key].get('tooltip'):
                    parameters[key]['tooltip'] = key
                if not parameters[key].get('title'):
                    parameters[key]['title'] = key
                #Numeric settings#
                if parameters[key].get('type'):
                    if parameters[key]['type'] in ['int','float']:
                        if parameters[key]['type'] == 'int':
                            input_type='integer'
                        else:
                            input_type='float'
                        input_parameters.append({
                            "name": key,
                            "title": parameters[key]['title'],
                            "tooltip": parameters[key]['tooltip'],
                            "type": input_type,
                            "default_value": parameters[key]['default'],
                            "input_type":"slider",
                            "increment": parameters[key]['increment'],
                            "max_value": parameters[key]['max_value'],
                            "max_value_included":True,
                            "min_value": parameters[key]['min_value'],
                            "min_value_inclusive":True
                            })
                
                    elif parameters[key]['type'] == 'str':
                        if parameters[key].get('from_data'):
                            if parameters[key]['from_data'] == 'True':
                                ######### create data-defined settings #############
                                input_parameters.append({
                                    "name": key,
                                    "title": parameters[key]['title'],
                                    "tooltip": parameters[key]['tooltip'],
                                    "type": 'str',
                                    "default_value":{'label': parameters[key]['default'],'value': parameters[key]['default']},
                                    "input_type":"dropdown",
                                    "options": []
                                    })
                                inputsRequireFiles.append(key)
                                dropdown=False
                            else:
                                dropdown=True
                        else:
                            dropdown=True
                        
                        #Category settings#
                        if dropdown:
                            option_list= []
                            for option in parameters[key]['options']:
                                option_list.append({"label": option, "value": option})
                            input_parameters.append({
                                "name": key,
                                "title": parameters[key]['title'],
                                "tooltip": parameters[key]['tooltip'],
                                "type": 'str',
                                "default_value":{'label': parameters[key]['default'],'value': parameters[key]['default']},
                                "input_type":"dropdown",
                                "options": option_list
                                })
                else:
                    raise Exception(f"Please define 'type' for parameter {key}")
        
    input_files = _define_files_from_yaml(yaml_dict)
    
    settings_config = {"disabledFields":inputsRequireFiles,
                       "inputsRequireFiles":inputsRequireFiles,
                       "parameters":{
                           "header": "Set Parameters",
                           "inputs":input_parameters},
                       "uploadOptions":input_files}
    
    ########## Output parameters #################
    results_config = {
        "description": "No description provided",
        "saveModel": False
        }
    if yaml_dict.get('output_settings'):
        if yaml_dict['output_settings'].get('description'):
            results_config['description'] = yaml_dict['output_settings']['description']
        if yaml_dict['output_settings'].get('save_model'):
            results_config['saveModel'] = (yaml_dict['output_settings']['save_model'] == "True")
    
    app_settings = {"resultsConfig":results_config,
                    "settingsConfig":settings_config}
    
    return(json.dumps(app_settings))


def payload_from_yaml(yaml_loc):
        
    #load workflow configuration
    with open(yaml_loc, "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    
    if yaml_dict['output_settings'].get('folder'):
        results_for_payload, additional_artifacts = _payload_from_folder(yaml_dict['output_settings']['folder'])
    else:
        results_for_payload, additional_artifacts = _payload_from_config(yaml_dict)
        
    return(json.dumps(results_for_payload), additional_artifacts)
    

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
        
    return(results_for_payload, additional_artifacts)
        

def _payload_from_folder(folder_loc):
    #based on contents of a given folder instead
    results_for_payload = {}
    folder_contents = os.listdir(folder_loc)
    
    tables = []
    images = []
    figures = []
    additional_artifacts = []
    for file in folder_contents:
        file_ext = file.split('.')[-1]
        if file_ext in ['csv','tsv','txt']:
            tables.append(folder_loc + file)
        elif file_ext in ['jpg','png']:
            images.append(folder_loc + file)
        elif file_ext in ['html']:
            figures.append(folder_loc + file)
        elif len(file.split('.'))>1:
            additional_artifacts.append(folder_loc + file)
    
    if len(images)>0:
        full_files = []
        for image in images:
            full_files.append({'file': image, 'title': image.split('/')[-1].split('.')[0]})
        results_for_payload['images'] = [full_files]
    if len(tables)>0:
        full_files = []
        for table in tables:
            full_files.append({'file': table, 'title': table.split('/')[-1].split('.')[0]})
        results_for_payload['tables'] = [full_files]
    if len(figures)>0:
        full_files = []
        for figure in figures:
            full_files.append({'file': figure, 'title': figure.split('/')[-1].split('.')[0]})
        results_for_payload['figures'] = [full_files]
    
    return(results_for_payload, additional_artifacts)
            