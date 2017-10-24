#!/usr/bin/env python

import os
import subprocess
import hmac
import hashlib
import json
import logging
import logging.handlers

from flask import Flask, request
import flask

app = Flask(__name__)
if os.environ.get('DEBUG') == 'true':
    app.debug = True

mappings = []
RESTART_SCRIPT = '/usr/local/bin/restart_docker'
URL_PREFIX = "/git/vc3"


if app.debug:
    handler = logging.handlers.RotatingFileHandler(filename='/tmp/vc3-webhook.log')
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
    handler.setFormatter(formatter)


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
        return flask.jsonify(response), 400
    # get github secret and verify push
    secret = os.environ['GITHUB_SECRET']
    payload_signature = request.headers.get('X-Hub-Signature')
    signature = "sha1=" + hmac.new(secret, str(request.data), digestmod=hashlib.sha1).hexdigest()
    if signature != payload_signature:
        response = {"status": 403,
                    "msg": "Signature doesn't match"}
        return flask.jsonify(response), 403

    # Check to see if we're only checking for a certain branch
    if 'GITHUB_BRANCH' in os.environ:
        ref = "refs/heads/{0}".format(os.environ['GITHUB_BRANCH'])
        github_response = json.loads(str(request.data))
        if github_response['ref'] != ref:
            response = {"status": 200,
                        "msg": "Interested in push " +
                               "to {0} not {1}, ignoring".format(ref, github_response['ref'])}
            return flask.jsonify(response), 200

    try:
        subprocess.check_call([RESTART_SCRIPT])
    except subprocess.CalledProcessError as e:
        response = {"status": 200,
                    "msg": "Could not reload container: {0}".format(e)}
    else:
        response = {"status": 200, "msg": "Container reloaded"}
    return flask.jsonify(response)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8888)

