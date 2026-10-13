"""ReefWatch Flask app (skeleton: pages only, no database logic yet)."""

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/surveys")
def surveys():
    return render_template("surveys.html")


@app.route("/surveys/new")
def new_survey():
    return render_template("new_survey.html")


@app.route("/equipment")
def equipment():
    return render_template("equipment.html")


@app.route("/partners")
def partners():
    return render_template("partners.html")


@app.route("/summaries")
def summaries():
    return render_template("summaries.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)
