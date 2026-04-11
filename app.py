# Libraries built into Python
import os
import json
import time
import datetime
import typing


# Git, Werkzeug and Flask install required!
import git
import werkzeug.exceptions
import flask


# Site data
domain_name = "multiplex64.pythonanywhere.com"
repository_path = "https://github.com/Multiplex64/Multiplex64/"
http_methods = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "CONNECT",
    "TRACE",
    "PATCH",
]


# Insert content into template file, variables wrapped with {{curly brackets}}
def replace(input_text: str, to_insert: dict[str, str]) -> str:
    text = input_text
    for key, value in to_insert.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


# Append data to a log
def append_log(file_path: str, to_append: str) -> None:
    try:
        with open(file_path, "a") as file:
            file.write("\n" + to_append)
    except FileNotFoundError:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)))
        with open(file_path, "w") as file:
            file.write(to_append)


# process a page and return data about it
def processPage(path: str) -> dict[str, typing.Any]:
    internal = True
    status_code = 200
    try:
        with open("pages/" + path + "/index.html", "r") as file:
            html_data = file.read()
    except Exception:
        html_data = respond(404)
        status_code = 400
    with open("system/fallback.json", "r") as file:
        json_data = json.loads(file.read())
    try:
        with open("pages/" + path + "/index.json", "r") as file:
            json_data.update(json.loads(file.read()))
    except Exception:
        pass
    return {
        "internal": internal,
        "html": html_data,
        "json": json_data,
        "code": status_code,
    }


# Wrap an HTML fragment with outer tags and styling
def wrap(content: str) -> str:
    try:
        with open("system/wrapper.html", "r") as file:
            return replace(
                file.read(),
                {
                    "content": content,
                },
            )
    except Exception:
        return respond(500, "Error While Generating Page")


# Generate a generic HTTP response page
def respond(e: int = 500, msg: str = "") -> str:
    try:
        with (
            open("system/http-response.json", "r") as file,
            open("system/http-response.html", "r") as html,
        ):
            data = json.loads(file.read())[str(e)]
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
        return "500 Internal Server Error - Critical Failure of Error Handling System."


app = flask.Flask(__name__)


# Init code at the start of every request
@app.before_request
def before_request() -> None:
    flask.g.start_datetime = datetime.datetime.now(datetime.timezone.utc)
    flask.g.start_time = time.time()


# Process and log data before returning response
@app.after_request
def after_request(response: flask.Response) -> flask.Response:
    if flask.request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        remote_addr = flask.request.environ["REMOTE_ADDR"]
    else:
        remote_addr = flask.request.environ["HTTP_X_FORWARDED_FOR"]

    append_log(
        "database/http-log.txt",
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
        "log/http-log.txt",
        str(flask.g.start_datetime)
        + " - "
        + remote_addr.ljust(15)
        + " - "
        + flask.request.method.ljust(8)
        + flask.request.path
        + " - "
        + str(response.status_code),
    )
    response.headers["X-Clacks-Overhead"] = (
        "GNU Kshitij Gairola, Surya Narayana Murthy Nookala"
    )
    return response


# Main page handler
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def main(path: str) -> flask.Response:
    if os.path.isfile("pages/" + path):
        return flask.send_from_directory("pages", path)
    else:
        page_data = processPage(path)

        metaData = (
            "<title>"
            + page_data["json"]["meta"]["title"]
            + "</title><meta name='description' content='"
            + page_data["json"]["meta"]["description"]
            + "'><link rel='canonical' href='"
            + "https://"
            + domain_name
            + page_data["json"]["meta"]["canonical"]
            + "'><meta property='og:title' content='"
            + page_data["json"]["meta"]["title"]
            + "'><meta property='og:description' content='"
            + page_data["json"]["meta"]["description"]
            + "'><meta property='og:url' content='"
            + "https://"
            + domain_name
            + page_data["json"]["meta"]["canonical"]
            + "'>"
        )


        with (
            open("system/index.html", "r") as outer_html,
        ):
            response = flask.make_response(
                replace(
                    outer_html.read(),
                    {
                        "metacontent": metaData,
                        "pagecontent": page_data["html"],
                    },
                ),
                page_data["code"],
            )
        return response


# /alt directory handler
@app.route("/alt/<path:path>")
def alt(path: str):
    if os.path.isfile("alt/" + path):
        return flask.send_from_directory("alt", path)
    else:
        try:
            with open("alt/" + path + "/index.html", "r") as file:
                status_code = 200
                page_content = file.read()
        except Exception:
            status_code = 404
            page_content = wrap(respond(404))
        return flask.make_response(page_content, status_code)


# Catch unused /null directories
@app.route("/null/<path:path>")
def null(path: str) -> tuple[str, int]:
    return (
        wrap(respond(404, "File/Directory Not Found - Requested Path: /null/" + path)),
        404,
    )


# Always return 200 for testing purposes
@app.route("/null/test/", methods=http_methods)
def null_test():
    return flask.request.method + " Test OK!"


# Handler that allows frontend to request page content and update site without full reload
@app.route("/null/page/", defaults={"path": ""})
@app.route("/null/page/<path:path>")
def null_page(path: str) -> tuple[dict[str, typing.Any], int]:
    page_data = processPage(path)
    page_data["json"]["data"] = {}
    page_data["json"]["data"]["html"] = page_data["html"]
    page_data["json"]["meta"]["canonical"] = (
        "https://" + domain_name + page_data["json"]["meta"]["canonical"]
    )
    return page_data["json"], page_data["code"]


# Update Pythonanywhere server using Github Webhooks
@app.route("/null/server-update/", methods=["POST"])
def update_server() -> tuple[str, int]:
    abort_code = 400
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

    git.cmd.Git().pull(repository_path, "main")  # type:ignore
    git.Repo(".").git.submodule("update", "--init")
    return "Updated PythonAnywhere successfully", 200


"""
# Catch All Unhandled Errors
@app.errorhandler(Exception)
def handle_exception(e: Exception) -> tuple[str, int]:
    return wrap(respond(500, "Unknown Internal Failure")), 500
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
