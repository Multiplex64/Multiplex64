from flask import Flask, abort, request
import os

# flask install required!


def get(page: str):
    try:
        with open(page, "r") as file:
            return file.read()
    except Exception:
        with open("error404.html", "r") as file:
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
                        return get("error404.html")
                    match dir[0]:
                        case "page":
                            del dir[0]
                            if os.path.isfile("pages/" + "/".join(dir) + "/index.html"):
                                return get("pages/" + "/".join(dir) + "/index.html")
                            else:
                                return get("error404.html")
                        case _:
                            return get("error404.html")
                case _:
                    return get("_index.html").replace(
                        "!pageContent",
                        main("null/page/" + "/".join(dir)),
                    )
        case "POST":
            match dir[0]:
                case _:
                    abort(404)
        case _:
            abort(405)