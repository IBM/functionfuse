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
        remote_args = opt["remoteArg"]
        if "rayInit" in opt and opt["rayInit"]:
            ray.shutdown()
            ray.init(**remote_args)
        actor = FileStorageActor.options(**remote_args).remote(opt["path"])
        storage = FileStorage(actor)
        return storage

    