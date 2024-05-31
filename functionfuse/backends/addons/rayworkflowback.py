from ...baseworkflow import BaseWorkflow
from ...workflow import _test_arg
import ray
from ray import workflow


@ray.remote
def exec_func(plugin_func, func, *args, **kargs):
    if plugin_func is not None:
        plugin_func()

    return func(*args, **kargs)


@ray.remote
def split(node, index):
    return node[index]


@ray.remote
def collect_results(*args):
    return args


class RayWorkflow(BaseWorkflow):
    def __init__(self, *nodes, workflow_name):
        super(RayWorkflow, self).__init__(*nodes, workflow_name=workflow_name)

    def set_storage(self, storage):
        self.storage = storage

    def run(self):
        ray.shutdown()
        ray.init(storage=self.storage)

        for name, exec_node in self.graph_traversal():
            args = list(exec_node.args)
            kargs = exec_node.kargs.copy()

            arg_index = []
            for index, (node, val_index) in exec_node.arg_index:
                if val_index is None:
                    args[index] = node.result
                else:
                    args[index] = split.bind(node.result, val_index)
                arg_index.append(index)

            karg_keys = []
            for key, (node, val_index) in exec_node.karg_keys:
                if val_index is None:
                    kargs[key] = node.result
                else:
                    kargs[key] = split.bind(node.result, val_index)
                karg_keys.append(key)

            backend_info = exec_node.backend_info

            plugin_func = None
            if "plugin" in backend_info:
                plugin = backend_info["plugin"]
                plugin.local_initialize()
                plugin_func = plugin.remote_initialize()

            result = exec_func.bind(plugin_func, exec_node.func, *args, **kargs)
            exec_node.result = result
            exec_node.free_memory()

        if len(self.leaves) == 1:
            result = self.leaves[0].result
        else:
            result = []
            for i in self.leaves:
                nodearg = _test_arg(i)
                if nodearg[1] is None:
                    result.append(nodearg[0].result)
                else:
                    result.append(split.bind(nodearg[0].result, nodearg[1]))

            result = collect_results.bind(result)

        return workflow.run(result, workflow_id=self.workflow_name)

    def set_plugin(self, pattern, plugin):
        nodes = self.find_nodes(pattern)
        for i in nodes:
            i.backend_info["plugin"] = plugin
