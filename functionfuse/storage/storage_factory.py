def storage_factory(opt):
    """
    Factory that creates a storage class.

    :param opt: Dictionary with parameters of the storage class

    """
    if opt["kind"] == "file":
        from .filestorage import FileStorage

        return FileStorage(opt["options"]["path"])

    if opt["kind"] == "ray":
        from .rayfilestorage import FileStorage

        storage = FileStorage(opt["options"])
        return storage

    if opt["kind"] == "S3":
        from .s3storage import S3FileStorage

        path = opt["options"]["path"]
        s3fs_pars = opt["options"]["s3fs"]
        return S3FileStorage(path, s3fs_pars)
