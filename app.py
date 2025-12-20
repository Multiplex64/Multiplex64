import os
import json
import git
import werkzeug
import flask


# Git, Werkzeug and Flask required


# Insert content into template text
def replace(inputText, **toInsert):
    text = inputText
    for key, value in toInsert.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


# Read text file and return content
def get(page: str):
    try:
        with open(page, "r") as file:
            return file.read()
    except Exception:
        return error(404)


# Handle errors
def error(e=500, msg=""):
    try:
        with (
            open("system/http-response.json", "r") as file,
            open("system/http-response.html", "r") as html,
        ):
            data = json.loads(file.read())[str(e)]
            return (
                replace(html.read(), error=str(e), errorinfo=data, errormessage=msg),
                str(e),
            )
    except Exception:
        return (
            "500 Internal Server Error - Critical Failure of Error Handling System.",
            500,
        )


# Handle user pages
def mainPageHandler(dir):
    pageContent = get("pages/" + "/".join(dir) + "/index.html")
    jsonRawData = get("pages/" + "/".join(dir) + "/multiplex64.json")

    if isinstance(pageContent, tuple):
        jsonRawData = get("system/error.json")
    else:
        pageContent = (pageContent, None)
        if isinstance(jsonRawData, tuple):
            jsonRawData = get("system/default.json")
    jsonData = json.loads(jsonRawData)

    metaData = (
        "<title>"
        + jsonData["meta"]["title"]
        + "</title><meta name='description' content='"
        + jsonData["meta"]["description"]
        + "'>"
    )

    return (
        replace(
            get("system/index.html"),
            stylecontent=("<style>" + get("system/style.css") + "</style>"),
            scriptcontent=("<script>" + get("system/script.js") + "</script>"),
            metacontent=metaData,
            pagecontent=pageContent[0],
        ),
        pageContent[1],
    )


def smartPageHandler(dir):
    pageContent = get("pages/" + "/".join(dir) + "/index.html")
    jsonRawData = get("pages/" + "/".join(dir) + "/multiplex64.json")

    if isinstance(pageContent, tuple):
        jsonRawData = get("system/error.json")
    else:
        pageContent = (pageContent, None)
        if isinstance(jsonRawData, tuple):
            jsonRawData = get("system/default.json")
    jsonData = json.loads(jsonRawData)
    jsonData["data"] = {}
    jsonData["data"]["html"] = pageContent[0]
    return jsonData, pageContent[1]


app = flask.Flask(__name__)


@app.errorhandler(werkzeug.exceptions.HTTPException)
def handleError(e):
    return error(e.code)


@app.route(
    "/",
    defaults={"path": ""},
    methods=[
        "GET",
        "HEAD",
        "POST",
        "PUT",
        "DELETE",
        "CONNECT",
        "OPTIONS",
        "TRACE",
        "PATCH",
    ],
)
@app.route(
    "/<path:path>",
    methods=[
        "GET",
        "HEAD",
        "POST",
        "PUT",
        "DELETE",
        "CONNECT",
        "OPTIONS",
        "TRACE",
        "PATCH",
    ],
)
def main(path):
    dir = path.split("/")
    if flask.request.method == "GET":
        match dir[0]:
            case "null":
                del dir[0]
                if not dir:
                    flask.abort(404)
                match dir[0]:
                    case "test":
                        return "GET Test OK!", 200
                    case "system":
                        del dir[0]
                        if not dir:
                            flask.abort(404)
                        if os.path.splitext("/".join(dir))[1]:
                            if os.path.isfile("system/" + "/".join(dir)):
                                return flask.send_from_directory(
                                    "system", "/".join(dir)
                                )
                            else:
                                flask.abort(404)
                    case "page":
                        del dir[0]
                        return smartPageHandler(dir)
                    case "file":
                        del dir[0]
                        if not dir:
                            flask.abort(404)
                        if os.path.splitext("/".join(dir))[1]:
                            if os.path.isfile("pages/" + "/".join(dir)):
                                return flask.send_from_directory("pages", "/".join(dir))
                            else:
                                flask.abort(404)
                    case _:
                        flask.abort(404)
            case "alt":
                del dir[0]
                if os.path.splitext("/".join(dir))[1]:
                    if os.path.isfile("alt/" + "/".join(dir)):
                        return flask.send_from_directory("alt", "/".join(dir))
                    else:
                        flask.abort(404)
                else:
                    return get("alt/" + "/".join(dir) + "/index.html")
            case _:
                if os.path.splitext("/".join(dir))[1]:
                    if os.path.isfile("pages/" + "/".join(dir)):
                        return flask.send_from_directory("pages", "/".join(dir))
                    else:
                        flask.abort(404)
                else:
                    return mainPageHandler(dir)
    elif flask.request.method == "POST":
        match dir[0]:
            case "null":
                del dir[0]
                if not dir:
                    flask.abort(404)
                match dir[0]:
                    case "test":
                        return {"response": "POST Test OK!"}, 200
                    case "server-update":
                        # Update flask server using github webhooks
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
                        if not ua.startswith("GitHub-Hookshot/"):
                            flask.abort(abort_code)

                        event = flask.request.headers.get("X-GitHub-Event")
                        if event == "ping":
                            return json.dumps({"Response": "Ping OK!"})
                        if event != "push":
                            return json.dumps({"Response": "Wrong event type"})

                        repo = git.cmd.Git(
                            "https://github.com/Multiplex64/Multiplex64/"
                        )
                        repo.pull("origin", "main")
                        return "Updated PythonAnywhere successfully", 200
                    case _:
                        flask.abort(404)
            case _:
                flask.abort(404)
    else:
        flask.abort(405)
