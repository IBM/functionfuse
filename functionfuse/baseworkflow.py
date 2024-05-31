from .workflow import NodeItem
import re


def _find_roots(nodes):
    roots = set()
    for i in nodes:
        stack = [i]
        while stack:
            v = stack.pop()
            if v.parents:
                for i in v.parents:
                    if not i.seen:
                        i.seen = True
                        stack.append(i)
            else:
                roots.add(v)

    return roots


class BaseWorkflow:
    def __init__(self, *nodes, workflow_name):
        self.workflow_name = workflow_name
        leaves = []
        for i in nodes:
            if isinstance(i, NodeItem):
                leaves.append(i.node)
            else:
                leaves.append(i)

        roots = _find_roots(leaves)
        self.roots = roots
        self.leaves = nodes

    def graph_traversal(self):
        roots = self.roots
        while roots:
            new_roots = []
            for i in roots:
                yield i.get_name(), i
                for node in i.children:
                    if node.parents_ready():
                        new_roots.append(node)
                        node.reset_ready_parents()
            roots = new_roots

    def find_nodes(self, pattern=None):
        if pattern is None:
            return [node for _, node in self.graph_traversal()]

        pattern = re.compile(pattern)
        res = []
        for name, node in self.graph_traversal():
            if pattern.fullmatch(name):
                res.append(node)
        return res

    def replace_func(self, node, new_func):
        node.func = new_func
