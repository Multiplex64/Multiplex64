import os
import json
import time
import datetime
import typing
import git
import werkzeug.exceptions
import flask


# Git, Werkzeug and Flask Required!


# List of All HTTP Methods
methods = [
    "GET",
    "HEAD",
    "POST",
    "PUT",
    "DELETE",
    "CONNECT",
    "OPTIONS",
    "TRACE",
    "PATCH",
]


# Insert Content into Template Text
def replace(input_text: str, to_insert: dict[str, str]) -> str:
    text = input_text
    for key, value in to_insert.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


# Append Data to a Log
def append_log(file_path: str, to_append: str) -> None:
    try:
        with open(file_path, "a") as file:
            file.write("\n" + to_append)
    except Exception as e:
        print(e)


# Read Text File and Return Content, Return a 404 page if Not Found
def get(page: str) -> str:
    try:
        with open(page, "r") as file:
            flask.g.last_get = 200
            return file.read()
    except Exception:
        flask.g.last_get = 404
        return respond(404)


# Wrap an HTML Fragment Page with Outer Tags
def wrap(content: str) -> str:
    try:
        with open("system/wrapper.html", "r") as file:
            return replace(
                file.read(),
                {
                    "stylecontent": ("<style>" + get("system/style.css") + "</style>"),
                    "content": content,
                },
            )
    except Exception:
        return respond(500, "Error While Generating Page")


# Generate a Generic HTTP Response Page
def respond(e: int = 500, msg: str = "") -> str:
    try:
        with (
            open("system/http-response.json", "r") as file,
            open("system/http-response.html", "r") as html,
        ):
            data = json.loads(file.read())[str(e)]
            flask.g.last_get = e
            return replace(
                html.read(),
                {
                    "error": str(e),
                    "errorinfo": data["message"],
                    "errormessage": msg,
                    "errordescription": data["description"],
                },
            )
    except Exception:
        flask.g.last_get = 500
        return "500 Internal Server Error - Critical Failure of Error Handling System."


app = flask.Flask(__name__)


@app.before_request
def before_request() -> None:
    flask.g.last_get = 404
    flask.g.start_datetime = datetime.datetime.now(datetime.timezone.utc)
    flask.g.start_time = time.time()


@app.after_request
def after_request(response: flask.Response) -> flask.Response:
    try:
        if flask.request.environ.get("HTTP_X_FORWARDED_FOR") is None:
            remote_addr = flask.request.environ["REMOTE_ADDR"]
        else:
            remote_addr = flask.request.environ["HTTP_X_FORWARDED_FOR"]

        append_log(
            "database/http-log-machine-readable.txt",
            json.dumps(
                {
                    "info": {
                        "request-time-utc": flask.g.start_time,
                        "response-time-ms": 1000 * (time.time() - flask.g.start_time),
                    },
                    "response": {
                        "status_code": response.status_code,
                    },
                    "request": {
                        "method": flask.request.method,
                        "path": flask.request.path,
                        "remote_addr": remote_addr,
                        "user_agent": flask.request.user_agent.string,
                        "referrer": flask.request.referrer,
                    },
                }
            ),
        )
        append_log(
            "database/http-log-human-readable.txt",
            str(flask.g.start_datetime)
            + " - "
            + remote_addr.ljust(15)
            + " - "
            + flask.request.method.ljust(8)
            + flask.request.path
            + " - "
            + str(response.status_code),
        )
    except Exception:
        pass
    return response


# Main Page Handler
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def main(path: str) -> flask.Response:
    if os.path.isfile("pages/" + path):
        return flask.send_from_directory("pages", path)
    else:
        page_content = get("pages/" + path + "/index.html")
        status_code = flask.g.last_get
        raw_json = get("pages/" + path + "/multiplex64.json")

        if status_code != 200:
            raw_json = get("system/error.json")
        else:
            if flask.g.last_get != 200:
                raw_json = get("system/default.json")
        json_dict = json.loads(raw_json)

        metaData = (
            "<title>"
            + json_dict["meta"]["title"]
            + "</title><meta name='description' content='"
            + json_dict["meta"]["description"]
            + "'><link rel='canonical' href='"
            + json_dict["meta"]["canonical"]
            + "'>"
        )
        response = flask.make_response(
            replace(
                get("system/index.html"),
                {
                    "stylecontent": ("<style>" + get("system/style.css") + "</style>"),
                    "scriptcontent": (
                        "<script>" + get("system/script.js") + "</script>"
                    ),
                    "metacontent": metaData,
                    "pagecontent": page_content,
                },
            ),
            status_code,
        )
        return response


# /alt Directory Handler
@app.route("/alt/<path:path>")
def alt(path: str):
    if os.path.isfile("alt/" + path):
        return flask.send_from_directory("alt", path)
    else:
        page_content = get("alt/" + path + "/index.html")
        status_code = flask.g.last_get
        return flask.make_response(page_content, status_code)


# Catch Unused /null Directories
@app.route("/null/<path:path>")
def null(path: str) -> tuple[str, int]:
    return (
        wrap(respond(404, "File/Directory Not Found - Requested Path: /null/" + path)),
        404,
    )


@app.route("/null/test/", methods=methods)
def null_test():
    return flask.request.method + " Test OK!"


# Allow Javascript Fetch to Get Page Content Without Full Site Reload
@app.route("/null/page/", defaults={"path": ""})
@app.route("/null/page/<path:path>")
def null_page(path: str) -> tuple[dict[str, typing.Any], int]:
    page_content = get("pages/" + path + "/index.html")
    status_code = flask.g.last_get
    raw_json = get("pages/" + path + "/multiplex64.json")

    if status_code != 200:
        raw_json = get("system/error.json")
    else:
        if flask.g.last_get != 200:
            raw_json = get("system/default.json")
    json_dict = json.loads(raw_json)
    json_dict["data"] = {}
    json_dict["data"]["html"] = page_content
    return json_dict, status_code


# Update Server Using Github Webhooks
@app.route("/null/server-update/", methods=["POST"])
def update_server() -> tuple[str, int]:
    abort_code = 403
    if "X-Github-Event" not in flask.request.headers:
        flask.abort(abort_code)
    if "X-Github-Delivery" not in flask.request.headers:
        flask.abort(abort_code)

    if not flask.request.is_json:
        flask.abort(abort_code)
    if "User-Agent" not in flask.request.headers:
        flask.abort(abort_code)
    ua = flask.request.headers.get("User-Agent")
    if ua and not ua.startswith("GitHub-Hookshot/"):
        flask.abort(abort_code)

    event = flask.request.headers.get("X-GitHub-Event")
    if event != "push":
        return "Wrong Event type", abort_code

    repo_path = "https://github.com/Multiplex64/Multiplex64/"
    #git.cmd.Git().pull(repo_path,'main')
    repo = git.Repo(repo_path)
    origin = repo.remotes.origin
    origin.pull()
    #repo.remotes.origin.pull()
    # repo.git.submodule('update', '--init')
    return "Updated PythonAnywhere successfully", 200


"""
# Catch All Unhandled Errors
@app.errorhandler(Exception)
def handle_exception(e: Exception) -> tuple[str, int]:
    return respond(500, "Unknown Internal Failure"), 500
"""


# Catch HTTP errors
@app.errorhandler(werkzeug.exceptions.HTTPException)
def handle_respond(e: werkzeug.exceptions.HTTPException) -> tuple[str, int]:
    error_code = e.code
    message = ""
    if error_code is None:
        error_code = 500
        message = "Unexpected Error State in Werkzeug"
    return wrap(respond(error_code, message)), error_code
