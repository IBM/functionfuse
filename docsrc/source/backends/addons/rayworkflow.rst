Ray Workflow Workflow
######################


The Ray Workflow Workflow is a backend for configuring a 
*FunctionFuse* workflow graph as a *Ray Workflow*, with each *FunctionFuse*
Node's main function run as a Node in the Ray Workflow DAG (see the 
`Ray Workflow documentation <https://docs.ray.io/en/latest/workflows/index.html>`_).

.. note::
    The Ray Workflow backend is completely separate from the 
    :ref:`backends/backends/Ray Backend`. The Ray Backend uses Ray remote task 
    calls directly within FunctionFuse Workflow Node execution. In contrast, 
    the Ray Workflow backend uses ``.bind()`` on each FunctionFuse Node during 
    graph traversal Ray to define a Ray Workflow DAG, and calls ``.run()`` at 
    the end of graph traversal

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

a Ray Workflow ``RayWorkflow`` can be instantiated, and ``run()`` will generate 
the Ray Workflow DAG and run the workflow:

.. highlight:: python
.. code-block::  python

    from functionfuse.backends.addons.rayworkflowback import RayWorkflow

    ray_workflow_workflow = RayWorkflow(a_plus_two_b, workflow_name="sums")
    c = ray_workflow_workflow.run()
