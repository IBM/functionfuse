from ...baseworkflow import BaseWorkflow
from ...workflow import _test_arg, _test_func_node
from prefect import task, flow, task_runners
from prefect.futures import PrefectFuture

def substitute_args(arg_index, karg_keys, args, kargs):
    for index, val_index in arg_index:
        if val_index is None:
            args[index] = args[index].result()
        else:
            args[index] = args[index].result()[val_index]

    for key, val_index in karg_keys:
        if val_index is None:
            kargs[key] = kargs[key].result()
        else:
            kargs[key] = kargs[key].result()[val_index]

    return arg_index, karg_keys, args, kargs

def exec_func(task_args, func, arg_index, karg_keys, args, kargs):
    
    # if plugin_func is not None:
    #     plugin_func()

    arg_index, karg_keys, args, kargs = substitute_args(arg_index, karg_keys, args, kargs)

    func = task(func, **task_args)
    return func.submit(*args, **kargs)

def _test_print_node(node):
    return "print" not in node.backend_info


class Query:
    """
    The class allows to set attributes to sets of nodes. Contains list of nodes returned by query.
    
    """

    def __init__(self, nodes, workflow):
        self.workflow = workflow
        self.nodes = nodes

    # def set_plugin(self, plugin):
    #     for i in self.nodes:
    #         i.backend_info["plugin"] = plugin
    
    def set_task_args(self, args):
        """
        Set arguments for task definition in Prefect. 

        :param args: Dictionary with arguments of a prefect.task call
        :type args: dict

        """

        for i in self.nodes:
            i.backend_info["task_args"] = args
        return self


class PrefectWorkflow(BaseWorkflow):
    """
    A Backend to run workflows through Prefect. To store node results, use local storage. The storage for this class could be created by functionfuse.storage.storage_factory.  

    :param nodes: A list of DAG nodes. The backend finds all DAG roots that are ancestors of the nodes and executes graph starting from that roots traversing all descendend nodes.
    :param workflow_name: A name of the workflow that is used by storage classes.
    
    """

    def __init__(self, *nodes, workflow_name):
        super(PrefectWorkflow, self).__init__(*nodes, workflow_name = workflow_name)
        self.object_storage = None
        self.prefect_flow_options = {}
        self.flow = None
    
    def set_storage(self, object_storage):
        """
        Set storage for the workflow.

        :param object_storage: Storage object.

        """
        self.object_storage = object_storage

    def log_nodes(self, query):
        nodes = self.find_nodes(query)
        for i in nodes:
            i.backend_info["print"] = True

    def set_plugin(self, query, plugin):
        nodes = self.find_nodes(query)
        for i in nodes:
            i.backend_info["plugin"] = plugin

    def set_prefect_flow_options(self, prefect_flow_options):
        self.prefect_flow_options = prefect_flow_options

    def run(self):
        """
        Start execution of the workflow

        :return: A list of results for input nodes or a single result if a single node is used in initialization of the class object.
        """
        if self.object_storage:
            self.object_storage.new_workflow(self.workflow_name)

        if not self.flow:
            self.generate_flow()

        return self.flow()

    def query(self, pattern = None):
        """
        Query nodes of the graph by regexp pattern.

        :param pattern: regexp pattern to match node names. If None returns all nodes.
        :type pattern: Optional[str]
        :return: Query object

        """
        return Query(self.find_nodes(pattern), self)

    def generate_flow(self):
        """
        Create the flow from the nodes in the graph.
        Separating this from run allows deploy() option within Prefect server
        """
        prefect_flow_options = {"name": self.workflow_name,
                                "task_runner": task_runners.SequentialTaskRunner}
        prefect_flow_options.update(self.prefect_flow_options)

        @flow(**prefect_flow_options)
        def prefect_flow():
            for name, exec_node in self.graph_traversal():
                func_node = _test_func_node(exec_node)
                if self.object_storage and func_node and _test_print_node(exec_node):
                    try:
                        result = self.object_storage.read_task(self.workflow_name, name)
                        print(f"{name} is read from the file.")
                        exec_node.free_memory()
                        exec_node.result = result
                        continue
                    except (self.object_storage.invalid_exception, FileNotFoundError):
                        pass

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

                task_args = {}
                if "task_args" in backend_info:
                    task_args = backend_info["task_args"]

                result = exec_func(task_args, exec_node.func, 
                                   arg_index, karg_keys, args, kargs)
                exec_node.result = result
                exec_node.free_memory()

                save_objects = []
                if self.object_storage and func_node and _test_print_node(exec_node):
                    save_objects.append((name, result))
                    # self.object_storage.save(self.workflow_name, name, result.result())
                    if self.object_storage.always_read:
                        exec_node.result = self.object_storage.read_task(self.workflow_name, name)

            for so in save_objects:
                if isinstance(so[1], PrefectFuture):
                    to_save = so[1].result()
                elif isinstance(so[1], list):
                    to_save = []
                    for i in so[1]:
                        if isinstance(i, PrefectFuture):
                            to_save.append(i.result())
                        else:
                            to_save.append(i)
                else:
                    to_save = so[1]
                    
                self.object_storage.save(self.workflow_name, so[0], to_save)

            if len(self.leaves) == 1:
                nodearg = _test_arg(self.leaves[0])
                if nodearg[1] == None:
                    if isinstance(nodearg[0].result, PrefectFuture):
                        result = nodearg[0].result.result()
                    else:
                        result = nodearg[0].result
                else:
                    if isinstance(nodearg[0].result[nodearg[1]], PrefectFuture):
                        result = nodearg[0].result[nodearg[1]].result()
                    else:
                        result = nodearg[0].result[nodearg[1]]
                return result
            
            result = []
            for i in self.leaves:
                nodearg = _test_arg(i)
                if nodearg[1] == None:
                    if isinstance(nodearg[0].result, PrefectFuture):
                        result.append(nodearg[0].result.result())
                    else:
                        result.append(nodearg[0].result)
                else:
                    if isinstance(nodearg[0].result[nodearg[1]], PrefectFuture):
                        result.append(nodearg[0].result[nodearg[1]].result())
                    else:
                        result.append(nodearg[0].result[nodearg[1]])

            return result
        
        self.flow = prefect_flow
