from ...baseworkflow import BaseWorkflow
from ...workflow import _test_arg
import ray


@ray.remote
def exec_func(plugin_func, arg_index, karg_keys, args, kargs, func):
    
    if plugin_func is not None:
        plugin_func()
    
    for index, val_index in arg_index:
        if val_index is None:
            args[index] = ray.get(args[index])
        else:
            args[index] = ray.get(args[index])[val_index]

    for key, val_index in karg_keys:
        if val_index is None:
            kargs[key] = ray.get(kargs[key])
        else:
            kargs[key] = ray.get(kargs[key])[val_index]

    return func(*args, **kargs)



class RayWorkflow(BaseWorkflow):

    def __init__(self, *nodes, workflow_name):
        super(RayWorkflow, self).__init__(*nodes, workflow_name = workflow_name)

    
    def run(self):
        ray.shutdown()
        ray.init()
        
        for name, exec_node in self.graph_traversal():

            args = list(exec_node.args)
            kargs = exec_node.kargs.copy()
            arg_index = []
            for index, (node, val_index) in exec_node.arg_index:
                args[index] = node.result
                arg_index.append((index, val_index))

            karg_keys = []
            for key, (node, val_index) in exec_node.karg_keys:
                kargs[key] = node.result
                karg_keys.append((key, val_index))

            backend_info = exec_node.backend_info

            plugin_func = None
            if "plugin" in backend_info:
                plugin = backend_info["plugin"]
                plugin.local_initialize()
                plugin_func = plugin.remote_initialize()
        
            result = exec_func.remote(plugin_func, arg_index, karg_keys, args, kargs, exec_node.func)
            exec_node.result = result
            exec_node.free_memory()

        if len(self.leaves) == 1:
            return ray.get(self.leaves[0].result)
     
        result = []
        for i in self.leaves:
            nodearg = _test_arg(i)
            if nodearg[1] == None:
                result.append(ray.get(nodearg[0].result))
            else:
                result.append(ray.get(nodearg[0].result)[nodearg[1]])
        return result


    def set_plugin(self, pattern, plugin):
        nodes = self.find_nodes(pattern)
        for i in nodes:
            i.backend_info["plugin"] = plugin

    
