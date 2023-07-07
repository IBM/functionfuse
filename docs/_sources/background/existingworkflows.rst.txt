Integration with existing workflow packages
############################################

There are many existing packages for managing workflows and pipelines that 
interface with python code in various different ways. A major strength of 
*FunctionFuse* is the ability touse identical frontend code across any backend. 
Leveraging the functionality of different workflow packages is possible by writing 
*Add-on* backends that interpret the DAG of Nodes described in the *FunctionFuse* 
frontend in terms of another workflow package.

Current Add-on backends:

* :ref:`backends/addons/kfp:Kubeflow Pipelines Workflow`
* :ref:`backends/addons/prefect:Prefect Workflow`
* :ref:`backends/addons/rayworkflow:Ray Workflow Workflow`
