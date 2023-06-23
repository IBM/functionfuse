from .base import generate_name, FILE_PROTOCOL, S3_PROTOCOL
from dask.array.core import Array
import dask.array as da
import zarr, h5py
import posixpath, s3fs



class DaskArraySerializer:
    
    datapath = "dask_arrays"
    name = "HDFSerializer"
    serializer_class = Array

    @classmethod
    def get_s3_root(cls, s3):
        client = s3["client"]
        folder = posixpath.join(s3["folder"], cls.datapath)
        store = s3fs.S3Map(root=folder, s3=client, check=False)
        root = zarr.group(store=store)
        return root


    @classmethod
    def pickle(cls, obj : Array, protocols : dict):

        if FILE_PROTOCOL in protocols:
            file = protocols[FILE_PROTOCOL]
            filename = generate_name()
            f = file.open(filename, "wb")
            hdf = h5py.File(f, mode = "w")
            dset = hdf.create_dataset(cls.datapath, obj.shape, dtype= obj.dtype, chunks = obj.chunksize)
            da.store(obj, dset)
            hdf.close()
            f.close()
        else:
            s3 = protocols[S3_PROTOCOL]
            root = cls.get_s3_root(s3)
            filename = generate_name()
            dset = root.create_dataset(filename, shape=obj.shape, chunks=obj.chunksize, dtype=obj.dtype)
            da.store(obj, dset)

        version = "0.0.0"
        return cls.name, (version, filename)
    
    @classmethod
    def unpickle(cls, pid, protocols: dict):
        _, filename = pid
        if FILE_PROTOCOL in protocols:
            file = protocols[FILE_PROTOCOL]
            f = file.open(filename, "rb")
            hdf = h5py.File(f, mode = "r")
            dset = hdf[cls.datapath]
        else:
            s3 = protocols[S3_PROTOCOL]
            root = cls.get_s3_root(s3)
            dset = root[filename]
        array = da.from_array(dset, chunks=dset.chunks)
        return array
    
    @classmethod
    def remove(cls, pid, protocols: dict):
        _, filename = pid
        if FILE_PROTOCOL in protocols:
            file = protocols[FILE_PROTOCOL]
            file.remove(filename)
        else:
            s3 = protocols[S3_PROTOCOL]
            client = s3["client"]
            file = posixpath.join(s3["folder"], cls.datapath, filename)
            s3.rm(file, recursive = True)

        return None