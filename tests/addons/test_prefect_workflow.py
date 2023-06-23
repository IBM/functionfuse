from functionfuse.workflow import workflow
from functionfuse.backends.addons.prefectback import PrefectWorkflow
from functionfuse.storage import storage_factory

from prefect import flow, task


def test_prefect():
    '''
    Testing basic graph usind deployment
    '''
    @task
    def sum(a, b):
        return a + b


    @task
    def minus(a, b):
        return a - b

    #      s1
    #    /  |
    #   s2  |
    #     \ |
    #       m

    @flow(name="ABTest")
    def workflow():
        a, b = 1, 1

        s1 = sum(a, b)
        s2 = sum(s1, b)
        m = minus(s1, s2)

        return m

    result = workflow()

    print("TestPrefect: ", result)
    assert(result == -1)


def test_prefect_cache():
    '''
    Testing basic graph
    '''
    from prefect.tasks import task_input_hash
    from time import sleep

    @task(cache_key_fn=task_input_hash)
    def sum(a, b):
        print(f"Summing {a} and {b}")
        sleep(10)
        return a + b


    @task(cache_key_fn=task_input_hash)
    def minus(a, b):
        print(f"Subtracting {b} and {a}")
        sleep(10)
        return a - b

    #      s1
    #    /  |
    #   s2  |
    #     \ |
    #       m

    @flow(name="ABTest_cache")
    def workflow():
        a, b = 1, 1

        s1 = sum(a, b)
        s2 = sum(s1, b)
        m = minus(s1, s2)

        return m

    result = workflow()

    print("TestPrefect: ", result)
    assert(result == -1)

    
def test1(prefect_flow_options={}):
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

    prefect_workflow = PrefectWorkflow(m, workflow_name = "first")
    prefect_workflow.set_prefect_flow_options(prefect_flow_options)
    result = prefect_workflow.run()
    print("Test1: ", result)
    assert(result == -1)


def test2(prefect_flow_options={}):
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


    prefect_workflow = PrefectWorkflow(m, workflow_name = "second")
    prefect_workflow.set_prefect_flow_options(prefect_flow_options)
    result = prefect_workflow.run()
    print("Test2: ", result)
    assert(result == -1)

    
def _test_storage(storage, prefect_flow_options={}):

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

    
    prefect_workflow = PrefectWorkflow(m, workflow_name = "storage_test")
    prefect_workflow.set_prefect_flow_options(prefect_flow_options)
    prefect_workflow.set_storage(storage)
    result = prefect_workflow.run()
    print("Test storage: ", result)
    assert(result == -1)


def test_storage():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdirname:
        storage_opt = {
            "kind": "file",
            "options": {
                "path": tmpdirname
            }
        }
        storage = storage_factory(storage_opt)
        _test_storage(storage)
        _test_storage(storage)


def test_persist_result():
    '''
    Turns on result persistence in Prefect Flow, which serializes
    task outputs into default prefect storage location
    '''
    prefect_flow_options = {'persist_result': True}
    test1(prefect_flow_options=prefect_flow_options)
    test2(prefect_flow_options=prefect_flow_options)


def test_cache_result(a=1, b=1):
    '''
    Turns on cache for prefect tasks, to load completed tasks from 
    cache if the function is called again with the same inputs
    '''
    from time import sleep
    @workflow
    def sum(a, b):
        print(f"Summing {a} and {b}")
        sleep(1)
        return a + b


    @workflow
    def minus(a, b):
        print(f"Subtracting {b} from {a}")
        sleep(1)
        return a - b

    s1 = sum(a, b)
    m1 = minus(s1, a)
    s2 = sum(m1, b)
    m2 = minus(s2, b)

    from prefect.tasks import task_input_hash
    query_task_args = {
        "^.*sum.*$": {"cache_key_fn": task_input_hash},
        "^.*minus.*$": {"cache_key_fn": task_input_hash},
    }

    prefect_workflow1 = PrefectWorkflow(m2, workflow_name = "first_cache")
    for query, task_args in query_task_args.items():
        prefect_workflow1.query(query).set_task_args(task_args)
    result = prefect_workflow1.run()

    print("Test cache: ", result)
    assert(result == b)


def test_concurrent_task_runner():
    '''
    Turns on result persistence in Prefect Flow, which serializes
    task outputs into default prefect storage location
    '''
    from prefect.task_runners import ConcurrentTaskRunner
    prefect_flow_options = {'task_runner': ConcurrentTaskRunner()}
    test1(prefect_flow_options=prefect_flow_options)
    test2(prefect_flow_options=prefect_flow_options)


if __name__ == "__main__":
    test1()
    test2()
    test_storage()
    test_persist_result()
    test_concurrent_task_runner()
    test_cache_result()
    test_cache_result(5, 5)
    test_cache_result(5, 5)
