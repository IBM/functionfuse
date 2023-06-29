Kubeflow Pipelines Workflow
############################

.. note::
    NOT IMPLEMENTED

The KFP Workflow is a backend for configuring a *FunctionFuse* workflow graph 
as a *Kubeflow Pipeline*. In this implementation the code and requirements for 
the *FunctionFuse* will be packaged in a container, and then when the 
``KFPWorkflow`` is ``.run()`` the DAG will be created on within KFP with 
identical code for each Node, and Node's execution functions will be referened 
by environment variables or parameters passed to each Node. The intention is to 
prevent complex code being written into yaml files. Instead the code can be 
packaged in the contaier and small references to the requested functions can be
written into the yaml files. See the  
`Kubeflow Pipelines documentation <https://www.kubeflow.org/docs/components/pipelines/v2/>`_).
