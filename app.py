import os
import json
import flask
import git


def replace(inputText, **toInsert):
    text = inputText
    for key, value in toInsert.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def get(page: str):
    try:
        with open(page, "r") as file:
            return file.read()
    except Exception:
        return error(404)


def error(e=500, msg=""):
    try:
        with (
            open("global/http-response.json", "r") as file,
            open("global/http-response.html", "r") as html,
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


app = flask.Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def main(path):
    try:
        dir = path.split("/")
        match flask.request.method:
            case "GET":
                match dir[0]:
                    case "_null":
                        del dir[0]
                        if not dir:
                            return error(404)
                        match dir[0]:
                            case "global":
                                del dir[0]
                                if os.path.splitext("/".join(dir))[1]:
                                    if os.path.isfile("global/" + "/".join(dir)):
                                        return flask.send_from_directory(
                                            "global", "/".join(dir)
                                        )
                                    else:
                                        return error(404)
                            case "page":
                                del dir[0]
                                if os.path.isfile(
                                    "pages/" + "/".join(dir) + "/index.html"
                                ):
                                    return get("pages/" + "/".join(dir) + "/index.html")
                                else:
                                    return error(404)
                            case "file":
                                del dir[0]
                                if os.path.splitext("/".join(dir))[1]:
                                    if os.path.isfile("pages/" + "/".join(dir)):
                                        return flask.send_from_directory(
                                            "pages", "/".join(dir)
                                        )
                                    else:
                                        return error(404)
                            case _:
                                return error(404)
                    case _:
                        if os.path.splitext("/".join(dir))[1]:
                            if os.path.isfile("pages/" + "/".join(dir)):
                                return flask.send_from_directory("pages", "/".join(dir))
                            else:
                                return error(404)
                        else:
                            pageContent = get("pages/" + "/".join(dir) + "/index.html")
                            if not isinstance(pageContent, tuple):
                                pageContent = (pageContent, None)
                            return (
                                replace(
                                    get("global/_index.html"),
                                    pagecontent=pageContent[0],
                                ),
                                pageContent[1],
                            )
            case "POST":
                match dir[0]:
                    case "_null":
                        del dir[0]
                        if not dir:
                            flask.abort(404)
                        match dir[0]:
                            case "server-update":
                                repo = git.cmd.Git(
                                    "https://github.com/Multiplex64/Multiplex64/"
                                )
                                repo.pull("origin", "main")
                                return "Updated PythonAnywhere successfully", 200
                            case _:
                                flask.abort(404)
                    case _:
                        flask.abort(404)
            case _:
                flask.abort(405)
    except Exception:
        return error(500, "Flask Handler Error")
