"""Optional API key authentication for the Flask dashboard."""
from flask import request, jsonify


class DashboardAuth:
    """Applies API key authentication to Flask API routes."""

    def __init__(self, api_key):
        self._api_key = api_key

    def apply(self, app):
        @app.before_request
        def check_api_key():
            if not request.path.startswith("/api/"):
                return None
            key = request.headers.get("X-API-Key") or request.args.get("key")
            if key != self._api_key:
                return jsonify({"error": "unauthorized"}), 401
