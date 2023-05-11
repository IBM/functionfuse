def storage_factory(opt):
    """
    Factory that creates a storage class. 

    :param opt: Dictionary with parameters of the storage class

    """
    if opt["kind"] == "file":
        from .filestorage import FileStorage
        return FileStorage(opt["options"]["path"])    
    
    if opt["kind"] == "ray":
        from .rayfilestorage import FileStorageActor, FileStorage
        import ray
        opt = opt["options"]
        remote_args = opt["remoteArgs"]
        if "rayInitArgs" in opt:
            ray.shutdown()
            ray.init(**opt["rayInitArgs"])
        storage = FileStorage(remote_args, opt["path"])
        return storage

    