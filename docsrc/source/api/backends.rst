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

.. highlight:: python
.. code-block::  python

    opt = {
            "kind": "file",
            "options": {
                "path": "path to folder for storage"
            }
    }

The name of the storage folder is path/workflow_name. This options returns object of the next class that is passed to :py:meth:`functionfuse.backends.builtin.localback.LocalWorkflow.set_storage`:

.. autoclass:: functionfuse.storage.filestorage.FileStorage
    :members: list_tasks, read_task, remove_task, remove_workflow


Example:

.. highlight:: python
.. code-block:: python

    local_workflow = LocalWorkflow(dataset, workflow_name="classifier")
    opt = {
        "kind": "file",
        "options": {
            "path": "storage"
        }
    }
    storage = storage_factory(opt)
    local_workflow.set_storage(storage)
    _ = local_workflow.run()



Ray Workflow
-------------

Ray Workflow interface is similar to `Local Workflow`_ with an addition of multiple methods to set Ray resources. 

.. autoclass:: functionfuse.backends.builtin.rayback.RayWorkflow
    :members: run, set_storage, query

.. autoclass:: functionfuse.backends.builtin.rayback.Query
    :members: set_remote_args


Example:

.. highlight:: python
.. code-block:: python

    ray_init_args = {
        "resources": {"_disk": 1.0, "_model": 1}
    }

    ray_storage_remote_args = {
        "resources": {"_disk": 0.001}
    }

    ray_workflow = RayWorkflow(dataset, workflow_name="classifier", ray_init_args=ray_init_args)

    # Ray init is called in the RayWorkflow constructor!!! Storage should be created AFTER RayWorkflow is created. 
    storage_path = os.path.join(os.getcwd(), "storage")
    opt = {
        "kind": "ray",
        "options": {
            "remoteArgs": ray_storage_remote_args,
            "path": storage_path,
        }
    }

    storage = storage_factory(opt)
    ray_workflow.set_storage(storage)
    ray_workflow.query(pattern="^model$").set_remote_args({"num_cpus": 1, "resources": {"_model": 1}})

    _ = ray_workflow.run()

