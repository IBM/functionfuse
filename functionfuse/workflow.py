import copy, os, re



def workflow(func):
    return NodeContainer(func)


def _test_arg(arg):
    if isinstance(arg, Node):
        return (arg, None)
    if isinstance(arg, NodeItem):
        return (arg.node, arg.index)
    return None


class NodeContainer:

    def __init__(self, func):
        self.func = func
        #self.index = 0
    
    def __call__(self, *args, **kargs):
        name = f"{getattr(self.func, '__qualname__', None)}"
        #self.index += 1
        node = Node(name, self.func)
        return node(*args, **kargs)


class NodeItem:
    def __init__(self, node, index):
        self.node, self.index = node, index

    @property
    def result(self):
        return self.node.result[self.index]


class Node:

    def __init__(self, name, func):
        self.name = name
        self.save_name = None
        self.func = func
        self.children = []
        self.parents = None
        self.seen = False
        self.arg_index = []
        self.karg_keys = []
        self._backend_info = {}

    @property
    def backend_info(self):
        return self._backend_info

    def set_name(self, name):
        self.save_name = name
        return self

    def __getitem__(self, index):
        return NodeItem(self, index)

    def __call__(self, *args, **kargs):
        self.args, self.kargs = args, kargs
        parents = []
        for index, i in enumerate(args):
            node_arg = _test_arg(i)
            if node_arg:
                parent = node_arg[0]
                parents.append(parent)
                parent.children.append(self)
                self.arg_index.append((index, node_arg))
        for key, value in kargs.items():
            node_arg = _test_arg(value)
            if node_arg:
                parent = node_arg[0]
                parents.append(parent)
                parent.children.append(self)
                self.karg_keys.append((key, node_arg))
        
        self.parents = parents
        self.n_ready_parents = 0
        return self
        

    def parents_ready(self):
        self.n_ready_parents += 1
        return self.n_ready_parents == len(self.parents)
    
    def reset_ready_parents(self):
        self.n_ready_parents = 0

    def free_memory(self):
        self.parents = None
        self.arg_index = None
        self.karg_keys = None


    def get_name(self, file_index = None):
        if file_index is None:
            return self.save_name
        name = self.save_name if self.save_name is not None else self.name + f"_{file_index:010d}" 
        return name


    def set_backend_info(self, info, obj):
        self.backend_info[info] = obj

    def exec(self, args, kargs):
        return self.func(*args, **kargs)










        



    


    

    





