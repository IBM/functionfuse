Big Data Modeling
##################

Very large arrays pose a problem for portability of data science workflows, as 
problems can easily arise around transmitting, storing, loading, and working 
with large data when moving code to new infrastructure. In such cases, 
solutions may need to be tailored to the specifics of the targeted platform.

A typical problem encountered is an Out-of-Memory error, where either a data
array is so large that it does not fit into the memory of an individual machine, 
or a memory-intensive sequence of operations must be performed. Existing 
solutions to these types of problems include software like 
`Apache Hadoop <https://hadoop.apache.org/>`_, which 
utilizes distributed file systems for working with data across multiple machines. 
Data is then processed using a MapReduce programming model, where chunks of 
data are mapped to individual machines or processes in a cluster, and combined 
(reduced) back to the distributed file system after independent processing.

`Dask <https://docs.dask.org/en/stable/>`_ is a Python-specific library for data 
science processing that includes features analoguous to systems like Hadoop. The 
fundamental interface is the 
`Dask Array <https://docs.dask.org/en/stable/array.html>`_, which arranges a 
very large array into chunks, where each chunk is an individual numpy array. 
Dask Arrays implement a subset of numpy array interfaces and perform computations
in parallel using blocked algorithms, and handle larger-than-memory scenarios. 
In general, Dask makes computations efficient by performing lazy evaluation of 
operations, returning ``Delayed`` objects when array operations are called, 
meaning that arrays don't need to be loaded from a distributed storage on every
function call, but instead only when the full computation graph has been 
specified and needs to be computed.

The use of chunked arrays and lazy operations allows Dask to operate on arrays 
stored in distributed and chunked file storage. HDF5 and Zarr file formats are 
both supported by Dask.

To facilitate working with large data sets within *FunctionFuse*, we introduced 
the concept of :ref:`serializers/serializers:Serializers` to 
:ref:`storage/storage:Storage` objects. The purpose of a serializer is to 
define an interface for serializing and deserializing a specific type of object. 
For example, the serializer written for Dask Array objects writes the Dask 
Array to an HDF5 file on local storage, or a Zarr file on S3 storage.
