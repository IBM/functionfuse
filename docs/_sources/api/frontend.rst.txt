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

The variables a_plus_b, a_plus_two_b, and result_of_mult contains references to the nodes. 

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

To run the DAG use one of the backends.
