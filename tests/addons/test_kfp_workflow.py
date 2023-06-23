from functionfuse.workflow import workflow
# from functionfuse.backends.addons.kfpback import KFPWorkflow
from functionfuse.storage import storage_factory

import kfp
import kfp.dsl as dsl
from kfp.components import create_component_from_func

# Requires a KubeflowPipelines server running on a Kubernetes cluster
# and with port forwarded to localhost:3000
def test1_kfp(host="http://localhost:3000"):

    client = kfp.Client(host=host)


    def sum(a: float, b: float) -> float:
        return a + b

    sum_op = create_component_from_func(sum)

    def minus(a: float, b: float) -> float:
        return a - b

    minus_op = create_component_from_func(minus)

    @dsl.pipeline(name='Basic pipeline',)
    def basic_pipeline(a=0, b=0):
        task_1 = sum_op(a, b)
        task_2 = sum_op(task_1.output, b)
        task_3 = minus_op(task_1.output, task_2.output)

    arguments = {'a': 1, 'b': 1}

    client.create_run_from_pipeline_func(basic_pipeline, arguments=arguments)


def test1(host="http://localhost:3000"):
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

    kfp_workflow = KFPWorkflow(m, workflow_name = "first")
    result = kfp_workflow.run()
    print("Test1: ", result)
    assert(result == -1)


if __name__ == "__main__":

    from optparse import OptionParser
    
    rejection_choices = ("basicRejection", "rejectionReusedDiscriminator")

    parser = OptionParser()
    parser.add_option(
        "-k", "--kfpserver", dest="kfpserver", default="http://localhost:3000",
        help=f"KFP Server (host) location. Default: http://localhost:3000")

    (options, args) = parser.parse_args()
    test1_kfp(host=options.kfpserver)
