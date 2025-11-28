import flask
import os
import git

# Flask and GitPython install required! (Through Pip)


def get(page: str):
    try:
        with open(page, "r") as file:
            return file.read()
    except Exception:
        return error404()


def error404():
    try:
        with open("global/404.html", "r") as file:
            return file.read(), 404
    except Exception:
        return "Error 404 Not Found (File System Failure)", 404


app = flask.Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def main(path):
    try:
        dir = path.split("/")
        match flask.request.method:
            case "GET":
                match dir[0]:
                    case "__null":
                        del dir[0]
                        if not dir:
                            return error404()
                        match dir[0]:
                            case "global":
                                del dir[0]
                                if os.path.splitext("/".join(dir))[1]:
                                    if os.path.isfile("global/" + "/".join(dir)):
                                        return flask.send_from_directory(
                                            "global", "/".join(dir)
                                        )
                                    else:
                                        return error404()
                            case "page":
                                del dir[0]
                                if os.path.isfile(
                                    "pages/" + "/".join(dir) + "/index.html"
                                ):
                                    return get("pages/" + "/".join(dir) + "/index.html")
                                else:
                                    return error404()
                            case "file":
                                del dir[0]
                                if os.path.splitext("/".join(dir))[1]:
                                    if os.path.isfile("pages/" + "/".join(dir)):
                                        return flask.send_from_directory(
                                            "pages", "/".join(dir)
                                        )
                                    else:
                                        return error404()
                            case _:
                                return error404()
                    case _:
                        pageContent = get("pages/" + "/".join(dir) + "/index.html")
                        if not isinstance(pageContent, tuple):
                            pageContent = (pageContent, None)

                        return (
                            get("global/_index.html").replace(
                                "!pageContent",
                                pageContent[0],
                            ),
                            pageContent[1],
                        )
            case "POST":
                match dir[0]:
                    case "__null":
                        del dir[0]
                        if not dir:
                            flask.abort(404)
                        match dir[0]:
                            case "server-update":
                                repo = git.cmd.Git(
                                    "https://github.com/Multiplex64/Multiplex64/"
                                )
                                repo.pull()
                                return "Updated PythonAnywhere successfully", 200
                            case _:
                                flask.abort(404)
                    case _:
                        flask.abort(404)
            case _:
                flask.abort(405)
    except Exception:
        return "Error 500 Internal Server Error (Flask Handler Error)", 500
