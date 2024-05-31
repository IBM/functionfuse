import yaml

from functionfuse import workflow
from functionfuse.backends.builtin.localback import LocalWorkflow
from functionfuse.storage import storage_factory


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


"""
# example of yaml file
s3fs:
  key: "access_key"
  secret: "secret_key"
  endpoint_url: "endpoint url"

path: "path to storage"
"""


def test_storage():
    with open("s3credentials.yaml", mode="r") as file:
        options = yaml.safe_load(file)

    storage_opt = {"kind": "S3", "options": options}
    storage = storage_factory(storage_opt)

    _test_storage(storage)
    _test_storage(storage)


test_storage()
