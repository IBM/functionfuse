from functionfuse import workflow
from functionfuse.backends.builtin.localback import LocalWorkflow


@workflow
class IncrementalSum:
    def __init__(self, start):
        self.start = start

    def add(self, n):
        self.start += n
        return self.start


@workflow
def minus(a, b):
    return a - b


def test1():
    one = minus(4, 3)
    incremental_sum = IncrementalSum(start=one)

    two = minus(3, one)
    incremental_sum.add(two)
    incremental_sum.add(two)
    six = incremental_sum.add(one)
    result = minus(six, 2)

    local_workflow = LocalWorkflow(result, workflow_name="first")
    result = local_workflow.run()
    print("Test1: ", result)


def test2():
    one = minus(4, 3).set_name("four_minus_three")
    incremental_sum = IncrementalSum(start=one).set_name("IncrementalSum")

    two = minus(3, one).set_name("three_minus_one")
    incremental_sum.add(two).set_name("one_plus_two")
    incremental_sum.add(two).set_name("three_plus_two")
    six = incremental_sum.add(one).set_name("five_plus_one")
    result = minus(six, 2).set_name("six_minus_two")

    local_workflow = LocalWorkflow(result, workflow_name="first")
    result = local_workflow.run()
    print("Test2: ", result)


test1()
test2()
