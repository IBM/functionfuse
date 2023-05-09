Backends
#########

Built-in
*********

Local Workflow
---------------

The Local Workflow are implemented with a class and a function to create local storage (see below). 
During graph execution all node results are saved in the storage. 
In the second run, all saved nodes are not executed but their results are loaded from the storage. 

.. autoclass:: functionfuse.backends.builtin.localback.LocalWorkflow
    :members: run, set_storage


.. autofunction:: functionfuse.storage.storage_factory

Options for local storage is 

.. code-block::  python

    opt = {
            "kind": "file",
            "options": {
                "path": "path to folder for storage"
            }
    }

The name of the storage folder is path/workflow_name. This options returns object of the next class that is passed to :py:meth:`functionfuse.backends.builtin.localback.LocalWorkflow.set_storage`:

.. autoclass:: functionfuse.storage.filestorage.FileStorage
    :members: list_tasks, read_tasks, remove_task, remove_workflow


Ray Workflow
-------------

Ray Workflow interface is similar to :ref:`Local Workflow` with an addition of multiple methods to set Ray resources. 



