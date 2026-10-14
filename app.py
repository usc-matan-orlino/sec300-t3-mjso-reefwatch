"""ReefWatch Flask app.

Cosmos collections: surveys, equipment, partners.
"""

from bson import ObjectId
from flask import Flask, redirect, render_template, request, url_for

from db import get_collection

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
    """Show the equipment table. ?id=... selects a row to edit in the form."""
    collection = get_collection("equipment")
    # Sorted in Python: Cosmos DB only sorts on indexed fields (just _id by default).
    items = sorted(collection.find(), key=lambda item: item["name"].lower())

    selected = None
    selected_id = request.args.get("id")
    if selected_id:
        selected = collection.find_one({"_id": ObjectId(selected_id)})

    return render_template("equipment.html", items=items, selected=selected)


@app.route("/equipment/save", methods=["POST"])
def save_equipment():
    """Insert a new item, or update the item if the form has an id."""
    collection = get_collection("equipment")
    data = {
        "name": request.form["name"].strip(),
        "category": request.form["category"].strip(),
        "replacement_cost": float(request.form["replacement_cost"]),
        "available_quantity": int(request.form["available_quantity"]),
        "low_stock_threshold": int(request.form["low_stock_threshold"]),
        "status": request.form["status"].strip(),
    }

    item_id = request.form.get("id")
    if item_id:
        collection.update_one({"_id": ObjectId(item_id)}, {"$set": data})
    else:
        collection.insert_one(data)
    return redirect(url_for("equipment"))


@app.route("/equipment/delete", methods=["POST"])
def delete_equipment():
    """Delete the selected item."""
    get_collection("equipment").delete_one({"_id": ObjectId(request.form["id"])})
    return redirect(url_for("equipment"))


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
