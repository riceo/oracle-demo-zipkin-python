from flask import Flask, request
from random import randint
from time import sleep

import datetime
import json
import requests
import os

from py_zipkin.zipkin import *

app = Flask(__name__)

# We need to reference this a few times in calls to Zipkin
zipkin_svc_name="time_api"


"""
Define a transport to send data to Zipkin over HTTP. It uses the
Zipkin URL defined as an environment variable.
"""
def http_transport(encoded_span):
    return requests.post(
		os.environ['ZIPKIN_DSN'],
        data=encoded_span,
        headers={'Content-Type': 'application/x-thrift'},
)


"""
A simple helper to return a Zipkin span name that has the service name
prepended. This namespacing helps keep the instrumented service/method 
clear on the Zipkin UI.
"""
def get_zipkin_span_name(name):
    return "_".join([zipkin_svc_name, name])


"""
Get the current time after random for a random number of
seconds between 1 and 5. Return it as a string.
"""
def get_time():
    with zipkin_span(service_name=zipkin_svc_name, span_name=get_zipkin_span_name("get_time")):
        sleep(randint(1,5))
        return str(datetime.datetime.now())


"""
The meat of the service: Listens for a HTTP call to "/", serves the return value
from get_time()
"""
@app.route('/')
def index():
    # The X-* headers come from the upstream, calling service. Since this is a backend
    # microservice that will be called by another service and not a human, we can expect
    # the request to come with Zipkin span headers attached. Those headers will then be included
    # in this service's call to Zipkin to ensure the request is tracked end-to-end, across both
    # services.
    with zipkin_span(
        service_name=zipkin_svc_name,
        span_name=get_zipkin_span_name("index"),
        transport_handler=http_transport,
        zipkin_attrs=ZipkinAttrs(
            trace_id=request.headers['X-B3-TraceID'],
            span_id=request.headers['X-B3-SpanID'],
            parent_span_id=request.headers['X-B3-ParentSpanID'],
            flags=request.headers['X-B3-Flags'],
            is_sampled=request.headers['X-B3-Sampled'],
        ),
        port=5000,
        sample_rate=100
    ):
        got_time = get_time()
        return json.dumps(got_time)

