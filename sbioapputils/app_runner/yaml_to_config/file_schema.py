from typing import List


class UploadType:
    def __init__(self, type_: str):
        self.title = type_.capitalize()
        self.type = type_


class AllowedFormats:
    def __init__(self, extensions: List[str]):
        self.fileExtensions = extensions
        self.title = ''
        self.value = ''


class FileSchema:
    allowedFormats = AllowedFormats([])
    disabled = False
    supportsPreview = False
    uploadTypes = [UploadType('local'), UploadType('remote')]
    dataStructure = ''
