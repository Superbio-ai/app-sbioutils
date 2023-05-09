from sbioapputils.app_runner.constants import TITLE_STR, DEMO_PATH_STR

upload_options = ['csv_template', 'image_template', 'sc_template']


class TemplateBase:
    disabled = False
    uploadTypes = [
        {
            "title": "Local",
            "type": "local"
        },
        {
            "title": "Remote",
            "type": "remote"
        }
    ]

    def __init__(self, key: str, value: dict):
        self.name = key
        self.title = value[TITLE_STR]
        if value.get(DEMO_PATH_STR):
            self.demoDataDetails = {
                'description': value['demo_description'],
                'filePath': value['demo_path'],
                'fileName': value['demo_path'].split('/')[-1],
                'fileSource': [{'title': 'Data Source', 'url': value['url']}]
            }


class CSVTemplate(TemplateBase):
    allowedFormats = {
        "fileExtensions": ["csv", "tsv", "txt"],
        "title": ".csv, .tsv or .txt",
        "value": ""
    }
    dataStructure = "Data should be in .csv, .tsv or .txt format"
    name = "table"
    supportsPreview = True
    title = "Input Tabular Data"


class ImageTemplate(TemplateBase):
    allowedFormats = {
        "fileExtensions": ["zip"],
        "title": ".zip",
        "value": ""
    }
    dataStructure = "Images should be provided in a .zip compressed file"
    name = "image"
    supportsPreview = False
    title = "Input Image Data"


class SCTemplate(TemplateBase):
    allowedFormats = {
        "fileExtensions": ["h5ad", "h5"],
        "title": ".h5ad or .h5",
        "value": ""
    }
    dataStructure = "Data should be in .h5ad or .h5 format"
    name = "anndata"
    supportsPreview = True
    title = "Input Annotated Data"


# default_template = {
#     "allowedFormats": {
#         "fileExtensions": [],
#         "title": "",
#         "value": ""
#     },
#     "supportsPreview": False,
#
#     "dataStructure": ""
# }
