Backends
#########

*Function Fuse* Backends specify how the DAG created in :ref:`background/introduction:The frontend` 
is executed. The DAG is defined by
`Nodes <https://github.ibm.com/vgurev/functionfuse/blob/0edcd9523f71a23cabb4e6b4ed5f6d7ab22937a7/functionfuse/workflow.py#L130>`_ 
(functions decorated with ``@workflow``) that reference each other's 
outputs as inputs. Workflow backends then operate on these Nodes to 
execute the graph of functions on configured infrastructure.

Basic Workflow Functionality
*****************************

The *BaseWorkflow* class is the parent class for all backends, and provides  
functions for backends to rely on:

``_find_roots()`` -- called when initializing a backend, given a set of *leaf*
nodes (i.e. output nodes of a DAG), ``_find_roots`` follows the chain of 
node inputs to find *root* nodes (i.e. input nodes to a DAG that do not have 
another node as an input).

``graph_traversal()`` -- traverses the DAG of nodes from the *root* nodes 
identified by ``_find_roots()``, yielding each node in turn. This function is 
the basis for executing each node using a backend.

``find_nodes(pattern)`` -- traverses the DAG and returns a list of nodes with names
matching the pattern provided.

Workflow Interface
*******************

Backends can perform any operations on the nodes yielded by 
``BaseWorkflow.graph_traversal()``. Typically, an interface should implement
at least two primary functions:

``set_storage()`` -- set a :ref:`storage/storage:Storage` class within the 
Workflow instance to be referenced during workflow execution

``run()`` -- call ``graph_traversal()`` and perform an operation on each node 
in the DAG, usually executing the node's ``func()``

Queries
--------

``Query()`` -- a backend may define a ``Query`` class that handles backend-specific 
assignment of information to the ``.backend_info`` field of individual Nodes. 
Typical implementation is that a ``Workflow.query("pattern")`` function is defined
that uses ``BaseWorkflow.find_nodes()`` to find a list of Nodes with names 
matching the pattern, which are assigned to a new ``Query`` object. Methods
of the ``Query`` class can then set specific items within the ``.backend_info`` 
field of the Nodes assigned to that ``Query`` object.

Plugins
--------

`Plugins <https://github.ibm.com/vgurev/functionfuse/blob/main/functionfuse/backends/plugins/baseplugins.py>`_
are additional functions that are executed for each node during DAG 
execution, prior to the node's main function call. Typical use includes state 
initialization on a remote machine (``InitializerPlugin``) and maintenance of 
random state across machines (``RandomStatePlugin``). We also implement 
``PluginCollection`` as a wrapper for multiple plugins.

Plugins implement two functions: ``local_initialize()`` and ``remote_initialize()``
that a backend can call at the appropriate time. For example, during graph 
traversal the RayWorkflow calls ``plugin.local_initialize()`` in the main 
process, then passes ``plugin.remote_initialize()`` as the plugin function to 
call as part of the remote function. The intention is that ``local_initialize`` 
can access information in the main process and help synchronize state, and that
information can be available to ``remote_initialize`` if required.

Workflows
**********

.. toctree::
   :maxdepth: 1
   :caption: Builtins:

   builtins/local
   builtins/ray

.. toctree::
   :maxdepth: 1
   :caption: Addons:

   addons/prefect
   addons/kfp
   addons/rayworkflow
