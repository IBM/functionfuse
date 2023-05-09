Introduction
############

The package *Function Fuse* is designed to build 
programming workflows in the form of direct acyclic 
graphs (DAG). The nodes of the DAG are functions defined by a user. 
The programming model of *Function Fuse* is inspired by `CodeFlare <https://github.com/project-codeflare/codeflare>`_, which is now a part of Ray.io (`Ray Workflows <https://docs.ray.io/en/latest/workflows/index.html>`_). 

.. note::
    It is strongly recommended to become familiar with Ray Workflows to accelerate the learning curve for *Function Fuse*.


Why another workflow package
*****************************

There are hundreds of workflow packages out there (for instance, see `this repo <https://github.com/meirwah/awesome-workflow-engines>`_). 
Our goal is to create the simplest workflow package that could be used by research scientists and machine learning engineers without a heavy background in software engineering. 
To make workflow simple, we follow next concepts:

* Split workflow engines into frontend-backend layers.
* Frontend layer: workflow is defined with a single Python decorator and capability to set DAG node names (the code is developed by research scientists).
* Backend: query nodes by their names, edit the pipeline, assign resources to nodes, etc. (developed and deployed by SWE).

Benefits:

* Simple for development (separation of research-SWE code). 
* Extreme flexibility. The same workflow could be extended to multiple backends.
* Pipeline editing: dynamic insertion of the nodes, node collapsing, etc.


Frontend
**********

Only two directives are implemented in the frontend:

* @workflow decorator for user functions.
* set_name function that assigns a name to a node of the DAG.




Programming paradigm
*********************

Unlike 