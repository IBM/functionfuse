# checksum is copied from 
# https://stackoverflow.com/questions/1653897/if-pickling-was-interrupted-will-unpickling-necessarily-always-fail-python

import hashlib, glob
import pickle, os, shutil
import io, copyreg

_HASHLEN = 20

class InvalidPickle(ValueError):
    pass


def init_serializers(serializer_classes, path, node_name):
    serializers = [i(path, node_name) for i in serializer_classes]
    return serializers

def safepickle(obj, serializers):
    if serializers:
        stream = io.BytesIO()
        p = pickle.Pickler(stream)
        p.dispatch_table = copyreg.dispatch_table.copy()
        for i in serializers:
            p.dispatch_table[i.serializer_class] = i.reduce
        p.dump(obj)
        stream.seek(0)
        s = stream.read()
    else:
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
    Local file storage. Pickle is used to save results of the graph nodes.
    """
    invalid_exception = InvalidPickle
    bigdata = "bigdata"


    def __init__(self, path):
        self.path = path
        os.makedirs(path, exist_ok=True)
        self.serializers = []

    def add_serializer(self, serializer_class):
        self.serializers.append(serializer_class)

    def save(self, workflow_name, filename, obj):
        folder = os.path.join(self.path, workflow_name)
        if not os.path.exists(folder):
            raise FileNotFoundError(f"Path {self.path} is not found")
        
        serializers = None
        if self.serializers:
            bigdata_folder = os.path.join(folder, self.bigdata)
            os.makedirs(bigdata_folder, exist_ok=True)
            serializers = [i(bigdata_folder, filename) for i in self.serializers]
        
        path = os.path.join(self.path, workflow_name, filename)
        with open(path, "wb") as f:
            f.write(safepickle(obj, serializers))


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
        with open(path, "rb") as f:
            return safeunpickle(f.read())


    def _remove_task(self, workflow_name, task_name):

        folder = os.path.join(self.path, workflow_name)
        path = os.path.join(folder, task_name)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} is not found")
        
        os.remove(path)

        bigdata_folder = os.path.join(folder, self.bigdata)
        if os.path.exists(bigdata_folder):        
            prefixed = [filename for filename in os.listdir(bigdata_folder) if filename.startswith(task_name)]
            for i in prefixed:
                os.remove(os.path.join(bigdata_folder, i))




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
        
        