import gzip, tarfile, zipfile, shutil, os


def decompress(src: str, dest: str):
    #src (source file path, which should include file extension)
    #dest (destination directory path)
    
    if src.endswith("tar.gz"):
        tar = tarfile.open(src, "r:gz")
        tar.extractall(dest)
        tar.close()
    elif src.endswith("gz"):
        with gzip.open(src, 'r') as f_in, open(src.split(".gz")[0], 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(src)
    elif src.endswith("tar"):
        tar = tarfile.open(src, "r:")
        tar.extractall(dest)
        tar.close()
    elif src.endswith("zip"):
        with zipfile.ZipFile(src,"r") as zip_ref:
            zip_ref.extractall(dest)
    else:
        pass
