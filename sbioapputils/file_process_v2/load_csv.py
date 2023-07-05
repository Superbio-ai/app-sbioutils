from io import BytesIO
import pandas as pd
from pandas.errors import ParserError
from file_process.exceptions import DelimiterError, FormatError


TABULAR_EXTENSIONS = ['csv','tsv','txt']
TABULAR_FORMATS = ['pandas', 'numpy']

#to add: excel support
def load_tabular(file: BytesIO, target_format = 'pandas', **kwargs):
    ext = file.split('.')[-1]
    with open(file, 'rb') as f:
        f.seek(0)
        if ext in TABULAR_EXTENSIONS:
            delimiter = kwargs.get('delimiter')

            try:
                if not delimiter:
                    reader = pd.read_csv(f, sep=None, iterator=True, nrows=10)
                    delimiter = reader._engine.data.dialect.delimiter  # pylint: disable=protected-access

            except ParserError as exc:
                raise FormatError() from exc
        else:
            print("Only {TABULAR_EXTENSIONS} file extensions are currently handled for loading tabular data")
        f.seek(0)
        if target_format in TABULAR_FORMATS:
            if target_format == 'pandas':
                try:
                    data = pd.read_csv(f, sep=delimiter)
                except ParserError as exc:
                    raise DelimiterError() from exc
            elif target_format == 'numpy':
                try:
                    data_df = pd.read_csv(f, sep=delimiter)
                    data_numeric = data_df.select_dtypes(include=['int','float'])
                    data = data_numeric.to_numpy()
                    
                except ParserError as exc:
                    raise DelimiterError() from exc
        else:
            print("Only {TABULAR_FORMATS} python packages are currently used for loading tabular data")
            
    return data
