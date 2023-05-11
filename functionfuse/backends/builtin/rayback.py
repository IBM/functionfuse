from ...baseworkflow import BaseWorkflow
from ...workflow import _test_arg
import ray


@ray.remote
def exec_func(
    plugin_func, arg_index, karg_keys, args, kargs, func, 
    workflow_name, node_name, object_storage):
    
    if object_storage and ray.get(object_storage.async_file_exists.remote(workflow_name, node_name)):
        return object_storage.async_read_task.remote(workflow_name, node_name)
        
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

    result = func(*args, **kargs)
    return result


class Query:

    def __init__(self, nodes, workflow):
        self.workflow = workflow
        self.nodes = nodes

    def set_plugin(self, plugin):
        for i in self.nodes:
            i.backend_info["plugin"] = plugin
    
    def set_remote_args(self, args):
        for i in self.nodes:
            i.backend_info["remote_args"] = args
        return self



class RayWorkflow(BaseWorkflow):
    """
    A Backend to run workflows on Ray engine. The storage for this class could be created by functionfuse.storage.storage_factory.  

    :param nodes: A list of DAG nodes. The backend finds all DAG roots that are ancestors of the nodes and executes graph starting from that roots traversing all descendend nodes.
    :param workflow_name: A name of the workflow that is used by storage classes.
    :param ray_init_args: A dictionary with parameters for Ray init
    :type ray_init_args: dict

    """
    def __init__(self, *nodes, workflow_name, ray_init_args = {}):
        super(RayWorkflow, self).__init__(*nodes, workflow_name = workflow_name)

        ray.shutdown()
        ray.init(**ray_init_args)
        self.object_storage = None


    def set_storage(self, object_storage):
        """
        Set storage for the workflow.

        :param object_storage: Storage object.

        """
        self.object_storage = object_storage
        ray.wait([self.object_storage.remote_actor.new_workflow.remote(self.workflow_name)], fetch_local=False)
    

    def run(self, return_results = False):
        """
        Start execution of the workflow.

        :return: A list of results for input nodes or a single result if a single node is used in initialization of the class object.
        """
        
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
        
            remote_args = {}
            if "remote_args" in backend_info:
                remote_args = backend_info["remote_args"]
            
            result = exec_func.options(**remote_args).remote(
                plugin_func, arg_index, karg_keys, args, kargs, exec_node.func, 
                self.workflow_name, name, self.object_storage)
            
            save_objects = []
            if self.object_storage:
                save_objects.append(self.object_storage.async_save.remote(self.workflow_name, name, (result,)))

            exec_node.result = result
            exec_node.free_memory()

        if save_objects:
            ray.wait(save_objects, num_returns=len(save_objects), fetch_local=False)

        if return_results:
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
        else:
            result = []
            for i in self.leaves:
                nodearg = _test_arg(i)
                result.append(nodearg[0].result)                    
            ray.wait(result, num_returns=len(result), fetch_local = False)

    def query(self, pattern = None):
        """
        Query nodes of the graph by regexp pattern.

        :param pattern: regexp pattern to match node names. If None returns all nodes.
        :type pattern: Optional[str]

        """
        return Query(self.find_nodes(pattern), self)

    def set_plugin(self, pattern, plugin):
        nodes = self.find_nodes(pattern)
        for i in nodes:
            i.backend_info["plugin"] = plugin

    
