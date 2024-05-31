from inspect import isclass
from types import FunctionType
from collections import defaultdict


def workflow(func):
    """
    The decorator to create a node of the DAG

    :param func: A function that is placed in the DAG node.
    :type func: function
    :return: a DAG node.

    """

    if isclass(func):
        return ClassContainer(func)
    else:
        return NodeContainer(func)


def _test_func_node(node):
    return isinstance(node, Node)


def _test_constructor_node(node):
    return isinstance(node, ClassInitNode)


def _test_arg(arg):
    if isinstance(arg, (Node, ClassInitNode, ClassCallNode)):
        return (arg, None)
    if isinstance(arg, (NodeItem, ClassItem)):
        return (arg.node, arg.index)
    return None


def _add_element(l: list, node):
    if node not in l:
        l.append(node)


class NodeContainer:
    index = defaultdict(int)

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kargs):
        index = NodeContainer.index[self.func]
        name = f"{getattr(self.func, '__qualname__', None)}_{index:04d}"
        NodeContainer.index[self.func] += 1
        node = Node(name, self.func)
        return node(*args, **kargs)


class NodeItem:
    def __init__(self, node, index):
        self.node, self.index = node, index

    @property
    def result(self):
        return self.node.result[self.index]


class BaseNode:
    def __init__(self, name):
        self.name = name
        self.children = []
        self.parents = None
        self.seen = False
        self.arg_index = []
        self.karg_keys = []
        self._backend_info = {}

    def __call__(self, *args, **kargs):
        self.args, self.kargs = args, kargs
        parents = []
        for index, i in enumerate(args):
            node_arg = _test_arg(i)
            if node_arg:
                parent = node_arg[0]
                _add_element(parents, parent)
                _add_element(parent.children, self)
                self.arg_index.append((index, node_arg))
        for key, value in kargs.items():
            node_arg = _test_arg(value)
            if node_arg:
                parent = node_arg[0]
                _add_element(parents, parent)
                _add_element(parent.children, self)
                self.karg_keys.append((key, node_arg))

        self.parents = parents
        self.n_ready_parents = 0
        return self

    @property
    def backend_info(self):
        return self._backend_info

    def set_name(self, name):
        self.name = name
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

    def get_name(self):
        return self.name

    def set_backend_info(self, info, obj):
        self.backend_info[info] = obj


class Node(BaseNode):
    def __init__(self, name, func):
        super(Node, self).__init__(name)
        self.func = func

    def __getitem__(self, index):
        return NodeItem(self, index)

    def exec(self, args, kargs):
        return self.func(*args, **kargs)


# Wrappers for class nodes


class ClassItem:
    def __init__(self, node, index):
        self.node, self.index = node, index

    @property
    def result(self):
        return self.node.result[self.index]


def _list_methods(cls):
    methods = set(x for x, y in cls.__dict__.items() if isinstance(y, FunctionType))
    methods.remove("__init__")
    if "__get_item__" in methods:
        methods.remove("__get_item__")
    return methods


class _Foo:
    pass


class ClassContainer:
    index = defaultdict(int)

    def __init__(self, class_spec):
        self.class_spec = class_spec

    def __call__(self, *args, **kargs):
        index = ClassContainer.index[self.class_spec]
        name = f"{getattr(self.class_spec, '__qualname__', None)}_{index:04d}"
        ClassContainer.index[self.class_spec] += 1
        node = ClassInitNode(name, self.class_spec)
        return node(*args, **kargs)


class ClassInitNode(BaseNode):
    name_index = defaultdict(int)

    def __init__(self, name, class_spec):
        super(ClassInitNode, self).__init__(name)
        self.class_spec = class_spec
        self.last_invoked_node = self
        self.method_calls = []

    def _make_class_method(self, method_name):
        def _make_call_class_object(*args, **kargs):
            func = getattr(self.class_spec, method_name)
            index = ClassInitNode.name_index[func]
            name = f"{getattr(func, '__qualname__', None)}_{index:04d}"
            ClassInitNode.name_index[func] += 1
            node = ClassCallNode(self, method_name, name)
            node = node(*args, **kargs)
            node.parents.append(self.last_invoked_node)
            self.last_invoked_node.children.append(node)
            self.last_invoked_node = node
            self.method_calls.append(node)
            return node

        return _make_call_class_object

    def __call__(self, *args, **kargs):
        super(ClassInitNode, self).__call__(*args, **kargs)

        call_object = _Foo()
        for i in _list_methods(self.class_spec):
            setattr(call_object, i, self._make_class_method(i))

        def set_name(name):
            self.set_name(name)
            return call_object

        call_object.set_name = set_name
        return call_object

    def exec(self, args, kargs):
        self.obj = self.class_spec(*args, **kargs)


class ClassCallNode(BaseNode):
    def __init__(self, init_object, method_name, name):
        super(ClassCallNode, self).__init__(name)
        self.init_object = init_object
        self.method_name = method_name

    def __getitem__(self, index):
        return ClassItem(self, index)

    def exec(self, args, kargs):
        func = getattr(self.init_object.obj, self.method_name)
        return func(*args, **kargs)
