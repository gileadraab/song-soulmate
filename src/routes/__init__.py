"""
Route modules for Song Soulmate application.

This package contains all Flask route definitions and blueprints.
"""

from flask import Blueprint

# Create blueprint for main routes
main = Blueprint("main", __name__)


@main.route("/api/status")
def api_status():
    """API status endpoint"""
    from flask import jsonify

    return jsonify({"api": "active", "version": "1.0.0"})
