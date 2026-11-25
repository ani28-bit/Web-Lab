from flask import jsonify, request, url_for


def json_body():
    """Parsed JSON body, or None (the schema then reports a field error)."""
    return request.get_json(silent=True)


def created(body, endpoint, **url_values):
    response = jsonify(body)
    response.status_code = 201
    response.headers["Location"] = url_for(endpoint, **url_values)
    return response


def no_content():
    return "", 204
