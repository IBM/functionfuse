import dask.array as da
import numpy as np

from functionfuse import workflow
from functionfuse.backends.builtin.localback import LocalWorkflow
from functionfuse.storage import storage_factory
from functionfuse.serializers.daskarray import HDFSerializer


def _test_storage(storage):
    """
    Testing basic graph
    """

    @workflow
    def create_dask_array():
        array = np.arange(10000)
        dask_array = da.from_array(array, chunks=(1000,))
        return dask_array * dask_array

    @workflow
    def print_array(array):
        print(array.compute())

    array = create_dask_array().set_name("dask_array")
    print_node = print_array(array).set_name("print")

    try:
        storage.remove_task(workflow_name="storage_test", task_name="print")
    except:
        pass

    try:
        storage.remove_task(workflow_name="storage_test", task_name="dask_array")
    except:
        pass

    local_workflow = LocalWorkflow(print_node, workflow_name="storage_test")
    local_workflow.set_storage(storage)
    _ = local_workflow.run()


def test_storage():
    storage_opt = {"kind": "file", "options": {"path": "storage"}}

    storage = storage_factory(storage_opt)
    storage.always_read = True
    storage.register_persistent_serializers(HDFSerializer)
    print("First run ...")
    _test_storage(storage)
    print("Second run ... ")
    _test_storage(storage)


test_storage()
