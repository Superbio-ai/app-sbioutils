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

standard_parameter_automation_prompt = """Can you list all the arguments and options in this script?
            For numeric arguments, please infer reasonable min, max and increment values. The max should be at most 1000 times the min and should not be None.
            For arguments without defaults, please infer reasonable defaults.
            For arguments without type, please infer the likely type.
            Provide this as a YAML configuration file.
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

standard_input_automation_prompt = """
        Based on the arguments in this script, make an inference about what files are needed, excluding directories or checkpoints.
        Once you have identified these files, create a YAML configuration file.
        Each file should have a separate configuration.
        Infer what file extensions might be suitable and include these in the 'type' option. For example, tabular data can be csv, txt or tsv. Type refers to file extension type, not data type.
        Identify a suitable title.
        The name should be at the root of the yaml. For example if the name of an argument is 'this_is_my_argument' it should be at the root.
        Infer any information relating to data structure, for example based on argument descriptions or help or tooltips, and include as text in the 'data_structure' option. If this cannot be found provide a sensible inference based on the file extension types.
        If possible, infer what test or demo data might be provided, and include a description in the 'demo_description' option. If not available use the text "INSERT DEMO DESCRIPTION HERE" instead.
        In your response delete any arguments which refer to directories or checkpoints. There should be at least one input file remaining.
        Avoid repeating this prompt, apologizing or self-referencing.
        name_of_argument:
            data_structure: Data should be in .csv .txt or .tsv tabular format. Columns for covariate comparisons
            should be included in the dataset.
            demo_description: Single cell data for follicular lymphoma.
            title: Single Cell RNA-Seq Data
            type:
              - csv
              - txt
              - tsv
            """