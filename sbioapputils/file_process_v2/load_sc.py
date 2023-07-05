from io import BytesIO
import anndata
import h5py
import numpy as np

    
SCRNA_EXTENSIONS = ['h5ad','h5','h5Seurat']
SCRNA_FORMATS = ['anndata']


def _h5_process(file):
    
   data_mat = h5py.File(file, 'r')
   #start processing data
   x = np.array(data_mat['X'])
   if 'Y' in data_mat:
       y = np.array(data_mat['Y'])
   else:
       y = None
   data_mat.close()

   # preprocessing scRNA-seq read counts matrix
   adata = anndata.AnnData(x)
   if y is not None:
       adata.obs['Group'] = y
   
   return adata
   
#to add: loom, h5seurat and rds support
def load_sc(file: BytesIO, target_format = 'anndata', **kwargs):
    ext = file.split('.')[-1]

    if ext in SCRNA_EXTENSIONS:
        if ext == 'h5':
            adata = _h5_process(file)
        elif ext in ['h5ad','h5Seurat']:
            adata = anndata.read_h5ad(file)

    else:
        print("Only {SCRNA_EXTENSIONS} file extensions are currently handled for loading SC-RNA data. For R file formats we recommend first converting to .h5Seurat format which can be done relatively easily using the Seurat R library")
    
    return adata
       