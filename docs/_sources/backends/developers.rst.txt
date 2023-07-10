Backend Development
********************

*Function Fuse* backends need to define how the DAG specified by the frontend
will be executed. We recommend that developers of a new backend first 
familiarize themselves with the source code for the 
`Local Backend <https://github.ibm.com/vgurev/functionfuse/blob/main/functionfuse/backends/builtin/localback.py>`_, 
then with the 
`Ray Backend <https://github.ibm.com/vgurev/functionfuse/blob/main/functionfuse/backends/builtin/rayback.py>`_ 
for an example based on asynchronous processing with futures.

Some of the basic functions and interfaces used by all of the backends are 
introduced below.

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

Storage
--------

Backends that interface with :ref:`storage/storage:Storage` should provide the 
option to add the Storage class to a Workflow instance using the 
``set_storage()`` function. The backend can make use of functions in the 
Storage class for checking and searching storage, such as ``list_tasks()`` and
``file_exists()``. The standard function for saving a node is ``save()``, and 
for loading results from a stored node is ``read_task()``. See LocalWorkflow 
and RayWorkflow backend source code for examples of using file storage locally
compared with file storage on a remote machine accessed in a setting using 
futures for asynchronous computation.
