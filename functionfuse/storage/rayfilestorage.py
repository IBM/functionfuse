# checksum is copied from
# https://stackoverflow.com/questions/1653897/if-pickling-was-interrupted-will-unpickling-necessarily-always-fail-python

import hashlib, glob
import pickle, os, shutil
import ray

from collections import namedtuple

_HASHLEN = 20


class InvalidPickle(ValueError):
    pass


def safepickle(obj):
    s = pickle.dumps(obj)
    s += hashlib.sha1(s).digest()
    return s


def safeunpickle(pstr):
    data, checksum = pstr[:-_HASHLEN], pstr[-_HASHLEN:]
    if hashlib.sha1(data).digest() != checksum:
        raise InvalidPickle("Pickle hash does not match!")
    return pickle.loads(data)


class FileStorage:
    """
    Remote file storage on a single designated Ray cluster node.
    Create a single node with unique Ray resource (e.g., _disk: 1) and route all function calls to this node with remoteArgs (see below) setting the same resource (e.g., _disk: 0.001).
    Pickle is used to save results of the graph nodes.

    To create file storage object use :py:func:`functionfuse.storage.storage_factory` with

    .. code-block:: python

        opt = {
            "kind": "ray",
            "options": {
                "rayInitArgs": {...},
                "remoteArgs": {...},
                "path": path,
            }
        }

    :param rayInitArgs: Use this field only in the read mode. File storage calls Ray init with rayInitArgs parameters. Otherwise, Ray init is called in the workflow class.
    :type rayInitArgs: dict, optional
    :param remoteArgs: Dictionary with parameters for the remote function (see `ray.remote <https://docs.ray.io/en/latest/ray-core/api/doc/ray.remote.html>`_)
    :type remoteArgs: dict
    :param path: relative or absolute path to save folder. All results are saved in path/workflow_name folder.

    """

    invalid_exception = InvalidPickle

    def __init__(self, opt):
        remote_args = opt["remoteArgs"]
        if "rayInitArgs" in opt:
            ray.shutdown()
            ray.init(**opt["rayInitArgs"])

        path = opt["path"]
        self.remote_args = remote_args
        self.path = path
        self._actor = None

    def get_writer_funcs(self, workflow_name):
        save_func, read_task, file_exists, new_workflow = self.init_write_functions(
            workflow_name, self.path, self.remote_args
        )
        ReadObectClass = namedtuple(
            "ObectStorageClass", ["remote_args", "file_exists", "read_task"]
        )
        read_object = ReadObectClass(self.remote_args, file_exists, read_task)
        ray.put(read_object)
        return new_workflow, read_object, save_func

    def init_write_functions(self, workflow_name, path, remote_args):
        @ray.remote(**remote_args)
        def save_func(filename, obj):
            if not os.path.exists(os.path.join(path, workflow_name)):
                raise FileNotFoundError(f"Path {path} is not found")
            save_path = os.path.join(path, workflow_name, filename)
            if not os.path.exists(os.path.join(path, workflow_name, filename)):
                obj = ray.get(obj[0])
                with open(save_path, "wb") as f:
                    f.write(safepickle(obj))

        def read_task(task_name):
            save_path = os.path.join(path, workflow_name, task_name)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path {path} is not found")
            print(f"Read task {task_name} from file.")
            with open(save_path, "rb") as f:
                return safeunpickle(f.read())

        def file_exists(filename):
            return os.path.exists(os.path.join(path, workflow_name, filename))

        @ray.remote(**remote_args)
        def new_workflow():
            workflow_path = os.path.join(path, workflow_name)
            if not os.path.exists(workflow_path):
                os.makedirs(workflow_path)

        return save_func, read_task, file_exists, new_workflow

    @property
    def actor(self):
        """
        Access to remote ray actor to avoid blocking calls.
        """
        if not self._actor:
            self._actor = FileStorageActor.options(**self.remote_args).remote(self.path)

        return self._actor

    def list_tasks(self, workflow_name, pattern):
        """
        List saved results of all saved nodes using glob pattern for workflow.

        :param workflow_name: A name of the workflow to list saved results.
        :type workflow_name: str
        :param pattern: A glob pattern to filter out names of saved results.

        """
        return ray.get(self.actor.list_tasks.remote(workflow_name, pattern))

    def read_task(self, workflow_name, task_name):
        """
        Read saved result of node execution from workflow storage.

        :param workflow_name: A name of the workflow to read saved results.
        :type workflow_name: str
        :param task_name: A task name to load results for.

        """
        return ray.get(self.actor.read_task.remote(workflow_name, task_name))

    def remove_task(self, workflow_name, task_name=None, pattern=None):
        """
        Remove results of selected nodes from the storage.

        :param workflow_name: A name of the workflow to remove node results.
        :type workflow_name: str
        :param task_name: A name of the node to remove. The parameter is ignored if pattern is defined
        :type workflow_name: str
        :param pattern: A glob pattern of node names to be removed.

        """

        self.actor.remove_task.remote(workflow_name, task_name, pattern)

    def remove_workflow(self, workflow_name):
        """
        Remove the workflow from the storage.

        :param workflow_name: A name of the workflow to remove from the storage.
        :type workflow_name: str

        """
        self.actor.remove_workflow(workflow_name)


@ray.remote
class FileStorageActor:
    """
    Local file storage. Pickle is used to save results of the graph nodes.
    """

    invalid_exception = InvalidPickle

    def __init__(self, path):
        self.path = path
        os.makedirs(path, exist_ok=True)

    def save(self, workflow_name, filename, obj):
        if not os.path.exists(os.path.join(self.path, workflow_name)):
            raise FileNotFoundError(f"Path {self.path} is not found")
        path = os.path.join(self.path, workflow_name, filename)
        if not self.file_exists(workflow_name, filename):
            obj = ray.get(obj[0])
            with open(path, "wb") as f:
                f.write(safepickle(obj))

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
        return [
            os.path.basename(i)
            for i in sorted(glob.glob(os.path.join(self.path, workflow_name, pattern)))
        ]

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
        with open(path, "rb") as f:
            return safeunpickle(f.read())

    def _remove_task(self, workflow_name, task_name):
        path = os.path.join(self.path, workflow_name, task_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} is not found")
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
                self._remove_task(i)
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
