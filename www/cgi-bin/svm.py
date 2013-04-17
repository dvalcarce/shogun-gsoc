#!/usr/bin/env python

import cgi
import cgitb
cgitb.enable()

import json
import numpy as np
import os
import re

from urlparse import parse_qs
from shogun.Features import RealFeatures, BinaryLabels
from shogun.Kernel import PolyKernel, GaussianKernel, LinearKernel
from shogun.Classifier import LibSVM


kernels = {
    "poly": PolyKernel,
    "linear": LinearKernel,
    "gaussian": GaussianKernel
}


def classify(features, labels, C=5, kernel_name=None, kernel_args=None):

    features = RealFeatures(features)

    labels = BinaryLabels(labels)
    # kernel = SplineKernel(features, features)
    sigma = 10000
    kernel = GaussianKernel(features, features, sigma)
    # kernel = PolyKernel(features, features, 50, 2)
    # TODO
    #kernel = kernels[kernel_name](features, features, *kernel_args)

    svm = LibSVM(C, kernel, labels)
    svm.train()
    x_size = 640
    y_size = 400
    size = 100
    x1 = np.linspace(0, x_size, size)
    y1 = np.linspace(0, y_size, size)
    x, y = np.meshgrid(x1, y1)

    test = RealFeatures(np.array((np.ravel(x), np.ravel(y))))
    kernel.init(features, test)

    out = svm.apply().get_values()
    z = out.reshape((size, size))
    z = np.transpose(z)

    return x, y, z


def _get_coordinates(data):
    regex = re.match(r"translate\((?P<x>.*),(?P<y>.*)\)", data)

    x = float(regex.group("x"))
    y = float(regex.group("y"))

    return (x, y)


def get_features(data):

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
    try:
        features, labels = get_features(data["points"])
    except ValueError as e:
        return json.dumps({"status": e.message})

    x, y, z = classify(features, labels, data["C"])

    data = {"status": "ok", "max": np.max(z), "min": np.min(z), "z": z.tolist()}

    return json.dumps(data)


def run_multi(data):
    # TODO
    return {"status": "Not implemented yet"}


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
