upload_options = ['csv_template', 'image_template', 'sc_template']

csv_template = {
    "allowedFormats": {
        "fileExtensions": ["csv", "tsv", "txt"],
        "title": ".csv, .tsv or .txt",
        "value": ""
    },
    "dataStructure": "Data should be in .csv, .tsv or .txt format",
    "disabled": False,
    "name": "table",
    "supportsPreview": True,
    "title": "Input Tabular Data",
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
        "fileExtensions": ["zip"],
        "title": ".zip",
        "value": ""
    },
    "dataStructure": "Images should be provided in a .zip compressed file",
    "disabled": False,
    "name": "image",
    "supportsPreview": False,
    "title": "Input Image Data",
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
    "name": "anndata",
    "supportsPreview": True,
    "title": "Input Annotated Data",
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
