# Here, we reimplement sklearn example as Function Fuse workflow https://scikit-learn.org/stable/auto_examples/linear_model/plot_sparse_logistic_regression_mnist.html#sphx-glr-auto-examples-linear-model-plot-sparse-logistic-regression-mnist-py

from functionfuse import workflow
from functionfuse.backends.builtin.rayback import RayWorkflow
from functionfuse.storage import storage_factory

import os


# Frontend

@workflow
def openml_dataset():
    from sklearn.datasets import fetch_openml
    from sklearn.utils import check_random_state

    X, y = fetch_openml("mnist_784", version=1, return_X_y=True, as_frame=False, parser="pandas")
    random_state = check_random_state(0)
    permutation = random_state.permutation(X.shape[0])
    X = X[permutation]
    y = y[permutation]
    X = X.reshape((X.shape[0], -1))
    return X, y


@workflow
def train_test_split(X, y, train_samples, test_size):
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=train_samples, test_size=test_size
    )
    return {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test}

@workflow
def train_model(X, y):
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.linear_model import LogisticRegression

    train_samples = len(X)
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=50.0 / train_samples, penalty="l1", solver="saga", tol=0.1))
    clf.fit(X, y)
    return clf


dataset = openml_dataset().set_name("dataset")
X, y = dataset[0], dataset[1]
dataset_split = train_test_split(X, y, train_samples = 5000, test_size = 10000).set_name("dataset_split")
model = train_model(dataset_split["X_train"], dataset_split["y_train"]).set_name("model")


# Ray Backend

ray_init_args = {
    "resources": {"_disk": 1.0, "_model": 1}
}

ray_storage_remote_args = {
    "resources": {"_disk": 0.001}
}

ray_workflow = RayWorkflow(dataset, workflow_name="classifier", ray_init_args=ray_init_args)

# Ray init is called in the RayWorkflow constructor!!! Storage should be created AFTER RayWorkflow is created. 
storage_path = os.path.join(os.getcwd(), "storage")
opt = {
    "kind": "ray",
    "options": {
        "remoteArgs": ray_storage_remote_args,
        "path": storage_path,
    }
}

storage = storage_factory(opt)
ray_workflow.set_storage(storage)
ray_workflow.query(pattern="^model$").set_remote_args({"num_cpus": 1, "resources": {"_model": 1}})

_ = ray_workflow.run()

