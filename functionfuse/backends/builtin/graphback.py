from ...baseworkflow import BaseWorkflow
import graphviz
import tempfile

class GraphWorkflow(BaseWorkflow):

    def __init__(self, *nodes, workflow_name, doc_path):
        super(GraphWorkflow, self).__init__(*nodes, workflow_name = workflow_name)
        self.doc_path = doc_path

    def run(self):
        
        dot = graphviz.Digraph(self.workflow_name, comment=self.workflow_name, format='svg')
        for name, node in self.graph_traversal():
            dot.node(name, name)
            for i in node.children:
                dot.edge(name, i.name)

        dot.render(directory=self.doc_path, view=True) 
        
