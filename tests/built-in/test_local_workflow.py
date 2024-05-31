from functionfuse import workflow
from functionfuse.backends.builtin.localback import LocalWorkflow
from functionfuse.storage import storage_factory


def test1():
    """
    Testing basic graph
    """

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

    local_workflow = LocalWorkflow(m, workflow_name="first")
    result = local_workflow.run()
    print("Test1: ", result)
    assert result == -1


def test2():
    """
    Testing basic graph with iterative output
    """

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

    local_workflow = LocalWorkflow(m, workflow_name="second")
    result = local_workflow.run()
    print("Test2: ", result)
    assert result == -1


def _test_storage(storage):
    """
    Testing basic graph
    """

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

    local_workflow = LocalWorkflow(m, workflow_name="storage_test")
    local_workflow.set_storage(storage)
    result = local_workflow.run()
    print("Test storage: ", result)
    assert result == -1


def test_storage():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdirname:
        storage_opt = {"kind": "file", "options": {"path": tmpdirname}}
        storage = storage_factory(storage_opt)

        _test_storage(storage)
        _test_storage(storage)


test1()
test2()
test_storage()
