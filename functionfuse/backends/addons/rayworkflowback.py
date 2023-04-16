from ...baseworkflow import BaseWorkflow
from ray import workflow
import ray



@ray.remote
def exec_func(plugins, arg_index, karg_keys, args, kargs, func):
    for plugin in plugins:
        plugin()
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

    def __init__(self, *nodes, workflow_name, plugins=[]):
        super(RayWorkflow, self).__init__(*nodes, workflow_name = workflow_name)
        self.plugins = plugins

    
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

            result = exec_func.remote(self.plugins, arg_index, karg_keys, args, kargs, exec_node.func)
            exec_node.result = result
            exec_node.free_memory()

        if len(self.leaves) == 1:
            return ray.get(self.leaves[0].result)
     
        # result = [ray.get(i.result) for i in self.leaves]
        result = []
        from particles.workflow.workflow import _test_arg
        for i in self.leaves:
            nodearg = _test_arg(i)
            if nodearg[1] == None:
                result.append(ray.get(nodearg[0].result))
            else:
                result.append(ray.get(nodearg[0].result)[nodearg[1]])
        return result

