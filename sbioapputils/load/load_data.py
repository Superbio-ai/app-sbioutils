# -*- coding: utf-8 -*-
from file_process.csv.csv_processor import CSVFileProcessor
from file_process.h5ad.h5ad_processor import H5ADFileProcessor
from .constants import TABULAR_PANDAS_FORMATS, TABULAR_NUMPY_FORMATS


def load_tabular(file_loc: str, target_format: str = 'pandas', **kwargs):
    '''
    target_format can be pandas or pd, numpy or np
    possible additional arguments include: delimiter
    '''
    with open(file_loc, 'rb') as file:
        processor = CSVFileProcessor(file = file, **kwargs)
    if target_format in TABULAR_PANDAS_FORMATS:
        data = processor.data_df
    elif target_format in TABULAR_NUMPY_FORMATS:
        data_numeric = processor.data_df.select_dtypes(include=['int','float'])
        data = data_numeric.to_numpy()
    return data


def load_sc(file_loc: str, **kwargs):
    '''
    possible additional arguments include: TBC
    '''
    ext = file_loc.split('.')[-1]
    with open(file_loc, 'rb') as file:
        processor = H5ADFileProcessor(file = file, ext = ext, **kwargs)
    return processor.adata