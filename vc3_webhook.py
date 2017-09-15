#!/usr/bin/env python

import os
import sys
import json
import uuid
import re
import subprocess
import hmac

from flask import Flask, request
import flask

app = Flask(__name__)
if os.environ.get('DEBUG') == 'true':
    app.debug = True

mappings = []
RESTART_SCRIPT = '/usr/local/bin/restart_docker'
URL_PREFIX = "/git/vc3"

@app.route(URL_PREFIX + '/vc3_webhook.wsgi', methods=['GET', 'POST'])
def update_code():
    """
    Receive a github webhook and update repo

    :return: flask response
    """
    if request.method == 'GET':
        # exit on gets, we want a call with a body
        response = {"status": 200,
                    "msg": "OK"}
        return flask.jsonify(response)

    if request.headers.get('X-GitHub-Event') == "ping":
        # respond to pings
        response = {"status": 200,
                    "msg": "Hi!"}
        return flask.jsonify(response)
    if request.headers.get('X-GitHub-Event') != "push":
        # punt if it's not a push
        response = {"status": 400,
                    "msg": "Invalid event type"}
        return flask.jsonify(response)

    # get github secret and verify push
    secret = os.environ['GITHUB_SECRET']
    payload_signature = request.headers.get('X-Hub-Signature')
    signature = "sha=1" + hmac.new(secret, str(request.form)).hexdigest()
    if signature != payload_signature:
        response = {"status": 403,
                    "msg": "Signature doesn't match"}
        return flask.jsonify(response)


    subprocess.call([RESTART_SCRIPT])
    response = {"status": 200,
                "msg": "Ok"}
    return flask.jsonify(response)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8888)
