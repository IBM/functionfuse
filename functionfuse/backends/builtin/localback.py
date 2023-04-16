from ...baseworkflow import BaseWorkflow


class LocalWorkflow(BaseWorkflow):

    def __init__(self, *nodes, workflow_name):
        super(LocalWorkflow, self).__init__(*nodes, workflow_name = workflow_name)
        self.object_storage = None

    def set_storage(self, object_storage):
        self.object_storage = object_storage

    def run(self):

        if self.object_storage:
            self.object_storage.new_workflow(self.workflow_name)

        for name, exec_node in self.graph_traversal():
            if self.object_storage:
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
            for index, (node, val_index) in exec_node.arg_index:
                if val_index is None:
                    args[index] = node.result
                else:
                    args[index] = node.result[val_index]

            for key, (node, val_index) in exec_node.karg_keys:
                if val_index is None:
                    kargs[key] = node.result
                else:
                    kargs[key] = node.result[val_index]

            result = exec_node.exec(args, kargs)
            exec_node.result = result
            exec_node.free_memory()

            if self.object_storage:
                self.object_storage.save(self.workflow_name, name, result)

        if len(self.leaves) == 1:
            return self.leaves[0].result
     
        result = [i.result for i in self.leaves]
        return result
