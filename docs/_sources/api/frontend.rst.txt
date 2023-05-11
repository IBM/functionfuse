Frontend
=========

The frontend employs a single decorator for user functions 

.. autofunction:: functionfuse.workflow


Nodes created with calls of decorated user functions have a method **set_name**:

.. py:function:: set_name(name)

   Return a list of random ingredients as strings.

   :param name: Name of the node to set.
   :type name: str
   :return: The node that is named.


An example code:

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

The variables a_plus_b, a_plus_two_b, and result_of_mult contains references to the nodes. To run the DAG use one of the backends.
