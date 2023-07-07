Serializers
############

*Function Fuse* Serializers specify how storage classes should handle 
serialization of node results for particular types of objects. The default 
serializer is ``pickle``. Serializers are registered with the storage object, 
e.g.:

.. highlight:: python
.. code-block::  python

   from functionfuse.storage import storage_factory
   from functionfuse.serializers.daskarray import DaskArraySerializer

   opt = {
      "kind": "file",
      "options": {
         "path": "storage"
      }
   }
   storage = storage_factory(opt)
   storage.register_persistent_serializers(DaskArraySerializer)

The registered serializers are then added to the pool of serializers 
for different object types that the storage class can call upon. To manage 
which objects are serialized by which registered serializers, serializers
have a ``serializer_class`` field that is registered to the storage. The 
``pickle()`` and ``unpickle()`` functions of the serializer will then be used 
in place of the defaults during the ``save()`` and ``read_task()`` functions of 
the storage, if the ``type`` of the object being saved matches the 
serializer's ``serializer_class`` field.

Protocols
----------

A key concept to aid the interface between storage classes and serializers is 
the concept of *protocols*. Currently 2 protocols are used across storage and 
serializers:

.. highlight:: python
.. code-block::  python

   from functionfuse.storage import storage_factory
   from functionfuse.serializers import FILE_PROTOCOL, S3_PROTOCOL

   FILE_PROTOCOL = "file_protocol"
   S3_PROTOCOL = "s3 protocol"

Protocols are essentially specified by a given type of storage, and the 
behavior of a serializer during ``pickle()`` and ``unpickle()`` can depend on 
the protocol specified by a class of storage. For example, currently the 
``DaskArraySerializer`` handles both ``FILE_PROTOCOL`` and ``S3_PROTOCOL``. If 
a storage class specifies pickling with ``FILE_PROTOCOL``, it will open an hdf5 
file, create a dataset for the passed object (Dask Array). Alternatively, if the 
storage class specifies pickling with ``S3_PROTOCOL``, it will connect to an S3
client, and store the object using an s3fs map in a zarr file. 

The actual protocols used to, for example, open a file or access an S3 server, 
are defined in the storage class, and the protocol variables are used as keys 
into a ``protocols`` dictionary that is accessed by the serializer and 
contains the interface the serializer will use during pickling (see 
:ref:`storage/storage:Storage`).

Serializer Classes
-------------------

.. toctree::
   :maxdepth: 1

   daskarray
