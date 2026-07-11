from flask import Blueprint, jsonify, request

from app.errors import AppError
from app.models import AIUseCase

governance_bp = Blueprint("governance", __name__)


@governance_bp.get("/status/")
def governance_status():
    """
    Mock watsonx.governance-style status endpoint.
    In a real project, this could call an external model inventory/governance platform.
    """
    use_case_id = request.args.get("usecaseId")

    if not use_case_id:
        raise AppError("usecaseId query parameter is required", 400)

    try:
        use_case_id = int(use_case_id)
    except ValueError:
        raise AppError("usecaseId must be a valid integer", 400)

    use_case = AIUseCase.query.get(use_case_id)

    if not use_case:
        raise AppError("Use case not found", 404)
    risk_category = use_case.risk_assessment.risk_category if use_case.risk_assessment else "UNKNOWN"

    explainability_required = risk_category in {"MEDIUM", "HIGH"}
    bias_check_required = use_case.model_type in {"ML", "GENAI"}
    drift_monitoring_required = use_case.model_type in {"ML", "GENAI"}

    return jsonify(
        {
            "modelInventoryId": f"AIGOV-{use_case.id:05d}",
            "useCaseId": use_case.id,
            "modelName": use_case.model_name,
            "governanceStatus": use_case.status,
            "riskCategory": risk_category,
            "biasCheckRequired": bias_check_required,
            "driftMonitoringRequired": drift_monitoring_required,
            "explainabilityRequired": explainability_required,
            "productionReadiness": use_case.status == "APPROVED",
        }
    ), 200
