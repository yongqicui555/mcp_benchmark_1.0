from flask import Flask, Blueprint

app = Flask(__name__)
bp = Blueprint("api", __name__, url_prefix="/api")


@app.route("/health")
def health():
    return {"ok": True}


@bp.route("/users", methods=["GET", "POST"])
def users():
    return []


@bp.route("/users/<int:id>", methods=["DELETE"])
def user(id):
    return ("", 204)


app.register_blueprint(bp)
