IBM Research Cloud
###################

The iRIS-IMS IaaS platform on IBM Research Cloud provides access to cloud-based 
VMs through a REST API. We are using a set of python scripts that interface 
with this API to start a cluster of VMs providing CPU resources for a Ray 
cluster that can be accessed by the RayWorkflow backend to run *FunctionFuse* 
workflows.

Tutorial
*********

1. Clone ``irisraycloud`` git repository:

.. code-block:: sh

    git clone git@github.ibm.com:vgurev/irisraycloud.git

2. Follow the `instructions <https://github.ibm.com/vgurev/irisraycloud#readme>`_ to:
    a. Prepare docker image with ``ray[default]``
    b. generate SSH keys
    c. update ``cluster.yaml``
    d. write ``secret.yaml``

3. Obtain iRIS-IMS API token from `the website <https://ocp-draco.bx.cloud9.ibm.com/iaas>`_:

.. image:: /images/iris-portal-access-token.png
    :alt: iRIS portal access token

4. `Start the cluster <https://github.ibm.com/vgurev/irisraycloud#manage-cluster>`_:

.. code-block:: sh

    python iris.py up --input cluster.yaml --secret secrets.yaml
    python iris.py secure
    python iris.py provision
    python iris.py deploy

S3 Storage Node Tutorial
*************************


