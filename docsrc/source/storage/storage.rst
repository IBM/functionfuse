Storage
########

*Function Fuse* Storage classes define how the results produced by Nodes 
are stored. All Workflows can have a Storage class attached using the 
``set_storage()`` method. We use the ``storage_factory`` to instantiate 
a storage object from a configuration dictionary, with "kind" key 
indicating the storage class to use, and "options" providing class-specific
options:

.. highlight:: python
.. code-block:: python

    from functionfuse.storage import storage_factory

    opt = {
        "kind": "file",
        "options": {
            "path": "storage"
        }
    }

    storage = storage_factory(opt)

The basic template for using a storage object looks as follows:

.. highlight:: python
.. code-block:: python

    from functionfuse.backends.builtin.localback import LocalWorkflow

    the_workflow_name = "operations"
    local_workflow = LocalWorkflow(node1, workflow_name=the_workflow_name)

    local_workflow.set_storage(storage)
    _ = local_workflow.run()

This will set the ``FileStorage`` object declared above into the 
``LocalWorkflow`` and the combination of the backend and the storage 
dictate how and where node outputs are saved.

After running a workflow, instantiating a storage class with identical options
will provide access to list and read task results from storage:

.. highlight:: python
.. code-block:: python

    from functionfuse.storage import storage_factory

    opt = {
        "kind": "file",
        "options": {
            "path": "storage"
        }
    }

    storage = storage_factory(opt)
    all_tasks = storage.list_tasks(workflow_name=the_workflow_name, pattern="*")
    print("All graph node names: ", all_tasks)

    node2_result = storage.read_task(workflow_name=the_workflow_name, task_name="node2")

Serializers
------------

Storage can utilize :ref:`serializers/serializers:Serializers` attached 
to the storage object. The intention of serializers is to be able to flexibly 
assign custom serialization approaches for certain types of objects to any 
storage object. For example, to utilize custom serialization of dask arrays to 
hdf5 files (rather than using pickle to dump to file), register the 
:ref:`serializers/daskarray:DaskArraySerializer`:

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



Protocols
----------

Different storage classes may use different :ref:`serializers/serializers:protocols` 
for opening, reading to, and writing from files. To make serializers, and other 
functions that might want to interface with a storage object, aware of the 
protocols a storage class uses, each storage class implements a ``protocols`` 
dictionary that is passed to the ``pickle`` and ``unpickle`` functions used by 
serializers. Currently there are 2 default keys used by this dictionary 
(``FILE_PROTOCOL``, ``S3_PROTOCOL``) that custom pickle functions can reference 
for how to access the file protocols used by the storage class.

Storage Classes
----------------

.. toctree::
   :maxdepth: 1

   filestorage
   rayfilestorage
   s3storage
