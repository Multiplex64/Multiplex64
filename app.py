from flask import Flask, abort, request
import os
import git

# flask install required!


def get(page: str):
    try:
        with open(page, "r") as file:
            return file.read()
    except Exception:
        with open("main/error404.html", "r") as file:
            return file.read()


app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def main(path):
    dir = path.split("/")
    match request.method:
        case "GET":
            match dir[0]:
                case "null":
                    del dir[0]
                    if not dir:
                        return get("main/error404.html")
                    match dir[0]:
                        case "page":
                            del dir[0]
                            if os.path.isfile("main/pages/" + "/".join(dir) + "/index.html"):
                                return get("main/pages/" + "/".join(dir) + "/index.html")
                            else:
                                return get("main/error404.html")
                        case _:
                            return get("main/error404.html")
                case _:
                    return get("main/_index.html").replace(
                        "!pageContent",
                        main("null/page/" + "/".join(dir)),
                    )
        case "POST":
            match dir[0]:
                case "null":
                    del dir[0]
                    if not dir:
                        abort(404)
                    match dir[0]:
                        case "server-update":
                            repo = git.Repo('https://github.com/Multiplex64/Multiplex64')
                            origin = repo.remotes.origin
                            origin.pull()
                            return 'Updated PythonAnywhere successfully', 200
                        case _:
                            abort(404)
                case _:
                    abort(404)
        case _:
            abort(405)