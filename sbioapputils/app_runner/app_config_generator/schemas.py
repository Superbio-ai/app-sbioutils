from sbioapputils.app_runner import CSVTemplate, ImageTemplate, SCTemplate
from sbioapputils.app_runner.constants import INPUT_SETTINGS_STR, UPLOAD_OPTIONS_STR, TYPE_STR
from sbioapputils.common import get_nested_value

TYPE_TEMPLATE_MAP = {
    'table': CSVTemplate,
    'image': ImageTemplate,
    'single_cell': SCTemplate
}


class FileConfigFactory:
    @classmethod
    def get(cls, key: str, value: dict, yaml_dict: dict):
        template = TYPE_TEMPLATE_MAP.get(value[TYPE_STR])


class FileConfig:
    def __init__(self, yaml_dict: dict):


            if template:
                input_element = TYPE_TEMPLATE_MAP.get(value[TYPE_STR]).copy()
            else:
                print("No template is available for this data modality. "
                      "Some parts of the uploadOptions configuration may need to be entered manually")
                input_element = _create_custom_modality(yaml_dict)



        return input_files


class Config:
    def __init__(self, yaml_dict: dict):
        input_files = []
        upload_options = get_nested_value(yaml_dict, [INPUT_SETTINGS_STR, UPLOAD_OPTIONS_STR])
        for key, value in upload_options.items():
            file_config = FileConfigFactory(key, value, yaml_dict)
            input_files.append(file_config)
