#!/usr/bin/env python

import cgi
import cgitb
cgitb.enable()

import json
import numpy as np
import os
import re
import pickle

from urlparse import parse_qs
from shogun.Kernel import PolyKernel, GaussianKernel, LinearKernel


kernels = {
    "poly": PolyKernel,
    "linear": LinearKernel,
    "gaussian": GaussianKernel
}


def classify(classifier, features, labels, C=5, kernel_name=None, kernel_args=None):
    from shogun.Features import RealFeatures
    sigma = 10000
    kernel = GaussianKernel(features, features, sigma)
    # TODO
    # kernel = LinearKernel(features, features)
    # kernel = PolyKernel(features, features, 50, 2)
    # kernel = kernels[kernel_name](features, features, *kernel_args)

    svm = classifier(C, kernel, labels)
    svm.train(features)
    x_size = 640
    y_size = 400
    size = 100
    x1 = np.linspace(0, x_size, size)
    y1 = np.linspace(0, y_size, size)
    x, y = np.meshgrid(x1, y1)

    test = RealFeatures(np.array((np.ravel(x), np.ravel(y))))
    kernel.init(features, test)

    out = svm.apply(test).get_values()
    if not len(out):
        out = svm.apply(test).get_labels()
    z = out.reshape((size, size))
    z = np.transpose(z)

    return x, y, z


def _get_coordinates(data):
    regex = re.match(r"translate\((?P<x>.*),(?P<y>.*)\)", data)

    x = float(regex.group("x"))
    y = float(regex.group("y"))

    return (x, y)


def get_binary_features(data):
    from shogun.Features import BinaryLabels, RealFeatures

    A = np.transpose(np.array(map(_get_coordinates, data.get("a", []))))
    B = np.transpose(np.array(map(_get_coordinates, data.get("b", []))))

    if not len(A):
        if not len(B):
            raise ValueError("0-labels")
        else:
            raise ValueError("1-class-labels")
    else:
        if not len(B):
            raise ValueError("1-class-labels")
        else:
            features = np.concatenate((A, B), axis=1)
            labels = np.concatenate((np.ones(A.shape[1]), -np.ones(B.shape[1])), axis=1)

    features = RealFeatures(features)
    labels = BinaryLabels(labels)

    return features, labels


def get_multi_features(data):
    from shogun.Features import MulticlassLabels, RealFeatures

    v = {"a": None, "b": None, "c": None, "d": None}
    empty = np.zeros((2, 0))
    for key in v:
        if key in data:
            v[key] = np.transpose(np.array(map(_get_coordinates, data[key])))
        else:
            v[key] = empty

    n = len(set(["a", "b", "c", "d"]) & set(data.keys()))

    if not n:
        raise ValueError("0-labels")
    elif n == 1:
        raise ValueError("1-class-labels")
    else:
        features = np.concatenate(tuple(v.values()), axis=1)
        labels = np.concatenate((np.zeros(v["a"].shape[1]), np.ones(v["b"].shape[1]), 2 * np.ones(v["c"].shape[1]), 3 * np.ones(v["d"].shape[1])), axis=1)
        with open("a", "w") as f:
            pickle.dump([v, features, labels], f)

    features = RealFeatures(features)
    labels = MulticlassLabels(labels)

    return features, labels


def render_binary(args):
    with open("binary.html", "r") as f:
        web = f.read()
    return web


def render_multi(args):
    with open("multi.html", "r") as f:
        web = f.read()
    return web


def render_regression(args):
    with open("regression.html", "r") as f:
        web = f.read()
    return web


def render_404(args):
    with open("404.html", "r") as f:
        web = f.read()
    return web


def run_binary(data):
    from shogun.Classifier import LibSVM

    try:
        features, labels = get_binary_features(data["points"])
    except ValueError as e:
        return json.dumps({"status": repr(e)})

    try:
        x, y, z = classify(LibSVM, features, labels, data["C"])
    except Exception as e:
        return json.dumps({"status": repr(e)})

    data = {"status": "ok", "domain": [-1, 1], "max": np.max(z), "min": np.min(z), "z": z.tolist()}

    return json.dumps(data)


def run_multi(data):
    from shogun.Classifier import GMNPSVM

    try:
        features, labels = get_multi_features(data["points"])
    except ValueError as e:
        return json.dumps({"status": e.message})

    x, y, z = classify(GMNPSVM, features, labels, data["C"])

    # Conrec hack: add tiny noise
    z = z + np.random.rand(*z.shape) * 0.01

    data = {"status": "ok", "domain": [0, 4], "max": np.max(z), "min": np.min(z), "z": z.tolist()}

    return json.dumps(data)


def run_regression(data):
    # TODO
    return {"status": "Not implemented yet"}


methods = {
    "binary": run_binary,
    "multi": run_multi,
    "regression": run_regression
}


def render_json(args):
    message = json.loads(cgi.FieldStorage().value)

    return methods[message["action"]](message["data"])


supported_formats = {
    "binary": {"render": render_binary, "content-type": "text/html"},
    "multi": {"render": render_multi, "content-type": "text/html"},
    "regression": {"render": render_regression, "content-type": "text/html"},
    "json": {"render": render_json, "content-type": "application/json"}
}


def main():
    args = parse_qs(os.environ['QUERY_STRING'], True)

    if "action" in args:
        action = args["action"][0]
        format = "text/html"
    else:
        action = "json"
        format = "application/json"

    print "Content-Type: {0}".format(format)
    print ""

    print supported_formats.get(action, {"render": render_404})["render"](args)


main()
