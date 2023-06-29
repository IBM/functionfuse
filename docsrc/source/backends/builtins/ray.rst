RayWorkflow
##############

The :ref:`api/backends:Ray Workflow` is a backend for executing the functions 
within a workflow graph on a Ray cluster, which is a framework for scaling 
and parallelizing python applications (see the 
`Ray documentation <https://docs.ray.io/en/latest/ray-core/walkthrough.html>`_).

After declaring a frontend-defined workflow, e.g.:

.. highlight:: python
.. code-block::  python

    from functionfuse import workflow

    @workflow
    def sum(a, b):
        return a + b

    a, b = 1, 1

    a_plus_b = sum(a, b).set_name("node1")
    a_plus_two_b = sum(a_plus_b, b).set_name("node2")

a ``RayWorkflow`` can be instantiated, and calling `run()` will initialize a 
local Ray cluster with default settings:

.. highlight:: python
.. code-block::  python

    from functionfuse.backends.builtin.rayback import RayWorkflow

    ray_workflow = RayWorkflow(a_plus_two_b, workflow_name="sums")
    c = ray_workflow.run()

Ray cluster options
--------------------

Usually the ``RayWorkflow`` will target an existing Ray cluster, and/or define a 
set of initialization options to use with ``ray.init()``. These are passed to the 
``RayWorkflow`` using ``ray_init_args``:

.. highlight:: python
.. code-block::  python

    from functionfuse.backends.builtin.rayback import RayWorkflow

    ray_options = {
        "address": "ray://localhost:10001",
        "ignore_reinit_error": True,
        "runtime_env": {"working_dir": "."}
    }

    ray_workflow = RayWorkflow(a_plus_two_b, workflow_name="sums", ray_init_args=ray_options)
    c = ray_workflow.run()

See the `ray.init API <https://docs.ray.io/en/latest/ray-core/api/doc/ray.init.html>`_
for all available options.

Ray remote task options
------------------------

The functions assigned to nodes in the workflow graph are executed as 
`Ray remote tasks <https://docs.ray.io/en/latest/ray-core/tasks.html#ray-remote-functions>`_,
which can be assigned individual task-specific options and resources within Ray. 
Specific options are assigned to the ``.backend_info`` field of each node using 
`:ref:background/introduction:Queries` through the ``Query.set_remote_args()`` 
function:

.. highlight:: python
.. code-block::  python

    node1_remote_args = {"num_cpus": 1}
    node2_remote_args = {"resources": {"custom_resource": 0.1}}
    ray_workflow.query("^.*node1.*$").set_remote_args(node1_remote_args)
    ray_workflow.query("^.*node2.*$").set_remote_args(node2_remote_args)

    c = ray_workflow.run()

See the `ray.remote API <https://docs.ray.io/en/latest/ray-core/api/doc/ray.remote_function.RemoteFunction.options.html#ray.remote_function.RemoteFunction.options>`_
for all available options.

Plugins
--------

Ray tasks are usually run in a distributed environment across multiple machines
in a Ray cluster. The state of the process on a remote machine may need 
some configuration prior to execution of a node. Common scenarios for this 
include global setting of package features, or synchronizing states like random
number generators. `:ref:backends/backends:Plugins` (and collections of plugins) 
can be assigned to nodes through the ``Query.set_plugins()`` function:

.. highlight:: python
.. code-block::  python

    from functionfuse.backends.plugins import PluginCollection, InitializerPlugin, RandomStatePlugin

    def init_float():
        import torch
        torch.set_default_dtype(torch.float64)
    
    def set_seed(seed):
        import torch
        torch.random.manual_seed(seed)
        print(torch.rand(1))

    random_state_plugin = RandomStatePlugin(min= -0x8000_0000_0000_0000, max= 0xffff_ffff_ffff_ffff, seed = -0x8000_0000_0000_0000, seed_func= set_seed)
    initializer_plugin = InitializerPlugin(init_float)
    plugin_collection = PluginCollection([initializer_plugin, random_state_plugin])

    ray_workflow.query("^.*node1.*$").set_plugins(initializer_plugin)
    ray_workflow.query("^.*node2.*$").set_plugins(plugin_collection)

    c = ray_workflow.run()

Storage
--------

The main storage class for a ``RayWorkflow`` is in rayfilestorage, and is 
attached using `set_storage()`. The typical way to use this Ray version of 
FileStorage is to specify a custom resource type in the ray remote arguments 
to ensures that save and load functions are processed on a machine with 
appropriate attached storage within a distributed cluster. 

.. highlight:: python
.. code-block::  python

    from functionfuse.storage import storage_factory

    ray_storage_remote_args = {
        "resources": {"_disk": 0.001}
    }

    store_config = {
        "kind": "ray",
        "options": {
            "remoteArgs": ray_storage_remote_args,
            "path": "storage"
        }
    }

    storage = storage_factory(opt)
    ray_workflow.set_storage(storage)

``RayWorkflow.run()`` uses the ``get_writer_funcs()`` to assign Storage class 
functions to a ``save_func`` used to queue up Ray save commands, and uses 
the ``read_task()`` property of the ``read_object`` returned by 
``get_writer_funcs()`` of :ref:`storage/storage:Storage`, so any attached 
Storage class needs to implement those functions.
