from flask import Flask, abort, request, send_from_directory
import os
import git

# Flask and GitPython install required! (Through Pip)


def get(page: str):
    try:
        with open(page, "r") as file:
            return file.read()
    except Exception:
        with open("pages/null/errors/404.html", "r") as file:
            return file.read()


app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def main(path):
    dir = path.split("/")
    match request.method:
        case "GET":
            if os.path.splitext("/".join(dir))[1]:
                if os.path.isfile("pages/" + "/".join(dir)):
                    return send_from_directory("pages", "/".join(dir))
                return get("pages/null/errors/404.html")
            else:
                return get("pages/null/global/index.html").replace(
                    "!pageContent",
                    get("pages/" + "/".join(dir) + "/index.html"),
                )
        case "POST":
            match dir[0]:
                case "null":
                    del dir[0]
                    if not dir:
                        abort(404)
                    match dir[0]:
                        case "server-update":
                            repo = git.cmd.Git("https://github.com/Multiplex64/Multiplex64/")
                            repo.pull()
                            return "Updated PythonAnywhere successfully", 200
                        case _:
                            abort(404)
                case _:
                    abort(404)
        case _:
            abort(405)
