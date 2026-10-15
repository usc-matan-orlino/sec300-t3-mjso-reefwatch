"""ReefWatch Flask app.

Cosmos collections: surveys, equipment, partners.
"""

import os
from datetime import date

from bson import ObjectId
from flask import Flask, redirect, render_template, request, url_for

from db import get_collection
from summary import generate_summary, get_summaries, start_scheduler

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/surveys")
def surveys():
    """List all surveys, newest first."""
    # Sorted in Python: Cosmos DB only sorts on indexed fields.
    items = sorted(get_collection("surveys").find(),
                   key=lambda survey: survey["survey_date"], reverse=True)
    return render_template("surveys.html", items=items)


@app.route("/surveys/new", methods=["GET", "POST"])
def new_survey():
    """Show the survey form (GET) or save a survey and reduce equipment stock (POST)."""
    equipment_collection = get_collection("equipment")
    equipment_items = sorted(equipment_collection.find(), key=lambda item: item["name"].lower())
    error = None

    if request.method == "POST":
        # Work out which equipment was used and check there is enough stock.
        equipment_used = []
        for item in equipment_items:
            quantity = int(request.form.get(f"qty_{item['_id']}") or 0)
            if quantity > item["available_quantity"]:
                error = f"Not enough {item['name']}: only {item['available_quantity']} available."
            if quantity > 0:
                equipment_used.append({
                    "equipment_id": str(item["_id"]),
                    "name": item["name"],
                    "quantity": quantity,
                })

        if error is None:
            get_collection("surveys").insert_one({
                "survey_date": request.form["survey_date"],
                "researcher": {
                    "name": request.form["researcher_name"].strip(),
                    "email": request.form["researcher_email"].strip(),
                },
                "species_observed": [s.strip() for s in request.form["species"].split(",") if s.strip()],
                "equipment_used": equipment_used,
                "survey_cost": float(request.form["survey_cost"]),
            })
            # Reduce the available quantity of each item used.
            for used in equipment_used:
                equipment_collection.update_one(
                    {"_id": ObjectId(used["equipment_id"])},
                    {"$inc": {"available_quantity": -used["quantity"]}},
                )
            return redirect(url_for("surveys"))

    return render_template("new_survey.html", equipment_items=equipment_items,
                           error=error, form=request.form, today=date.today().isoformat())


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
    """Show the partners table. ?id=... selects a row to edit in the form."""
    collection = get_collection("partners")
    items = sorted(collection.find(), key=lambda item: item["organisation_name"].lower())

    selected = None
    selected_id = request.args.get("id")
    if selected_id:
        selected = collection.find_one({"_id": ObjectId(selected_id)})

    return render_template("partners.html", items=items, selected=selected)


@app.route("/partners/save", methods=["POST"])
def save_partner():
    """Insert a new partner, or update the partner if the form has an id."""
    collection = get_collection("partners")

    # Conservation areas are typed as a comma-separated list.
    areas = [a.strip() for a in request.form["conservation_areas"].split(",") if a.strip()]
    data = {
        "organisation_name": request.form["organisation_name"].strip(),
        "contact": {
            "name": request.form["contact_name"].strip(),
            "email": request.form["contact_email"].strip(),
            "phone": request.form["contact_phone"].strip(),
        },
        "conservation_areas": areas,
    }

    partner_id = request.form.get("id")
    if partner_id:
        collection.update_one({"_id": ObjectId(partner_id)}, {"$set": data})
    else:
        collection.insert_one(data)
    return redirect(url_for("partners"))


@app.route("/partners/delete", methods=["POST"])
def delete_partner():
    """Delete the selected partner."""
    get_collection("partners").delete_one({"_id": ObjectId(request.form["id"])})
    return redirect(url_for("partners"))


@app.route("/summaries", methods=["GET", "POST"])
def summaries():
    """List stored daily summaries. POST generates the summary for a date."""
    message = None
    success = False
    if request.method == "POST":
        success, message = generate_summary(request.form["summary_date"])

    return render_template("summaries.html", items=get_summaries(), message=message,
                           success=success, today=date.today().isoformat())


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    # The debug reloader runs this file twice; only start the scheduler in the
    # process that serves requests, so the summary is not generated twice.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_scheduler()
    app.run(debug=True)
