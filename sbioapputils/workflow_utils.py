import os
import yaml
import warnings
import argparse


def _parse_workflow():
    
    #load workflow configuration
    with open("app/workflow.yml", "r") as stream:
        try:
            yaml_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    name = yaml_dict['name']
    entry_points = yaml_dict['entry_points']
    parameters = yaml_dict['parameters']
    
    return(name, entry_points, parameters)
    

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)
    
    
def validate_config(request, job_id):
    
    name, entry_points, parameters = _parse_workflow()
    
    for key, value in request['input_files'].items():
        request[key] = value
    request['job_id'] = job_id
        
    #check all required parameters are provided
    no_default = []
    default = {}
    no_type = []
    wrong_data_types = []
    invalid_value = []
        
    for key in parameters.keys():
        
        #check if type is present
        if not parameters[key].get('type'):
            no_type.append(key)
        else:
            #check if type is correct
            try:
                if not type(request[key])==parameters[key]['type']:
                    wrong_data_types.append(key)
            #on error if config[key] not present
            except:
                pass
        
        #check if default is present
        if not parameters[key].get('default'):
            no_default.append(key)
        else:
            default[key] = parameters[key]['default']
            #set defaults if not present
            if not request.get(key):
                request[key] =  parameters[key]['default']
                
        if parameters[key].get('user_defined'):
            if parameters[key]['user_defined'] == 'True':
                if parameters[key]['type'] in ['int','float']:
                    #check between min and max
                    if parameters[key].get('max_value'):
                        if (request[key]> parameters[key]['max_value']):
                            invalid_value.append(key)
                    if parameters[key].get('min_value'):
                        if (request[key]< parameters[key]['min_value']):
                            invalid_value.append(key)
                
                elif parameters[key]['type'] == 'str':
                    if parameters[key].get('from_data'):
                        if parameters[key]['from_data'] == 'True':
                            dropdown=False
                        else:
                            dropdown=True
                    else:
                        dropdown=True
                    
                    #Category settings#
                    if dropdown:
                        if request[key] not in parameters[key]['options']:
                            invalid_value.append(key)
        #create directory if needed
        try:
            if str(request[key])[-1]=='/':
                if not os.path.exists(request[key]):
                    os.mkdir(request[key])
                    #print("Directory '% s' created" % request[key])
        except:
            pass
                    
    if not all(param in request.keys() for param in no_default):
        raise Exception(f"These required parameters are not specified: {list(set(no_default) - set(request.keys()))}")
    
    if not all(param in request.keys() for param in no_type):
        raise Exception(f"These parameters have an incorrect data type: {list(set(wrong_data_types) - set(request.keys()))}")
            
    if len(no_type)>0:
        warnings.warn('Some parameters do not have their datatype specified: {}'.format(no_type))
    
    if len(invalid_value)>0:
        raise Exception(f"These parameters have invalid values (out of specified range of allowed values): {invalid_value}")
        
    return(request, name, entry_points, parameters)


def parse_arguments():
    
    name, entry_points, parameters = _parse_workflow()
    
    parser = argparse.ArgumentParser(add_help=False, conflict_handler='resolve')
    for key in parameters.keys():
        if parameters[key]['type']=='float':
            parser.add_argument(f"--{key}", type=float)
        elif parameters[key]['type']=='int':
            parser.add_argument(f"--{key}", type=int)
        else:
            parser.add_argument(f"--{key}")
    
    args, unknown = parser.parse_known_args()
    
    return(args)