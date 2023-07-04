from io import BytesIO
import anndata
import h5py
import numpy as np

    
SCRNA_EXTENSIONS = ['h5ad','h5','loom','h5Seurat']
SCRNA_FORMATS = ['anndata']


def _h5_process(file):
    
   data_mat = h5py.File(file, 'r')
   #start processing data
   x = np.array(data_mat['X'])
   # y is the ground truth labels for evaluating clustering performance
   # If not existing, we skip calculating the clustering performance metrics (e.g. NMI ARI)
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
   
#to add: loom and rds support
def load_sc(file: BytesIO, ext = 'h5ad', target_format = 'anndata', **kwargs):
    
    if ext in SCRNA_EXTENSIONS:
        if ext == 'h5':
            adata = _h5_process(file)
        elif ext in ['h5ad','h5Seurat']:
            adata == anndata.read_h5ad(file)
        elif ext == 'loom':
            #kwargs here can include key where x matrix, obs_names and var_names are stored
            anndata.read_loom(file, **kwargs)    
    else:
        print("Only {SCRNA_EXTENSIONS} file extensions are currently handled for loading SC-RNA data. For R file formats we recommend first converting to either .loom or .h5Seurat format which can be done relatively easily using the LoomR or Seurat libraries")
    
    return adata
       