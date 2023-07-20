import pytest

from load.load_data import load_tabular, load_sc
from load.decompress import decompress
from tests.test_sbioapputils import INPUT_FILES_PATH

from pandas import DataFrame
from numpy import array
from anndata import AnnData
from os import listdir

class TestLoad:
    
    #test read csv, tsv, txt
    def test_load_csv(self):
        file_loc = f'{INPUT_FILES_PATH}/follicular_obs_sample.csv'
        data = load_tabular(file_loc)
        assert isinstance(data, DataFrame)

    def test_load_tsv(self):
        file_loc = f'{INPUT_FILES_PATH}/liver.tsv'
        data = load_tabular(file_loc)
        assert isinstance(data, DataFrame)
    
    def test_load_txt(self):
        file_loc = f'{INPUT_FILES_PATH}/wine_quality.txt'
        data = load_tabular(file_loc)
        assert isinstance(data, DataFrame)
        
    def test_set_delimiter(self):
        file_loc = f'{INPUT_FILES_PATH}/liver.tsv'
        data = load_tabular(file_loc, delimiter='/t')
        assert isinstance(data, DataFrame)
    
    def test_return_numpy(self):
        file_loc = f'{INPUT_FILES_PATH}/wine_quality.txt'
        data = load_tabular(file_loc, target_format = 'numpy')
        assert isinstance(data, array)
    
    #test load h5, h5ad, h5Seurat
    def test_load_h5(self):
        file_loc = f'{INPUT_FILES_PATH}/worm_neuron_cell.h5'
        data = load_sc(file_loc)
        assert isinstance(data, AnnData)
    
    def test_load_h5ad(self):
        file_loc = f'{INPUT_FILES_PATH}/follicular_sample.h5ad'
        data = load_sc(file_loc)
        assert isinstance(data, AnnData)
        
    def test_load_h5Seurat(self):
        file_loc = f'{INPUT_FILES_PATH}/liver_sample.h5Seurat'
        data = load_sc(file_loc)
        assert isinstance(data, AnnData)
        
    #decompress
    def test_unzip(self):
        src = f'{INPUT_FILES_PATH}/test_zip.zip'
        dest = 'zip_out/'
        decompress(src, dest)
        files = listdir(dest)
        assert len(files) == 5
        
    def test_untar(self):
        src = f'{INPUT_FILES_PATH}/test_tar.tar'
        dest = 'tar_out/'
        decompress(src, dest)
        files = listdir(dest)
        assert len(files) == 5
        
    def test_un_gzip(self):
        src = f'{INPUT_FILES_PATH}/test_tar.tar.gz'
        dest = 'gz_out/'
        decompress(src, dest)
        files = listdir(dest)
        assert len(files) == 5