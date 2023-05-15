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

    