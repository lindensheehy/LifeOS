from flask import Blueprint, jsonify, request
from cache import cache

# Create a blueprint for our API
api_bp = Blueprint('api', __name__)

@api_bp.route('/api/journal/<date_str>', methods=['GET'])
def get_journal_day(date_str):
    """
    Client requests a day: GET /api/journal/2026-05-11
    """
    # The cache handles cache misses automatically
    data = cache.get_day(date_str)
    return jsonify(data)

@api_bp.route('/api/journal/month/<year_month>', methods=['GET'])
def get_journal_month(year_month):
    """
    Client requests a whole cache line: GET /api/journal/month/2026-05
    """
    data = cache.get_month_days(year_month)
    return jsonify(data)

@api_bp.route('/api/dropdowns', methods=['GET'])
def get_dropdowns():
    """
    Returns the permanently pinned util data.
    """
    # Fallback to empty dict if it doesn't exist
    return jsonify(cache.util_store.get('dropdowns', {}))

@api_bp.route('/api/journal/<date_str>/<section>', methods=['POST'])
def save_journal_section(date_str, section):
    """
    Client saves a specific section: POST /api/journal/2026-05-11/gym
    """
    # Security Failsafe: Prevent directory traversal
    if ".." in section or "/" in section or "\\" in section:
        return jsonify({"error": "Invalid section name"}), 400

    payload = request.json
    
    try:
        cache.save_section(date_str, section, payload)
        return jsonify({"status": "success", "message": f"Saved {section}"})
    except Exception as e:
        print(f"Error saving {section}: {e}")
        return jsonify({"error": "Failed to save to disk"}), 500
    
@api_bp.route('/api/heartbeat', methods=['GET'])
def health_check():
    return {"status": "alive"}, 200