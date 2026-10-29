"""Kleine Flask-app die de openingstijden van de gemeentelijke milieustraten toont."""
import json
from pathlib import Path

from flask import Flask, render_template

app = Flask(__name__)
DATA = json.loads((Path(__file__).parent / "static" / "milieustraten.json").read_text(encoding="utf-8"))


@app.route("/")
def index():
    return render_template("index.html", milieustraten=DATA)


if __name__ == "__main__":
    app.run()
