from functionfuse.workflow import workflow
from functionfuse.backends.addons.kfpback import KFPWorkflow

import kfp
import kfp.dsl as dsl
from kfp.components import (
    create_component_from_func,
    InputBinaryFile,
    OutputBinaryFile,
    OutputPath,
    InputPath,
)


# Requires a KubeflowPipelines server running on a Kubernetes cluster
# and with port forwarded to localhost:3000
def test1_kfp(host="http://localhost:3000"):
    client = kfp.Client(host=host)

    def sum1(a: float, b: float, output_path: OutputPath(str)):
        print(a)
        print(b)
        import pickle

        with open(output_path, "wb") as f:
            pickle.dump(a + b, f)

    def sum2(a: InputPath(), b: float, output_file: OutputBinaryFile(bytes)):
        print(type(a))
        print(b)
        import pickle

        with open(a, "rb") as f:
            a_val = pickle.load(f)
        print(a_val)
        pickle.dump(a_val + b, output_file)
        # with open(output_file, 'wb') as f:
        #     pickle.dump(a_val+b, f)

    # sum_op = create_component_from_func(sum)
    sum1_op = create_component_from_func(sum1)
    sum2_op = create_component_from_func(sum2)

    def minus(a: InputPath(), b: InputBinaryFile(bytes)) -> float:
        print(a)
        print(type(a))
        print(b)
        print(type(b))
        import io

        print(type(b) == io.BufferedReader)
        import pickle

        a_val = pickle.load(open(a, "rb"))
        b_val = pickle.load(b)
        # b_val = b.read()
        print(a_val)
        print(b_val)
        return a_val - b_val

    minus_op = create_component_from_func(minus)

    @dsl.pipeline(
        name="Basic pipeline",
    )
    def basic_pipeline(a=0, b=0):
        task_1 = sum1_op(a, b)
        task_2 = sum2_op(task_1.output, b)
        minus_op(task_1.output, task_2.output)

    arguments = {"a": 1, "b": 1}

    client.create_run_from_pipeline_func(basic_pipeline, arguments=arguments)


def test2_kfp(host="http://localhost:3000"):
    client = kfp.Client(host=host)

    def gen_sum(args):
        import inspect

        def sum_func(output_file: OutputBinaryFile(bytes), **kwargs):
            import io, pickle

            def sum(a, b):
                return a + b

            a = kwargs["a"]
            if type(a) == io.BufferedReader:
                a = pickle.load(a)
            b = kwargs["b"]
            if type(b) == io.BufferedReader:
                b = pickle.load(b)
            result = sum(a, b)
            pickle.dump(result, output_file)

        args.update({"output_file": OutputBinaryFile(bytes)})

        params = [
            inspect.Parameter(
                param, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=type_
            )
            for param, type_ in args.items()
        ]
        sum_func.__signature__ = inspect.Signature(params)
        sum_func.__annotations__ = args

        return sum_func

    sum1 = gen_sum({"a": float, "b": float})
    print(sum1.__signature__)
    sum1_op = create_component_from_func(sum1)

    sum2 = gen_sum({"a": InputBinaryFile(bytes), "b": float})
    print(sum2.__signature__)
    sum2_op = create_component_from_func(sum2)

    def minus(a: InputBinaryFile(bytes), b: InputBinaryFile(bytes)) -> float:
        print(a)
        print(type(a))
        print(b)
        print(type(b))
        import io

        print(type(b) == io.BufferedReader)
        import pickle

        a_val = pickle.load(a)
        b_val = pickle.load(b)
        # b_val = b.read()
        print(a_val)
        print(b_val)
        return a_val - b_val

    minus_op = create_component_from_func(minus)

    @dsl.pipeline(
        name="Basic pipeline",
    )
    def basic_pipeline(a=0, b=0):
        task_1 = sum1_op(a, b)
        task_2 = sum2_op(task_1.output, b)
        minus_op(task_1.output, task_2.output)

    arguments = {"a": 1, "b": 1}

    client.create_run_from_pipeline_func(basic_pipeline, arguments=arguments)


def test1(host="http://localhost:3000"):
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

    kfp_workflow = KFPWorkflow(m, workflow_name="first")
    result = kfp_workflow.run()
    print("Test1: ", result)
    assert result == -1


# if __name__ == "__main__":

#     from optparse import OptionParser

#     rejection_choices = ("basicRejection", "rejectionReusedDiscriminator")

#     parser = OptionParser()
#     parser.add_option(
#         "-k", "--kfpserver", dest="kfpserver", default="http://localhost:3000",
#         help=f"KFP Server (host) location. Default: http://localhost:3000")

#     (options, args) = parser.parse_args()
#     test1_kfp(host=options.kfpserver)

# if __name__ == "__main__":

registry_credentials = {
    "server": "docker-na.artifactory.swg-devops.com/res-hcls-mcm-brain-docker-local",
    "username": "thrumbel@us.ibm.com",
    "password": "",
}
baseimage = "docker-na.artifactory.swg-devops.com/res-hcls-mcm-brain-docker-local/particles-py3.10:1.5"

TEST = "test2"

if TEST == "test1":

    @workflow
    def sum(a, b):
        return a + b

    @workflow
    def minus(a, b):
        return a - b

    a, b = 1, 1

    # Testing kargs
    # s1 = sum(a=a, b=b)
    # s2 = sum(a=s1, b=b)
    # m = minus(a=s1, b=s2)

    # Testing args
    s1 = sum(a, b)
    s2 = sum(s1, b)
    m = minus(s1, s2)

    #      s1
    #    /  |
    #   s2  |
    #     \ |
    #       m

    kfp_workflow = KFPWorkflow(
        m,
        workflow_name="kfp_test_first",
        baseimage=baseimage,
        registry_credentials=registry_credentials,
    )
    kfp_workflow.run()

elif TEST == "test2":
    # Testing multiple return values:
    @workflow
    def sum(a, b):
        return (a + b, b)

    @workflow
    def minus(a, b):
        return a - b

    a, b = 1, 1

    # Testing kargs
    # s1 = sum(a=a, b=b)
    # s2 = sum(a=s1, b=b)
    # m = minus(a=s1, b=s2)

    # Testing args
    s1 = sum(a, b)
    s2 = sum(s1[0], b)
    m = minus(s1[0], s2[0])

    #      s1
    #    /  |
    #   s2  |
    #     \ |
    #       m

    kfp_workflow2 = KFPWorkflow(
        m,
        workflow_name="kfp_test_second",
        baseimage=baseimage,
        registry_credentials=registry_credentials,
    )
    kfp_workflow2.run()
