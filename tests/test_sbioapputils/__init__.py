from io import BytesIO


INPUT_FILES_PATH = 'tests/test_sbioapputils/input_files'


def get_remote_file_obj(path: str):
    with open(path, 'rb') as file:
        file_obj = BytesIO(file.read())
        return file_obj
