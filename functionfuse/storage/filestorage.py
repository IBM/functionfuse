import glob
import os, shutil

from .base import StorageWithSerializers
from ..serializers import FILE_PROTOCOL


class FileProtocol:
    def __init__(self, path):
        self.path = path

    def open(self, filename, mode):
        return open(os.path.join(self.path, filename), mode)

    def remove(self, filename):
        os.remove(os.path.join(self.path, filename))


class FileStorage(StorageWithSerializers):
    """
    Local file storage. Pickle is used to save results of the graph nodes.
    """

    bigdata = "bigdata"

    def __init__(self, path):
        super(FileStorage, self).__init__()
        self.path = path
        os.makedirs(path, exist_ok=True)
        self._always_read = False

    def get_bigdata_path(self, workflow):
        return os.path.join(self.path, workflow, self.bigdata)

    def get_protocols(self, path):
        protocols = {FILE_PROTOCOL: FileProtocol(path)}
        return protocols

    @property
    def always_read(self):
        return self._always_read

    @always_read.setter
    def always_read(self, value):
        self._always_read = value

    def save(self, workflow_name, filename, obj):
        folder = os.path.join(self.path, workflow_name)
        if not os.path.exists(folder):
            raise FileNotFoundError(f"Path {self.path} is not found")

        if self.have_serializers():
            bigdata_folder = os.path.join(folder, self.bigdata)
            os.makedirs(bigdata_folder, exist_ok=True)

        path = os.path.join(self.path, workflow_name, filename)
        protocols = (
            self.get_protocols(self.get_bigdata_path(workflow_name))
            if self.persistent_serializers
            else None
        )

        with open(path, "wb") as f:
            f.write(self.pickle(obj, protocols))

    def _test_path(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Path {self.path} is not found")

    def file_exists(self, workflow_name, filename):
        return os.path.exists(os.path.join(self.path, workflow_name, filename))

    def list_tasks(self, workflow_name, pattern):
        """
        List saved results of all saved nodes using glob pattern for workflow.

        :param workflow_name: A name of the workflow to list saved results.
        :type workflow_name: str
        :param pattern: A glob pattern to filter out names of saved results.

        """
        files = glob.glob(os.path.join(self.path, workflow_name, pattern))
        return [os.path.basename(i) for i in sorted(files) if os.path.isfile(i)]

    def read_task(self, workflow_name, task_name):
        """
        Read saved result of node execution from workflow storage.

        :param workflow_name: A name of the workflow to read saved results.
        :type workflow_name: str
        :param task_name: A task name to load results for.

        """
        path = os.path.join(self.path, workflow_name, task_name)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} is not found")
        protocols = (
            self.get_protocols(self.get_bigdata_path(workflow_name))
            if self.persistent_serializers
            else None
        )
        with open(path, "rb") as f:
            return self.unpickle(f.read(), protocols)

    def _remove_task(self, workflow_name, task_name):
        folder = os.path.join(self.path, workflow_name)
        path = os.path.join(folder, task_name)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} is not found")

        if self.persistent_serializers:
            protocols = self.get_protocols(self.get_bigdata_path(workflow_name))
            with open(path, "rb") as f:
                self.remove_persistent_storage(f.read(), protocols)

        os.remove(path)

    def remove_task(self, workflow_name, task_name=None, pattern=None):
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
        path = os.path.join(self.path, workflow_name)
        shutil.rmtree(path, ignore_errors=True)

    def new_workflow(self, workflow_name):
        workflow_path = os.path.join(self.path, workflow_name)
        if not os.path.exists(workflow_path):
            os.makedirs(workflow_path)
