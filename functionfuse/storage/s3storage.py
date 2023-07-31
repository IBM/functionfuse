import posixpath, s3fs

from .base import StorageWithSerializers
from ..serializers import S3_PROTOCOL

class FileProtocol:

    def __init__(self, path, s3):
        self.path = path
        self.s3 = s3

    def open(self, filename, mode):
        return self.s3.open(posixpath.join(self.path, filename), mode)
    
    def remove(self, filename):
        self.s3.rm_file(posixpath.join(self.path, filename))
        


def rmtree(s3, path):
    files = s3.glob(posixpath.join(path, "*"))
    for i in files:
        s3.rm(i)



class S3FileStorage(StorageWithSerializers):
    """
    Local file storage. Pickle is used to save results of the graph nodes.
    """

    bigdata = "bigdata"
    prefix = "s3:/"


    def __init__(self, path, s3fs_pars):
        super(S3FileStorage, self).__init__()
        self.s3fs_pars = s3fs_pars
        self.path = S3FileStorage.prefix + path
        self._always_read = False


    def get_s3(self):
        s3 = s3fs.S3FileSystem(**self.s3fs_pars)
        return s3


    def get_bigdata_path(self, workflow):
        return posixpath.join(self.path, workflow, self.bigdata)

    def get_protocols(self, path, s3):
        protocols = {
            S3_PROTOCOL: {
                "client" : s3,
                "folder" : path
            }
        }
        return protocols

    @property
    def always_read(self):
        return self._always_read
    
    @always_read.setter
    def always_read(self, value):
        self._always_read = value

    def save(self, workflow_name, filename, obj):

        s3 = self.get_s3()
        path = posixpath.join(self.path, workflow_name, filename)
        protocols = self.get_protocols(self.get_bigdata_path(workflow_name), s3) if self.persistent_serializers else None
        
        with s3.open(path, "wb") as f:
            f.write(self.pickle(obj, protocols)) 


    def _test_path(self):
        if not posixpath.exists(self.path):
            raise FileNotFoundError(f"Path {self.path} is not found")


    def file_exists(self, workflow_name, filename):
        s3 = self.get_s3()
        return s3.exists(posixpath.join(self.path, workflow_name, filename))


    def list_tasks(self, workflow_name, pattern):
        """
        List saved results of all saved nodes using glob pattern for workflow.

        :param workflow_name: A name of the workflow to list saved results.
        :type workflow_name: str
        :param pattern: A glob pattern to filter out names of saved results. 

        """
        s3 = self.get_s3()
        path = posixpath.join(self.path, workflow_name, pattern)
        files = s3.glob(path)
        return [posixpath.basename(i) for i in sorted(files) if s3.isfile(i)]


    def read_task(self, workflow_name, task_name):
        """
        Read saved result of node execution from workflow storage.

        :param workflow_name: A name of the workflow to read saved results.
        :type workflow_name: str
        :param task_name: A task name to load results for. 

        """
        s3 = self.get_s3()
        path = posixpath.join(self.path, workflow_name, task_name)
        
        if not s3.exists(path):
            raise FileNotFoundError(f"Path {path} is not found")
        protocols = self.get_protocols(self.get_bigdata_path(workflow_name), s3) if self.persistent_serializers else None
        with s3.open(path, "rb") as f:
            return self.unpickle(f.read(), protocols)


    def _remove_task(self, workflow_name, task_name):

        s3 = self.get_s3()

        folder = posixpath.join(self.path, workflow_name)
        path = posixpath.join(folder, task_name)

        if not s3.exists(path):
            raise FileNotFoundError(f"Path {path} is not found")
        
        if self.persistent_serializers:
            protocols = self.get_protocols(self.get_bigdata_path(workflow_name), s3) 
            with s3.open(path, "rb") as f:
                self.remove_persistent_storage(f.read(), protocols)

        s3.rm_file(path)



    def remove_task(self, workflow_name, task_name = None, pattern = None):
        """
        Remove results of selected nodes from the storage.

        :param workflow_name: A name of the workflow to remove node results.
        :type workflow_name: str
        :param task_name: A name of the node to remove. The parameter is ignored if pattern is defined
        :type workflow_name: str
        :param pattern: A glob pattern of node names to be removed.

        """
        
        if pattern:
            tasks = self.list_tasks(workflow_name, pattern)
            for i in tasks:
                self._remove_task(workflow_name, i)
        else:
            self._remove_task(workflow_name, task_name)


    def remove_workflow(self, workflow_name):
        """
        Remove the workflow from the storage.

        :param workflow_name: A name of the workflow to remove from the storage.
        :type workflow_name: str

        """
        s3 = self.get_s3()
        path = posixpath.join(self.path, workflow_name)
        rmtree(path)
        

    def new_workflow(self, workflow_name):
        """
        S3 does not have folders, we don't need to create a directory 
        to save workflow data
        """
        pass
        