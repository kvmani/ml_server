import json
import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request

"""Feedback submission and rendering routes."""

bp = Blueprint("feedback", __name__)

# Path to feedback file relative to package
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feedback.json")

# Ensure file exists
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, "w") as f:
        json.dump({"feedback": []}, f)


@bp.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    try:
        name = request.form.get("name")
        email = request.form.get("email")
        rating = int(request.form.get("rating"))
        feedback_text = request.form.get("feedback")

        if not all([name, email, rating, feedback_text]):
            return (
                jsonify({"success": False, "message": "All fields are required"}),
                400,
            )

        feedback_data = {
            "name": name,
            "email": email,
            "rating": rating,
            "feedback": feedback_text,
            "date": datetime.now().isoformat(),
            "page": request.referrer,
        }

        with open(FEEDBACK_FILE, "r+") as f:
            data = json.load(f)
            data["feedback"].insert(0, feedback_data)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        return jsonify({"success": True})
    except Exception as e:
        bp.logger.error(f"Feedback error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


@bp.route("/admin/feedback")
def admin_feedback():
    token = request.args.get("token")
    admin_token = current_app.config.get("ADMIN_TOKEN")
    if admin_token and token != admin_token:
        return "Unauthorized", 401

    page = int(request.args.get("page", 1))
    per_page = 10
    with open(FEEDBACK_FILE) as f:
        data = json.load(f).get("feedback", [])
    start = (page - 1) * per_page
    entries = data[start : start + per_page]
    return render_template("admin_feedback.html", feedback=entries, page=page)
