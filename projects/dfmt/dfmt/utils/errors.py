from flask import make_response, jsonify

def make_error(message, status):
    error = {
        "status" : status,
        "message" : message,
    }
    return make_response(jsonify(error), status)