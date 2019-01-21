from flask import Flask
from random import randint
from time import sleep

import datetime
import json
import requests
import os

from py_zipkin.zipkin import *

app = Flask(__name__)

# We need to reference this a few times in calls to Zipkin
zipkin_svc_name="time_web"


"""
Define a transport to send data to Zipkin over HTTP. It uses the Zipkin
URL defined as an environment variable.
"""
def http_transport(encoded_span):
    return requests.post(
		os.environ["ZIPKIN_DSN"],
        data=encoded_span,
        headers={"Content-Type": "application/x-thrift"},
)


"""
A simple helper to return a Zipkin span name that has the service name
prepended. This namespacing helps keep the instrumented service/method
clear on the Zipkin UI
"""
def get_zipkin_span_name(name):
    return "_".join([zipkin_svc_name, name])


"""
Call the Time API microservice, which should return the time in JSON. Unserialise the
response and return it as a plaintext string.

If the API is unavailable return False.
"""
def get_time_from_api():
    with zipkin_span(service_name=zipkin_svc_name, span_name=get_zipkin_span_name("get_time_from_api")):

        time_api = os.environ["TIME_API_URL"]

        # Generate a new set of Zipkin span headers and include them in the call to the
        # downstream microservice. This will cause Zipkin to join both services and surface
        # them as a single Span.
        headers = {}
        headers.update(create_http_headers_for_new_span())

        r = requests.get(time_api, headers=headers)

        return r.json()


"""
The meat of the service: Listens for a HTTP call to "/", serves the return value
from get_time_from_api()
"""
@app.route("/")
def index():
    with zipkin_span(
        service_name=zipkin_svc_name,
        span_name=get_zipkin_span_name("index"),
        transport_handler=http_transport,
        port=5001,
        sample_rate=100,
    ):
        time = get_time_from_api()
        return "<html><h1>{}</h1></html>".format(time)
