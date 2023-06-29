FileStorage
############

``FileStorage`` is the default storage class for writing node outputs to files.

Configuration options:

``path``: The path to the base storage location. Inside this folder, 
the workflow name is used as a subdirectory, and a node's name is used by the 
backend as the file name to save to/read from.

Available Protocols:

* ``FILE_PROTOCOL``
