S3storage
##########

``S3Storage`` is the storage class to use when working with an S3 server.

Configuration options:

``path``: The path to the storage location with the S3 bucket. At this location, 
the ``S3Storage`` class creates an ``s3fs.S3FileSystem`` to store results. 
Workflow name and Node name are used by the backend as the file name to save 
to/read from.

``s3fs``: Configuration options for access to the S3 storage. Dictionary with 
fields:

    * ``endpoint_url``: URL location of the S3 server
    * ``key``: access key
    * ``secret``: secret key

Available Protocols:

* ``S3_PROTOCOL``

