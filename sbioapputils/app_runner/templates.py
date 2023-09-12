upload_options = ['csv_template', 'image_template', 'sc_template']

csv_template = {
    "allowedFormats": {
        "fileExtensions": ["csv", "tsv", "txt"],
        "title": ".csv, .tsv or .txt",
        "value": ""
    },
    "dataStructure": "Data should be in .csv, .tsv or .txt format",
    "disabled": False,
    "supportsPreview": True,
    "title": "Input Tabular Data",
    "description": "Insert desccription here",
    "type": "tabular",
    "uploadTypes": [
        {
            "title": "Local",
            "type": "local"
        },
        {
            "title": "Remote",
            "type": "remote"
        }
    ]
}

image_template = {
    "allowedFormats": {
        "fileExtensions": ["zip","gz","tar"],
        "title": ".zip",
        "value": ""
    },
    "dataStructure": "Images should be provided in a .zip .gz or .tar compressed file",
    "disabled": False,
    "supportsPreview": False,
    "title": "Input Image Data",
    "description": "Insert desccription here",
    "type": "images",
    "uploadTypes": [
        {
            "title": "Local",
            "type": "local"
        },
        {
            "title": "Remote",
            "type": "remote"
        }
    ]
}

sc_template = {
    "allowedFormats": {
        "fileExtensions": ["h5ad", "h5"],
        "title": ".h5ad or .h5",
        "value": ""
    },
    "dataStructure": "Data should be in .h5ad or .h5 format",
    "disabled": False,
    "supportsPreview": True,
    "title": "Input Annotated Data",
    "description": "Insert desccription here",
    "type": "single-cell",
    "uploadTypes": [
        {
            "title": "Local",
            "type": "local"
        },
        {
            "title": "Remote",
            "type": "remote"
        }
    ]
}

default_template = {
    "allowedFormats": {
        "fileExtensions": [],
        "title": "",
        "value": ""
    },
    "disabled": False,
    "supportsPreview": False,
    "title": "Input Data",
    "description": "Insert desccription here",
    "type": "Unknown",
    "uploadTypes": [
        {
            "title": "Local",
            "type": "local"
        },
        {
            "title": "Remote",
            "type": "remote"
        }
    ],
    "dataStructure": ""
}

argparse_tags = ['from argparse', 'import argparse', 'ArgumentParser']
click_tags = ['from click', 'import click']
allowed_types = ['str', 'int', 'float', 'path', 'boolean']
allowed_args = ['type', 'default', 'tooltip', 'min_value', 'max_value', 'increment', 'user_defined', 'options',
                'from_data', 'input_type']
boolean_values = ['True', 'False', 'true', 'false', True, False]

standard_yaml_automation_prompt = """Can you list all the arguments and options in this script?
            For numeric arguments, please infer reasonable min, max and increment values. The max should be at most 1000 times the min and should not be None.
            For arguments without defaults, please infer reasonable defaults.
            For arguments without type, please infer the likely type.
            Please provide this as a YAML configuration file.
            Add the option 'input_type' as 'slider' for numeric, 'dropdown' for string, 'checkbox' for Boolean.
            Rename 'help' or similar options as 'tooltip'.
            If possible dropdown values are included in tooltips then include these as another option called "options" with the possible values provided in an array.
            Remove any arguments which are related to hardware configuration.
            Below are two examples of what an argument should look like:
            ndf:
              type: int
              help: Number of discriminator filters in the first convolutional layer.
              input_type: slider
              default: 64
              min: 16
              max: 512
              increment: 16
            init-type:
              type: str
              tooltip: 'network initialization [normal | xavier | kaiming | orthogonal]'
              input_type: dropdown
              options: ['normal','xavier','kaiming','orthogonal']
              default: 'normal'  
            """