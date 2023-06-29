DaskArraySerializer
####################

The ``DaskArraySerializer`` is designed to serialize Dask Arrays to appropriate
file types (hdf5 for local files, or zarr on s3 storage).

.. highlight:: python
.. code-block::  python

    from dask.array.core import Array

    class DaskArraySerializer

        serializer_class = Array

Accepted :ref:`serializers/serializers:Protocols` are ``FILE_PROTOCOL`` and 
``S3_PROTOCOL``. 

File protocol interface
------------------------

The file protocol used by ``DaskArraySerializer`` requires an ``open()`` function
that can be used as in the default python ``open()``.

.. highlight:: python
.. code-block::  python


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

    def unpickle(cls, pid, protocols: dict):
        _, filename = pid
        if FILE_PROTOCOL in protocols:
            file = protocols[FILE_PROTOCOL]
            f = file.open(filename, "rb")
            hdf = h5py.File(f, mode = "r")
            dset = hdf[cls.datapath]

S3 protocol interface
------------------------

The S3 protocol used by ``DaskArraySerializer`` requires a dictionary with 
"client" and "folder" keys. The "client" value should have the S3FileSystem 
interface as in ``s3fs.S3FileSystem``. The "folder" value 

.. highlight:: python
.. code-block::  python


    def pickle(cls, obj : Array, protocols : dict):

        if S3_PROTOCOL in protocols:
            s3 = protocols[S3_PROTOCOL]
            root = cls.get_s3_root(s3)
            filename = generate_name()
            dset = root.create_dataset(filename, shape=obj.shape, chunks=obj.chunksize, dtype=obj.dtype)
            da.store(obj, dset)

    def unpickle(cls, pid, protocols: dict):
        _, filename = pid
        if S3_PROTOCOL in protocols:
            s3 = protocols[S3_PROTOCOL]
            root = cls.get_s3_root(s3)
            dset = root[filename]

    def get_s3_root(cls, s3):
        client = s3["client"]
        folder = posixpath.join(s3["folder"], cls.datapath)
        store = s3fs.S3Map(root=folder, s3=client, check=False)
        root = zarr.group(store=store)
        return root
        