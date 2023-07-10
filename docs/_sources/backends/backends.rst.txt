Backends
#########

*Function Fuse* Backends specify how the DAG created in :ref:`background/introduction:The frontend` 
is executed. The DAG is defined by
`Nodes <https://github.ibm.com/vgurev/functionfuse/blob/0edcd9523f71a23cabb4e6b4ed5f6d7ab22937a7/functionfuse/workflow.py#L130>`_ 
(functions decorated with ``@workflow``) that reference each other's 
outputs as inputs. Workflow backends then operate on these Nodes to 
execute the graph of functions on configured infrastructure.

In :ref:`backends/backends:Workflows` we provide users of Function Fuse backends with information 
about the features of currently implemented "builtin" and "addon" backends. 

In :ref:`backends/backends:For Backend Developers`, we provide developers
basic information about how backends are executing the DAG specified by the 
frontend, as a starting point for implementation of new backends. 

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

For Backend Developers
***********************

.. toctree::
   :maxdepth: 1

   developers
