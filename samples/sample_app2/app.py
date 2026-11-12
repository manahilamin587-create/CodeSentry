import hashlib

import yaml
from flask import Flask, request

app = Flask(__name__)


@app.route("/hash")
def make_hash():
    pw = request.args.get("pw", "")
    return hashlib.md5(pw.encode()).hexdigest()


@app.route("/load", methods=["POST"])
def load_config():
    return str(yaml.load(request.data))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")