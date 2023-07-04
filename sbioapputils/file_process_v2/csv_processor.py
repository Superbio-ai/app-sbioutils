from io import BytesIO
import pandas as pd
import numpy as np
from pandas.errors import ParserError
from file_process.exceptions import DelimiterError, FormatError


TABULAR_EXTENSIONS = ['csv','tsv','txt']
TABULAR_FORMATS = ['pandas', 'numpy']

#to add: excel support
def load_tabular(file: BytesIO, ext = 'csv', target_format = 'pandas', **kwargs):

    if ext in TABULAR_EXTENSIONS:
        delimiter = kwargs.get('delimiter')
            
        try:
            if not delimiter:
                reader = pd.read_csv(file, sep=None, iterator=True, nrows=10)
                delimiter = reader._engine.data.dialect.delimiter  # pylint: disable=protected-access
                file.seek(0)
        except ParserError as exc:
            raise FormatError() from exc
    else:
        print("Only {TABULAR_EXTENSIONS} file extensions are currently handled for loading tabular data")
        
    if target_format in TABULAR_FORMATS:
        if target_format == 'pandas':
            try:
                data = pd.read_csv(file, sep=delimiter)
            except ParserError as exc:
                raise DelimiterError() from exc
        elif target_format == 'numpy':
            #try:
                #below assumes first row are column names
                data = np.load_txt(file, delimiter=delimiter, skiprows=1)
            #except Error as exc:
             #   raise DelimiterError() from exc
    else:
        print("Only {TABULAR_FORMATS} python packages are currently used for loading tabular data")
            
    return data
