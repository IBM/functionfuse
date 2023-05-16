Introduction and quick start
###############################

The package *Function Fuse* is designed to build 
programming workflows in the form of direct acyclic 
graphs (DAG). The nodes of the DAG are functions defined by a user. 
The programming model of *Function Fuse* is inspired by `CodeFlare <https://github.com/project-codeflare/codeflare>`_, which is now a part of Ray.io (`Ray Workflows <https://docs.ray.io/en/latest/workflows/index.html>`_). 

.. note::
    It is strongly recommended to become familiar with Ray Workflows to accelerate the learning curve for *Function Fuse*.


Why another workflow package
*****************************

There are hundreds of workflow packages out there (see `this repo <https://github.com/meirwah/awesome-workflow-engines>`_ for instance for a list). 
Our goal is to create the simplest workflow package that could be used by research scientists and machine learning engineers without a heavy background in software engineering. 
To make workflow simple, we follow next concepts:

* Split workflow engines into frontend-backend layers.
* The frontend layer: workflow is defined with a single Python decorator and capability to set DAG node names (the code is developed by research scientists).
* Backend layers: query nodes by their names, edit the pipeline, assign resources to nodes, etc. (developed and deployed by SWE).

Benefits:

* Simple for development (separation of research-SWE code). 
* Extreme flexibility. The same workflow could be extended to multiple backends.
* Pipeline editing: dynamic insertion of the nodes, node collapsing, etc. by backends.
* Plugins: intialization of environment before execution of DAG nodes by backends such as initialization of random number generator in parallel execution.
* Cloud engine backends.


The frontend
*************

Only two directives are implemented in the frontend:

* @workflow decorator for user functions.
* set_name function that assigns a name to a node of the DAG.


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

To make stateful nodes, we apply @workflow decorator to classes. Nodes can be arguments of constructors and methods of decorated clasess:

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

Note that edges between methods of the same class instance are generated automatically to produce a chain of sequentially called methods.

To run DAGs, we need one of the backends.



Backends
*********************

Backends take as an input one or several nodes of the graph and run the workflow. 
There are two types of backends, built-in and addons. 
Two built-in backends to Function Fuse package are designed to run workflow in-serial and in-parallel with `Ray <https://www.ray.io/>`_, these are :ref:`api/backends:Local Workflow` and :ref:`api/backends:Ray Workflow`. 
For addons, I currently implemented only one backend - CodeFlare, also with name Ray Workflow, and we are developing backend for `KubeFlow <https://www.kubeflow.org/>`_. 
Backends classes typically take workflow name to use in the data storage class. Here is an example of backend setup and run for the above workflow.

.. highlight:: python
.. code-block:: python

    from functionfuse.backends.builtin.localback import LocalWorkflow
    from functionfuse.storage import storage_factory

    local_workflow = LocalWorkflow(node1, workflow_name="operations")
    opt = {
        "kind": "file",
        "options": {
            "path": "storage"
        }
    }
    storage = storage_factory(opt)
    local_workflow.set_storage(storage)
    _ = local_workflow.run()



Model analysis and visualization
*********************************

The workflows are used to prepare data and to train ML models. Further analysis and visualization are performed in Jupyter Notebooks.
We read results of node execution from the storage, run model on testing data and create pictures. 
To read the data, we create the same storage object in a notebook:

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

list_tasks returns the list of node names. To read specific saved node results (task):

.. highlight:: python
.. code-block:: python

    nodel_result = storage.read_task(workflow_name=the_workflow_name, task_name="node2")


Queries
********

CodeFlare and other workflow packages assign different attributes to nodes of DAGs. 
For instance, CodeFlare set Ray resources for execution of functions remotely. 
However, the frontend does not support such functionality. Instead, I propose to set attributes in the backend. 
In the backend, we query nodes by their names, assign different attributes and perform operations on nodes. 
An example is setting resources for :ref:`api/backends:Ray Workflow` backend:

.. code-block:: python

    ray_workflow.query(pattern="^model$").set_remote_args({"num_cpus": 1, "resources": {"_model": 1}})

Here, we query nodes using RegExp pattern and assing resources to all nodes that match the pattern.
