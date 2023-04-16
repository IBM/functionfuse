from functionfuse import workflow
from functionfuse.backends.builtin.localback import LocalWorkflow
from functionfuse.storage import storage_factory


def test1():
    '''
    Testing basic graph
    '''
    @workflow
    def sum(a, b):
        return a + b


    @workflow
    def minus(a, b):
        return a - b


    a, b = 1, 1

    s1 = sum(a, b).set_name("First sum")
    s2 = sum(s1, b).set_name("Second sum")
    m = minus(s1, s2).set_name("Single minus")


    #      s1
    #    /  |
    #   s2  |
    #     \ |
    #       m

    local_workflow = LocalWorkflow(m, workflow_name = "first")
    nodes = local_workflow.find_nodes(r"^.*sum.*$")
    print("^.*sum.*$: ")
    for i in nodes:
        print(i.get_name())
    
    nodes = local_workflow.find_nodes(r"^.*minus.*$")
    print("^.*minus*$")
    for i in nodes:
        print(i.get_name())    
    

test1()
