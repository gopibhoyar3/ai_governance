from flask import Blueprint, jsonify, request

from app.risk import calculate_risk_score

risk_bp = Blueprint("risk", __name__)


@risk_bp.post("/calculate")
def calculate_risk():
    payload = request.get_json(silent=True) or {}
    result = calculate_risk_score(payload)
    return jsonify(result), 200
