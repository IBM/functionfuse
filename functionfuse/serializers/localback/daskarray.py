from .base import generate_name
from dask.array.core import Array
import dask.array as da
import h5py
import os

DATAPATH = "/data"

def _write(obj : Array, filename : str):
    obj.to_hdf5(filename, DATAPATH, chunks = True)


class HDFSerializer:

    serializer_class = Array
    ext = "hdf5"

    def __init__(self, path, node_name):
        self.path, self.node_name = path, node_name

    @classmethod
    def state(cls, obj):
        return {}
    
    def reduce(self, obj):
        filename = os.path.join(self.path, self.node_name+generate_name(self.ext))
        _write(obj, filename)
        return (self.call, (filename,))

    @classmethod
    def call(cls, filename):
        f = h5py.File(filename)
        save_object = f[DATAPATH]
        return da.from_array(save_object, chunks=save_object.chunks)



    


