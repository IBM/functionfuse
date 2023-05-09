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
* Frontend layer: workflow is defined with a single Python decorator and capability to set DAG node names (the code is developed by research scientists).
* Backend layer: query nodes by their names, edit the pipeline, assign resources to nodes, etc. (developed and deployed by SWE).

Benefits:

* Simple for development (separation of research-SWE code). 
* Extreme flexibility. The same workflow could be extended to multiple backends.
* Pipeline editing: dynamic insertion of the nodes, node collapsing, etc.
* Plugins: intialization of environment before execution of DAG nodes such as initialization of random number generator in parallel execution


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

The variables a_plus_b, a_plus_two_b, and result_of_mult contains references to the nodes. To run the DAG, we need one of the backends.



Backends
*********************

Backends take as an input one or several nodes of the graph and run the workflow. 
There are two types of backends, built-in and addons. 
Two built-in backends to Function Fuse package are designed to run workflow in-serial and in-parallel with `Ray <https://www.ray.io/>`_, these are :ref:`api/backends:Local Workflow` and Ray Workflow. 
For addons, I currently implemented only one backend - Ray Workflow backend.