import os
import json
import time
import datetime
import typing
import git
import werkzeug.exceptions
import flask


# Git, Werkzeug and Flask Required!


# Insert Content into Template Text
def replace(inputText: str, toInsert: dict[str, str]) -> str:
    text = inputText
    for key, value in toInsert.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


# Append Data to a Log
def appendLog(filePath: str, toAppend: str) -> None:
    try:
        with open(filePath, "a") as file:
            file.write("\n" + toAppend)
    except Exception as e:
        print(e)


# Read Text File and Return Content, Return a 404 page if Not Found
def get(page: str) -> str:
    try:
        with open(page, "r") as file:
            flask.g.lastGet = 200
            return file.read()
    except Exception:
        flask.g.lastGet = 404
        return http_response(404)


# Wrap an HTML fragment page with outer tags and style
def html_wrap(content: str) -> str:
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
        flask.g.lastGet = 404
        return http_response(404)


# Generate a generic HTTP response page
def http_response(e: int = 500, msg: str = "") -> str:
    try:
        with (
            open("system/http-response.json", "r") as file,
            open("system/http-response.html", "r") as html,
        ):
            data = json.loads(file.read())[str(e)]
            flask.g.lastGet = e
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
        flask.g.lastGet = 500
        return "500 Internal Server Error - Critical Failure of Error Handling System."


app = flask.Flask(__name__)


@app.before_request
def before_request() -> None:
    flask.g.lastGet = 404
    flask.g.startDatetime = datetime.datetime.now(datetime.timezone.utc)
    flask.g.startTime = time.time()


@app.after_request
def after_request(response: flask.Response) -> flask.Response:
    try:
        if flask.request.environ.get("HTTP_X_FORWARDED_FOR") is None:
            remote_addr = flask.request.environ["REMOTE_ADDR"]
        else:
            remote_addr = flask.request.environ["HTTP_X_FORWARDED_FOR"]

        appendLog(
            "database/http-log-machine-readable.txt",
            json.dumps(
                {
                    "info": {
                        "request-time-utc": flask.g.startTime,
                        "response-time-ms": 1000 * (time.time() - flask.g.startTime),
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
        appendLog(
            "database/http-log-human-readable.txt",
            str(flask.g.startDatetime)
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


# Main page handler
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def main(path: str) -> flask.Response:
    if os.path.isfile("pages/" + path):
        return flask.send_from_directory("pages", path)
    else:
        pageContent = get("pages/" + path + "/index.html")
        statusCode = flask.g.lastGet
        jsonRawData = get("pages/" + path + "/multiplex64.json")

        if statusCode != 200:
            jsonRawData = get("system/error.json")
        else:
            if flask.g.lastGet != 200:
                jsonRawData = get("system/default.json")
        jsonData = json.loads(jsonRawData)

        metaData = (
            "<title>"
            + jsonData["meta"]["title"]
            + "</title><meta name='description' content='"
            + jsonData["meta"]["description"]
            + "'><link rel='canonical' href='"
            + jsonData["meta"]["canonical"]
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
                    "pagecontent": pageContent,
                },
            ),
            statusCode,
        )
        return response


@app.route("/null/<path:path>")
def null(path: str) -> tuple[str, int]:
    return (
        html_wrap(
            http_response(
                404, "File/Directory Not Found - Requested Path: /null/" + path
            )
        ),
        404,
    )


# Allow javascript Fetch to get page content without full reload
@app.route("/null/page/", defaults={"path": ""})
@app.route("/null/page/<path:path>")
def null_page(path: str) -> tuple[typing.Any, int]:
    pageContent = get("pages/" + path + "/index.html")
    statusCode = flask.g.lastGet
    jsonRawData = get("pages/" + path + "/multiplex64.json")

    if statusCode != 200:
        jsonRawData = get("system/error.json")
    else:
        if flask.g.lastGet != 200:
            jsonRawData = get("system/default.json")
    jsonData = json.loads(jsonRawData)
    jsonData["data"] = {}
    jsonData["data"]["html"] = pageContent
    return jsonData, statusCode


# Allow Access to System/ folder
@app.route("/null/system/<path:path>")
def null_system(path: str) -> flask.Response:
    return flask.send_from_directory("system", path)


@app.route("/null/server-update/", methods=["POST"])
def update_server():
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
    if event == "ping":
        return json.dumps({"Response": "Ping OK!"})
    if event != "push":
        return json.dumps({"Response": "Wrong event type"})

    repo = git.cmd.Git("https://github.com/Multiplex64/Multiplex64/")  # type: ignore
    repo.pull("origin", "main")  # type: ignore
    return "Updated PythonAnywhere successfully", 200


"""
# Catch all errors
@app.errorhandler(Exception)
def handle_exception(e: Exception):
    return http_response(500, "Unknown failure"), 500
"""


# Catch HTTP errors
@app.errorhandler(werkzeug.exceptions.HTTPException)
def handle_http_response(e: werkzeug.exceptions.HTTPException) -> tuple[str, int]:
    errorCode = e.code
    message = ""
    if errorCode is None:
        errorCode = 500
        message = "Unexpected error state in werkzeug"
    return html_wrap(http_response(errorCode, message)), errorCode
