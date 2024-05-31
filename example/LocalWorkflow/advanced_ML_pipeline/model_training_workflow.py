# This Workflow Is Created To Replicate An Example From Sklearn https://scikit-learn.org/stable/auto_examples/classification/plot_classifier_comparison.html

from functionfuse import workflow
from functionfuse.backends.builtin.localback import LocalWorkflow
from functionfuse.storage import storage_factory

import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier

# List of classifiers to test

classifiers = [
    ("Nearest Neighbors", KNeighborsClassifier, {"n_neighbors": 3}),
    ("Linear SVM", SVC, {"kernel": "linear", "C": 0.025}),
    ("RBF SVM", SVC, {"gamma": 2, "C": 1}),
    ("Gaussian Process", GaussianProcessClassifier, {"kernel": 1.0 * RBF(1.0)}),
    ("Decision Tree", DecisionTreeClassifier, {"max_depth": 5}),
    (
        "Random Forest",
        RandomForestClassifier,
        {"max_depth": 5, "n_estimators": 10, "max_features": 1},
    ),
    ("Neural Net", MLPClassifier, {"alpha": 1, "max_iter": 1000}),
    ("AdaBoost", AdaBoostClassifier, {}),
    ("Naive Bayes", GaussianNB, {}),
    ("QDA", QuadraticDiscriminantAnalysis, {}),
]


# User function definitions to setup graph nodes


@workflow
def linearly_separable_dataset():
    import numpy as np
    from sklearn.datasets import make_classification

    X, y = make_classification(
        n_features=2,
        n_redundant=0,
        n_informative=2,
        random_state=1,
        n_clusters_per_class=1,
    )
    rng = np.random.RandomState(2)
    X += 2 * rng.uniform(size=X.shape)

    return X, y


@workflow
def moons_dataset():
    from sklearn.datasets import make_moons

    return make_moons(noise=0.3, random_state=0)


@workflow
def circles_dataset():
    from sklearn.datasets import make_circles

    return make_circles(noise=0.2, factor=0.5, random_state=1)


@workflow
def train_test_split(X, y):
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.4, random_state=42
    )
    return {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test}


@workflow
def train_model(classifier_name, classifire_class, classifier_pars, X, y):
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline

    clf = make_pipeline(StandardScaler(), classifire_class(**classifier_pars))
    clf.fit(X, y)
    print(f"Training model {classifier_name}")
    return clf


# Constructing nodes

datasets = [circles_dataset(), moons_dataset(), linearly_separable_dataset()]
datasets_names = ["circles_dataset", "moons_dataset", "linearly_separable_dataset"]

for ds_name, ds in zip(datasets_names, datasets):
    ds.set_name(f"{ds_name}_samples")
    dataset_split = train_test_split(X=ds[0], y=ds[1]).set_name(f"{ds_name}_split")
    for clf_name, clf_class, clf_pars in classifiers:
        model = train_model(
            clf_name,
            clf_class,
            clf_pars,
            dataset_split["X_train"],
            dataset_split["y_train"],
        ).set_name(f"{ds_name}, {clf_name}-model")


# Local backend with storage

local_workflow = LocalWorkflow(*datasets, workflow_name="classifiers")
storage_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "storage")
opt = {"kind": "file", "options": {"path": storage_path}}
storage = storage_factory(opt)
local_workflow.set_storage(storage)
local_workflow.run()
