Introduction and quick start
###############################

The package *Function Fuse* is designed to build 
programming workflows in the form of direct acyclic 
graphs (DAG). The nodes of the DAG are functions defined by a user. 
The programming model of *Function Fuse* is inspired by `CodeFlare <https://github.com/project-codeflare/codeflare>`_, 
which is now a part of Ray.io (`Ray Workflows <https://docs.ray.io/en/latest/workflows/index.html>`_). 

.. note::
    It is strongly recommended to become familiar with Ray Workflows to accelerate the learning curve for *Function Fuse*.


Why another workflow package
*****************************

There are hundreds of workflow packages out there (see 
`this repo <https://github.com/meirwah/awesome-workflow-engines>`_ for instance for a list). 
Our goal is to create the simplest workflow package that could be used by 
research scientists and machine learning engineers without a heavy background 
in software engineering. 
To make workflows simple, we follow these concepts:

*   Split workflow engines into seperated frontend and backend layers.
*   The frontend layer: the workflow is defined with a single Python decorator 
    and the capability to set DAG node names (the main code used in the workflow
    is developed by research scientists).
*   Backend layers: query nodes by their names, edit the pipeline, assign resources 
    to nodes, etc. (developed and deployed by Software Engineers (SWEs)).

Benefits:

*   Simple for development (separation of research-SWE code).
*   Extreme flexibility. The exact same workflow code can be run using multiple backends.
*   Pipeline editing: dynamic insertion of the nodes, node collapsing, etc. by backends.
*   Plugins: intialization of environment before execution of DAG nodes by backends 
    such as initialization of random number generator during parallel and distributed execution.
*   Cloud engine backends.


The frontend
*************

Only two directives are implemented in the frontend:

* ``@workflow`` decorator for user functions (alias ``@task`` can also be used).
* ``set_name()`` function that assigns a name to a node of the DAG.


.. code-block:: python

    from functionfuse import workflow

    @workflow
    def sum(a, b):
        return a + b


    @workflow
    def multiply(a, b):
        return a * b


    a, b = 1, 1

    a_plus_b = sum(a, b).set_name("node1")
    a_plus_two_b = sum(a_plus_b, b).set_name("node2")
    result_of_mult = multiply(a_plus_b, a_plus_two_b).set_name("node3")

The above code defines a graph with 3 nodes: **node1**, **node2**, **node3**:

.. graphviz::

   digraph {
      "node1" -> "node2" -> "node3";
      "node1" -> "node3"
   }

The variables a_plus_b, a_plus_two_b, and result_of_mult contain references to the nodes. 

To make stateful nodes, we apply the ``@workflow`` decorator to classes. Nodes 
can be arguments of constructors and methods of decorated clasess:

.. code-block:: python

    from functionfuse import workflow

    @workflow
    class IncrementalSum:
        def __init__(self, start):
            self.start = start

        def add(self, n):
            self.start += n
            return self.start
    
    @workflow
    def minus(a, b):
        return a - b


    one = minus(4, 3).set_name("four_minus_three")
    incremental_sum = IncrementalSum(start = one).set_name("IncrementalSum")
    
    two = minus(3, one).set_name("three_minus_one")
    incremental_sum.add(two).set_name("one_plus_two")
    incremental_sum.add(two).set_name("three_plus_two")
    six = incremental_sum.add(one).set_name("five_plus_one")
    result = minus(six, 2).set_name("six_minus_two")


The above code defines a graph with 7 nodes: 

.. graphviz::

   digraph {
      "four_minus_three" -> "IncrementalSum";
      "four_minus_three" -> "five_plus_one";
      "IncrementalSum" -> "one_plus_two" -> "three_plus_two" -> "five_plus_one" -> "six_minus_two";
      "four_minus_three" -> "three_minus_one";
      "three_minus_one" -> "one_plus_two";
      "three_minus_one" -> "three_plus_two"
   }

Note that edges between methods of the same class instance are generated automatically 
to produce a chain of sequentially called methods.

To run a DAG, we need one of the backends.



Backends
*********************

Backends take as an input one or several nodes of the graph and run the workflow. 

There are two types of backends, built-in and addons. Built-ins are implemented 
entirely in the Function Fuse package, whereas addons leverage other existing 
packages that might help manage or run workflows.

Two built-in backends to Function Fuse package are designed to run workflow 
in-serial locally (:ref:`api/backends:Local Workflow`), or in-parallel with `Ray <https://www.ray.io/>`_ 
(:ref:`api/backends:Ray Workflow`). 

There are currently 3 addon backends. :ref:`api/backends:KFP Workflow` uses the 
`KubeflowPipelines <https://www.kubeflow.org/docs/components/pipelines/v1/sdk/python-function-components/>`_ 
SDK to deploy a Function Fuse DAG to run Nodes in containers on a 
Kubernetes/OpenShift cluster. :ref:`api/backends:Prefect Workflow` uses the 
`Prefect <https://docs.prefect.io/2.10.18/>`_ python ecosystem to orchestrate 
running the workflow, and is an example
of interfacing Function Fuse with a popular existing workflow package that 
provides a variety of different options out of the box that could be useful for 
users of Function Fuse. :ref:`backends/addons/rayworkflow:Ray Workflow Workflow` 
uses the Workflow components of the Ray (CodeFlare) package directly. 
These addon backends are all in an alpha stage of development.

Backends classes typically take workflow name to use in the data storage class. 
Here is an example of backend setup and run for the above workflow.

.. highlight:: python
.. code-block:: python

    from functionfuse.backends.builtin.localback import LocalWorkflow
    from functionfuse.storage import storage_factory

    local_workflow = LocalWorkflow(result_of_mult, workflow_name="operations")
    opt = {
        "kind": "file",
        "options": {
            "path": "storage"
        }
    }
    storage = storage_factory(opt)
    local_workflow.set_storage(storage)
    _ = local_workflow.run()

Addon backends can provide access to any features of existing packages, such as 
systems for tracking previous workflows and runs, and interactive dashboards - 
the images below show the same frontend run in the dashboards for Kubeflow 
(left) and Prefect (right):

.. image:: /images/KFPDashboardRunResult.png
    :alt: KFPWorkflow Dashboard
    :width: 450

.. image:: /images/PrefectBasicRun.png
    :alt: PrefectWorkflow Dashboard
    :width: 450


Graph visualization
--------------------

Backends can potentially be used for visualization and analysis - we have 
implemented one example of a backend for visualizing the Nodes in a DAG:

.. highlight:: python
.. code-block:: python

    from functionfuse.backends.builtin.graphback import GraphWorkflow

    graph_workflow = GraphWorkflow(result_of_mult, 
                                   workflow_name="plot_graph", 
                                   doc_path='.')
    graph_workflow.run()

.. image:: /images/GraphWorkflow.png
    :alt: Graph Workflow example
    :width: 100

Storage and Analysis
*********************************

The workflows are used to prepare data and to train ML models. Further analysis 
and visualization can be performed in Jupyter Notebooks by loading workflow results.
We read results of node execution from the storage, and can run the trained models 
on testing data and create pictures. 

To read the data, we recreate the same storage object in a notebook:

.. highlight:: python
.. code-block:: python

    from functionfuse.storage import storage_factory

    the_workflow_name = "classifier"
    storage_path = "storage"
    opt = {
        "kind": "file",
        "options": {
            "path": storage_path
        }
    }
    storage = storage_factory(opt)

To list existing saved node results: 

.. highlight:: python
.. code-block:: python

    all_tasks = storage.list_tasks(workflow_name=the_workflow_name, pattern="*")
    print("All graph node names: ", all_tasks)

``list_tasks`` returns the list of node names. To read specific saved node results (task):

.. highlight:: python
.. code-block:: python

    nodel_result = storage.read_task(workflow_name=the_workflow_name, task_name="node2")


Queries
********

CodeFlare and other workflow packages assign different attributes to nodes of DAGs. 
For instance, CodeFlare sets Ray resources for execution of functions remotely. 
However, the frontend does not support such functionality. Instead, attributes 
of nodes are set in the backend. 
In the backend, we query nodes by their names, assign different attributes and 
perform operations on selected nodes. 
An example is setting resources for :ref:`api/backends:Ray Workflow` backend:

.. code-block:: python

    ray_workflow.query(pattern="^model$").set_remote_args({"num_cpus": 1, "resources": {"_model": 1}})

Here, we query nodes using RegExp pattern and assing resources to all nodes that match the pattern.

Serializers
************

Backends can make use of different types of storage, including local file systems, 
storage assigned to specific remote machines in a Ray server using Ray custom 
resources, or we have implemented access to S3 storage. Certain types of object 
might require different methods of serialization and deserialization. For that, 
we have included the ability to add custom :ref:`serializers/serializers:Serializers` 
to backend storage. For example, currently we have implemented a 
serializer for `Dask Arrays <https://docs.dask.org/en/stable/array.html>`_ that 
facilitates access to large arrays using distributed files such as HDF5 or Zarr.
