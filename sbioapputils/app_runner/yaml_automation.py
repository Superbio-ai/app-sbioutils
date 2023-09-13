from io import BytesIO
from typing import List

import yaml
from copy import deepcopy
from .templates import csv_template, image_template, sc_template, standard_parameter_automation_prompt, standard_input_automation_prompt
from .templates import argparse_tags, click_tags, allowed_types, allowed_args, boolean_values

import openai
import re
from os import environ


def _parse_input_python(file: BytesIO):
    byte_lines = file.readlines()
    line_array = []

    argparse_flag = False
    click_flag = False

    for byte_line in byte_lines:
        # example of str_line: 'b'import os\r\n''
        str_line = str(byte_line)
        line = str_line.replace("b'", "").replace("\\r", "").replace("\\n", "")[:-1]
        # TODO add if line ends with coma - add next line to this line.
        # Strips the newline character
        line_array.append(line.strip())
        if any(tag in line for tag in argparse_tags):
            argparse_flag = True
        if any(tag in line for tag in click_tags):
            click_flag = True

    if argparse_flag and not click_flag:
        return line_array, "argparse"
    elif click_flag and not argparse_flag:
        return line_array, "click"
    else:
        return None, None
        
        
def _dict_from_args(filelines: List[str], library: str):
    if library == 'argparse':
        arg_command = '.add_argument('
    else:
        arg_command = '.option('
        
    parameter_dict = {}
    for line in filelines:
        if arg_command not in line:
            continue
        arg_string = line.split(arg_command)[1]
        arguments = arg_string.split(',')
        argname = arguments[0].split('--')[1].strip().strip("'")
        parameter_dict[argname] = {}

        for argument in arguments[1:]:
            argument_split = argument.strip().split('=')
            arg_value = ''.join(argument_split[1:])
            if len(arg_value.strip("'")) == 0:
                continue
            if arg_value.count('(') < arg_value.count(')'):
                arg_value = arg_value.rstrip(')')
            if arg_value[0] == "'" and arg_value[-1] == "'":
                arg_value = arg_value[1:-1]
            if len(argument_split) > 1:
                parameter_dict[argname][argument_split[0]] = arg_value
                    
    return parameter_dict


def _stages_from_scripts(filenames):
    stages = {}
    for file in filenames:
        file_name = file.split('/')[-1].split('.py')[0]
        stages[file_name] = {'file': file}
    return stages


def _is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
    

def _attempt_numeric(string, ntype):
    if ntype == 'int':
        try:
            return int(string)
        except ValueError:
            return string
    if ntype == 'float':
        try:
            return float(string)
        except ValueError:
            return string        
        

def _format_argparse_parameters(input_parameters):
    parameters = deepcopy(input_parameters)
    
    for key, subdict in parameters.items():
        # inferring / correcting type
        if 'type' in subdict:
            if subdict['type'] not in allowed_types:
                subdict['type'] = 'str'
        elif 'is_flag' in subdict:
            subdict['type'] = 'boolean'
            if 'default' not in subdict:
                subdict['default'] = False
        elif 'default' in subdict:
            if subdict['default'] in boolean_values:
                subdict['type'] = 'boolean'
            elif subdict['default'].isdigit():
                subdict['type'] = 'int'
            elif _is_float(subdict['default']):
                subdict['type'] = 'float'
            else:
                subdict['type'] = 'str'
        # adjusting naming conventions
        if 'help' in subdict:
            subdict['tooltip'] = subdict.pop('help')
        if 'choices' in subdict:
            subdict['options'] = subdict.pop('choices')
        if 'min' in subdict:
            subdict['min_value'] = subdict.pop('min')
        if 'max' in subdict:
            subdict['max_value'] = subdict.pop('max')
        # adjusting number formatting
        if 'type' in subdict:
            if subdict['type'] in ['int', 'float']:
                if 'default' in subdict:
                    subdict['default'] = _attempt_numeric(subdict['default'], subdict['type'])
                if 'min_value' in subdict:
                    subdict['min_value'] = _attempt_numeric(subdict['min_value'], subdict['type'])
                if 'max_value' in subdict:
                    subdict['max_value'] = _attempt_numeric(subdict['max_value'], subdict['type'])
                if 'increment' in subdict:
                    subdict['increment'] = _attempt_numeric(subdict['increment'], subdict['type'])
        # remove excess quotes from tooltip
        if 'tooltip' in subdict:
            raw_tip = subdict['tooltip'].strip("'")
            subdict['tooltip'] = str(raw_tip)
        # removing unknown arguments
        del_list = []
        for argkey in subdict.keys():
            if argkey not in allowed_args:
                del_list.append(argkey)
        [subdict.pop(argkey) for argkey in del_list]
    return parameters


def _prune_script(script_text):
    substrings = ["@click.option(", "parser.add_argument("]
    new_text = ""
    lines = list(set(script_text.splitlines()))

    for line in lines:
        if any(line.startswith(substring) for substring in substrings):
            new_text += line + "\n"
    
    return new_text


def _parse_input_python_v2(file: BytesIO, verbose: bool = False):
    
    script_text = file.getvalue().decode('ASCII')
    stripped_script = _prune_script(script_text)
    if verbose:
        line_count1 = len(script_text.splitlines())
        line_count2 = len(stripped_script.splitlines())
        print(f"Length of full script is {line_count1}, and the stripped script is {line_count2}")
    return stripped_script


def _parse_multiple_files(file_list, verbose=False):
    list_contents = []
    for file in file_list:
        list_contents.append(_parse_input_python_v2(file_loc=file, verbose=verbose))
    delimiter = '\n'
    result = delimiter.join(list_contents)
    return result


def openai_chat_completion(prompt, file_contents, max_token=50, outputs=1, temperature=0.75, model="gpt-4-0613"):
    
    messages = [{"role": "system", "content": prompt}, {"role": "user", "content": file_contents}]
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_token,
        n=outputs,
        #The range of the sampling temperature is 0 to 2.
        #lower values like 0.2=more random, higher values like 0.8=more focused and deterministic
        temperature=temperature
    )
    if outputs == 1:
        response_text = response['choices'][0]['message']['content']
    else:
        response_text = []
        for i in range(outputs):
            response_text.append(response['choices'][i]['message']['content'])
            
    return response_text


#sometimes chatgpt returns yaml+an explanation of the yaml above and below. This keeps only the yaml
def _extract_yaml(output):
    matches = re.findall(r"```(.*?)```", output, re.DOTALL)
    return matches[0].replace('yaml', '')


def is_invalid_yaml(text):
    try:
        yaml.safe_load(text)
        return False
    except yaml.YAMLError as exc:
        return True
    
    
def substring_parse_inputs(parameters):
    input_settings = {}
    for parameter_dict in parameters.values():
        if not all(k in parameter_dict.keys() for k in ("type", "default")):
            continue
        elif not parameter_dict['type'] in ['path', 'str']:
            continue
        else:
            file_split = parameter_dict['default'].split('.')
            # if a path, then usually has two parts
            if len(file_split) == 2:
                filename = file_split[0]
                fileext = file_split[1]
                if fileext in csv_template['allowedFormats']['fileExtensions']:
                    input_template = csv_template.copy()
                    input_settings[filename] = input_template
                elif fileext in image_template['allowedFormats']['fileExtensions']:
                    input_template = image_template.copy()
                    input_settings[filename] = input_template
                elif fileext in sc_template['allowedFormats']['fileExtensions']:
                    input_template = sc_template.copy()
                    input_settings[filename] = input_template

    return input_settings


def validate_multiple_outputs(outputs):
    checkpoint = 0
    not_yaml = 0
    valid_outputs = []
    for output in outputs:
        valid = True
        #check has not returned directories or checkpoints as input files
        if any(substring in output for substring in ['directory', 'Directory', 'checkpoint', 'Checkpoint']):
            checkpoint += 1
            valid = False
        if not is_invalid_yaml(output):
            not_yaml += 1
            valid = False
        if valid:
            valid_outputs.append(output)
    return valid_outputs


def chatgpt_parse_parameters(file_contents):
    openai.api_key = environ.get("OPENAI_KEY")
    parameters = openai_chat_completion(standard_parameter_automation_prompt, file_contents, max_token=4000, outputs=1)
    formatted_parameters = _extract_yaml(parameters)
    if is_invalid_yaml(formatted_parameters):
        raise ValueError('Invalid YAML format for parameters.')
    return(formatted_parameters)
    

def chatgpt_parse_inputs(file_contents):
    openai.api_key = environ.get("OPENAI_KEY")
    input_options = openai_chat_completion(standard_input_automation_prompt, file_contents, max_token=400, outputs=10, temperature=0.9)
    valid_options = validate_multiple_outputs(input_options)
    if len(valid_options)>0:
        input_settings = valid_options[0]
    else:
        raise ValueError('Invalid YAML format for inputs.')
    return(input_settings)


def substring_parse_parameters(files):
    parameters = {}
    library_found = False
    
    for file in files:
        file_lines, argument_parsing_library = _parse_input_python(file)
        if argument_parsing_library is not None:
            library_found = True
            new_parameters = _dict_from_args(file_lines, argument_parsing_library)
            parameters = {**parameters, **new_parameters}
    formatted_parameters = _format_argparse_parameters(parameters) if library_found else parameters
    return(formatted_parameters)

    
def parameters_yaml_from_args(files: List[BytesIO], filenames: List[str], method='chatgpt_parse'):
    
    #parameters
    if method == 'chatgpt_parse':
        file_contents = _parse_multiple_files(file_list=files, verbose=False)
        try:
            formatted_parameters = chatgpt_parse_parameters(file_contents)    
        except:
            formatted_parameters = substring_parse_parameters(files)
        try:
            input_settings = chatgpt_parse_inputs(file_contents)
        except:
            input_settings = substring_parse_inputs(formatted_parameters)
        
    elif method == 'substring_parse':
        formatted_parameters = substring_parse_parameters(files)
        input_settings = substring_parse_inputs(formatted_parameters)
    
    stages = _stages_from_scripts(filenames)
    
    # output settings not covered
    return stages, formatted_parameters, input_settings, method
