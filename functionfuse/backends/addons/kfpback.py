from ...baseworkflow import BaseWorkflow
from ...workflow import _test_func_node

import kfp
import kfp.dsl as dsl
from kfp.components import create_component_from_func, InputBinaryFile, OutputBinaryFile


def generate_function(args: dict) -> callable:

    import inspect

    def exec_func(output_file: OutputBinaryFile(bytes),
                    calling_file: str,
                    *args,
                    **kargs):
        import os, pickle, io

        ffargs = []
        for arg in args:
            if type(arg) == io.BufferedReader:
                ffargs.append(pickle.load(arg))
            else:
                ffargs.append(arg)

        ffkargs = {}
        for key, val in kargs.items():
            if type(val) == io.BufferedReader:
                ffkargs[key] = pickle.load(val)
            else:
                ffkargs[key] = val

        os.ffargs = ffargs
        os.ffkargs = ffkargs

        # Run the function by importing the file with workflow.run original call
        from importlib import import_module
        import_module(calling_file)

        # Get result from os module
        result = os.ffresult
        pickle.dump(result, output_file)

    args.update({'output_file': OutputBinaryFile(bytes),
                    'calling_file': str})
    
    params = [inspect.Parameter(param,
                                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                    annotation=type_)
                            for param, type_ in args.items()]
    
    exec_func.__signature__ = inspect.Signature(params)
    exec_func.__annotations__ = args

    return exec_func
    

class KFPWorkflow(BaseWorkflow):
    """
    A Backend to run workflows on Kubeflow Pipelines. To store node results, use local storage. The storage for this class could be created by functionfuse.storage.storage_factory.  

    :param nodes: A list of DAG nodes. The backend finds all DAG roots that are ancestors of the nodes and executes graph starting from that roots traversing all descendend nodes.
    :param workflow_name: A name of the workflow that is used by storage classes.
    
    """
    def __init__(self, *nodes, workflow_name,
                 baseimage="python",
                 registry_credentials={},
                 kfp_host="http://localhost:3000"):
        super(KFPWorkflow, self).__init__(*nodes, workflow_name = workflow_name)
        self.object_storage = None
        self.baseimage = baseimage
        self.registry_credentials = registry_credentials
        self.kfp_host = kfp_host

    def set_registry_credentials(self, registry_credentials):
        self.registry_credentials = registry_credentials

    def set_baseimage(self, baseimage):
        self.baseimage = baseimage

    def set_kfp_host(self, kfp_host):
        self.kfp_host = kfp_host

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

    def run(self):
        """
        Start execution of the workflow

        :return: A list of results for input nodes or a single result if a single node is used in initialization of the class object.
        """

        # Check environment to see if we should call a function, or build the 
        # pipeline:
        import os
        fffunction = os.getenv("FFFUNCTION")
        if fffunction:
            ffargs = os.ffargs
            ffkargs = os.ffkargs
            # Execute function matching environment variable:
            for name, exec_node in self.graph_traversal():
                if name == fffunction:
                    # this is the node to run
                    result = exec_node.func(*ffargs, **ffkargs)
                    os.ffresult = result
                    return result
        else:

            import inspect, os, subprocess
            calling_file = (inspect.stack()[1])[1]
            print(f"KFP Workflow Run -- calling_file: {calling_file}")
            calling_folder = os.path.dirname(calling_file)
            print(f"KFP Workflow Run -- calling_folder: {calling_folder}")
            calling_file_trim = calling_file.split('/')[-1].split('.')[0]
            print(f"KFP Workflow Run -- calling_file_trim: {calling_file_trim}")

            # Create image from base + calling folder
            with open("Dockerfile", "w") as f:
                f.write(f"FROM {self.baseimage}\n")
                f.write("WORKDIR /ffrun")
                f.write(f"ADD {calling_folder} /ffrun/\n")

            if "server" in self.registry_credentials:
                image_name = f"{self.registry_credentials['server']}/{self.workflow_name}"
            else:
                image_name = f"{self.workflow_name}"
            build_cmd = ["docker", "build", "-t", f"{image_name}", "."]
            build_process = subprocess.Popen(build_cmd)
            build_process.wait()

            # Login to docker registry
            if self.registry_credentials:
                username = self.registry_credentials['username'] if 'username' in self.registry_credentials.keys() else None
                password = self.registry_credentials['password'] if 'password' in self.registry_credentials.keys() else None
                login_cmd = ["docker", "login"]
                if username:
                    login_cmd.extend(["--username", username])
                if (username and password):
                    login_cmd.extend(["--password", password])
                login_cmd.extend([self.registry_credentials['server']])
                login_process = subprocess.Popen(login_cmd)
                login_process.wait()
            
            # push new image for retrieval by KFP
            push_cmd = ["docker", "push", f"{image_name}"]
            push_process = subprocess.Popen(push_cmd)
            push_process.wait()


            # Traverse the graph, creating ops from functions
            for name, exec_node in self.graph_traversal():
                # Check arguments and set node outputs present in arguments to OutputBinaryFiles
                args = list(exec_node.args)
                args_types = [type(arg) for arg in args]

                kargs = exec_node.kargs.copy()
                kargs_types = {}
                for key, val in kargs.items():
                    kargs_types.update({key: type(val)})

                for index, _ in exec_node.arg_index:
                    args_types[index] = InputBinaryFile(bytes)

                for key, _ in exec_node.karg_keys:
                    kargs_types[key] = InputBinaryFile(bytes)

                exec_func = generate_function(kargs_types)

                print(name)

                exec_node.set_backend_info('exec_func', exec_func)
                print(exec_func.__signature__)
                exec_op = create_component_from_func(exec_func)
                exec_node.set_backend_info('op', exec_op)

            @dsl.pipeline(name=self.workflow_name)
            def workflow_pipeline():
                for name, exec_node in self.graph_traversal():
                    args = list(exec_node.args)
                    kargs = exec_node.kargs.copy()
                    for index, (node, val_index) in exec_node.arg_index:
                        if val_index is None:
                            args[index] = node.result.output
                        else:
                            args[index] = node.result[val_index].output

                    for key, (node, val_index) in exec_node.karg_keys:
                        if val_index is None:
                            kargs[key] = node.result.output
                        else:
                            kargs[key] = node.result[val_index].output

                    import pickle
                    exec_node.result = exec_node.backend_info['op'](
                        calling_file=calling_file_trim,
                        **kargs
                        )
                    
                    # exec_node.free_memory()

                # if len(self.leaves) == 1:
                #     return self.leaves[0].result
            
                # result = [i.result for i in self.leaves]
                # return result

        client = kfp.Client(host=self.kfp_host)
        client.create_run_from_pipeline_func(workflow_pipeline,
                                             arguments={})
