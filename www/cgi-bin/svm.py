#!/usr/bin/env python

import cgi
import cgitb
cgitb.enable()

import json
import numpy as np
import os
import re

from urlparse import parse_qs


def classify(features, labels):
    from shogun.Features import RealFeatures, BinaryLabels
    from shogun.Kernel import PolyKernel, GaussianKernel, SplineKernel
    from shogun.Classifier import LibSVM

    features = RealFeatures(features)

    labels = BinaryLabels(labels)
    # kernel = SplineKernel(features, features)
    sigma = 10000
    kernel = GaussianKernel(features, features, sigma)
    # kernel = PolyKernel(features, features, 50, 2)
    cost = 5

    svm = LibSVM(cost, kernel, labels)
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


def get_features(message):
    data = json.loads(message)

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


def render_html(args):
    with open("demo.html", "r") as f:
        web = f.read()
    return web


def render_json(args):
    message = cgi.FieldStorage().value

    try:
        features, labels = get_features(message)
    except ValueError as e:
        return json.dumps({"status": e.message})

    x, y, z = classify(features, labels)

    data = {"status": "ok", "max": np.max(z), "min": np.min(z), "z": z.tolist()}

    return json.dumps(data)


supported_formats = {
    "html": {"render": render_html, "content-type": "text/html"},
    "json": {"render": render_json, "content-type": "application/json"}
}


def main():
    args = parse_qs(os.environ['QUERY_STRING'], True)

    format = "html"     # Default format
    for a in supported_formats:
        if a in args:
            format = a
            break

    print "Content-Type: {0}".format(supported_formats[format]["content-type"])
    print ""
    print supported_formats[format]['render'](args)


main()
