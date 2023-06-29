LocalWorkflow
##############

The :ref:`api/backends:Local Workflow` is a backend for executing the functions 
within a workflow graph locally and in serial in the current Python process. 

The simplest way to test a frontend-defined workflow is to declare a 
`LocalWorkflow`, and call `run()`:

.. highlight:: python
.. code-block::  python

    from functionfuse import workflow

    @workflow
    def sum(a, b):
        return a + b

    a, b = 1, 1

    a_plus_b = sum(a, b).set_name("node1")
    a_plus_two_b = sum(a_plus_b, b).set_name("node2")

    from functionfuse.backends.builtin.localback import LocalWorkflow

    local_workflow = LocalWorkflow(node1, workflow_name="sums")
    c = local_workflow.run()

Any :ref:`storage/storage:Storage` class can be added to a `LocalWorkflow`
using `set_storage()`:

.. highlight:: python
.. code-block::  python

    from functionfuse.storage import storage_factory

    opt = {
        "kind": "file",
        "options": {
            "path": "storage"
        }
    }
    storage = storage_factory(opt)
    local_workflow.set_storage(storage)

`LocalWorkflow.run()` uses the `save()`, `read_task()`, and `always_read` 
properties of :ref:`storage/storage:Storage`, so any Storage class 
implementing those functions can be attached.
