from functionfuse.workflow import workflow
from functionfuse.backends.builtin.rayback import RayWorkflow
from functionfuse.backends.plugins import PluginCollection, InitializerPlugin, RandomStatePlugin


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

    s1 = sum(a, b)
    s2 = sum(s1, b)
    m = minus(s1, s2)


    #      s1
    #    /  |
    #   s2  |
    #     \ |
    #       m

    ray_workflow = RayWorkflow(m, workflow_name = "first")
    result = ray_workflow.run()
    print("Test1: ", result)
    assert(result == -1)


def test2():
    '''
    Testing basic graph with iterative output
    '''
    @workflow
    def sum(a, b):
        return (a + b, b)


    @workflow
    def minus(a, b):
        return a - b


    a, b = 1, 1

    s1 = sum(a, b)
    s2 = sum(s1[0], b)
    m = minus(s1[0], s2[0])


    #      s1
    #    /  |
    #   s2  |
    #     \ |
    #       m


    ray_workflow = RayWorkflow(m, workflow_name = "second")
    result = ray_workflow.run()
    print("Test2: ", result)
    assert(result == -1)


class TorchRandomStatePlugin(RandomStatePlugin):

    def set_seed(self, seed):
        import torch
        return torch.random.manual_seed(seed)
    


def test3():
    '''
    Testing plugin
    '''

    @workflow
    def sum(a, b):
        import torch 
        print("sum random:", torch.rand(1))
        print("sum type:", torch.get_default_dtype())
        return a + b


    @workflow
    def minus(a, b):
        import torch
        print("minus random:", torch.rand(1))
        print("minus type:", torch.get_default_dtype())
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


    def init_float():
        import torch
        torch.set_default_dtype(torch.float64)
    
    def set_seed(seed):
        import torch
        torch.random.manual_seed(seed)
        print(torch.rand(1))

    random_state_plugin = RandomStatePlugin(min= -0x8000_0000_0000_0000, max= 0xffff_ffff_ffff_ffff, seed = -0x8000_0000_0000_0000, seed_func= set_seed)
    plugin = PluginCollection([InitializerPlugin(init_float), random_state_plugin])

    ray_workflow = RayWorkflow(m, workflow_name = "first")
    ray_workflow.set_plugin(pattern=r"^.*sum.*$", plugin=plugin)
    result = ray_workflow.run()
    print("Test1: ", result)
    assert(result == -1)



test1()
test2()
test3()