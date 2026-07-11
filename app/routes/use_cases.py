from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import desc

from app.errors import AppError
from app.extensions import db
from app.models import AIUseCase, ApprovalTask, AuditLog, ModelRiskAssessment
from app.risk import calculate_risk_score

use_cases_bp = Blueprint("use_cases", __name__)

REQUIRED_CREATE_FIELDS = [
    "modelName",
    "businessUnit",
    "modelType",
    "submittedBy",
    "customerImpact",
    "usesSensitiveData",
    "regulatoryImpact",
    "modelComplexity",
]

VALID_DECISIONS = {"APPROVED", "REJECTED", "MORE_INFO_REQUIRED"}


def require_fields(payload, fields):
    missing = [field for field in fields if field not in payload or payload.get(field) in (None, "")]
    if missing:
        raise AppError(f"Missing required fields: {', '.join(missing)}", 400)


def add_audit(use_case_id, action, performed_by, details=None):
    db.session.add(
        AuditLog(
            use_case_id=use_case_id,
            action=action,
            performed_by=performed_by,
            details=details,
        )
    )


@use_cases_bp.post("")
def create_use_case():
    payload = request.get_json(silent=True) or {}
    require_fields(payload, REQUIRED_CREATE_FIELDS)

    risk_result = calculate_risk_score(payload)
    normalized = risk_result["normalizedInput"]

    use_case = AIUseCase(
        model_name=payload["modelName"].strip(),
        business_unit=payload["businessUnit"].strip(),
        model_type=normalized["modelType"],
        description=payload.get("description"),
        submitted_by=payload["submittedBy"].strip(),
        status="IN_REVIEW",
        cloud_platform=payload.get("cloudPlatform"),
        api_details=payload.get("apiDetails"),
    )
    db.session.add(use_case)
    db.session.flush()

    risk_assessment = ModelRiskAssessment(
        use_case_id=use_case.id,
        customer_impact=normalized["customerImpact"],
        uses_sensitive_data=normalized["usesSensitiveData"],
        regulatory_impact=normalized["regulatoryImpact"],
        model_complexity=normalized["modelComplexity"],
        total_risk_score=risk_result["riskScore"],
        risk_category=risk_result["riskCategory"],
    )
    db.session.add(risk_assessment)

    for approver_role in risk_result["requiredApprovals"]:
        db.session.add(
            ApprovalTask(
                use_case_id=use_case.id,
                approver_role=approver_role,
                decision="PENDING",
            )
        )

    add_audit(
        use_case.id,
        "USE_CASE_SUBMITTED",
        use_case.submitted_by,
        f"Risk category: {risk_result['riskCategory']}, score: {risk_result['riskScore']}",
    )

    db.session.commit()
    return jsonify(use_case.to_detail_dict()), 201


@use_cases_bp.get("")
def list_use_cases():
    status = request.args.get("status")
    risk_category = request.args.get("riskCategory")

    query = AIUseCase.query

    if status:
        query = query.filter(AIUseCase.status == status.strip().upper())

    if risk_category:
        query = query.join(ModelRiskAssessment).filter(
            ModelRiskAssessment.risk_category == risk_category.strip().upper()
        )

    use_cases = query.order_by(desc(AIUseCase.created_at)).all()
    return jsonify([item.to_summary_dict() for item in use_cases]), 200


@use_cases_bp.route("/byId", methods=["GET"])
def get_use_case_by_id_query_param():
    usecase_id = request.args.get("usecaseId")

    if not usecase_id:
        raise AppError("usecaseId query parameter is required", 400)

    try:
        usecase_id = int(usecase_id)
    except ValueError:
        raise AppError("usecaseId must be a valid integer", 400)

    use_case = AIUseCase.query.get(usecase_id)

    if not use_case:
        raise AppError("Use case not found", 404)

    return jsonify(use_case.to_detail_dict()), 200


@use_cases_bp.post("/decision")
def submit_decision():
    use_case_id = request.args.get("usecaseId")

    if not use_case_id:
        raise AppError("usecaseId query parameter is required", 400)

    try:
        use_case_id = int(use_case_id)
    except ValueError:
        raise AppError("usecaseId must be a valid integer", 400)

    payload = request.get_json(silent=True) or {}
    require_fields(payload, ["approverRole", "approverName", "decision"])

    decision = payload["decision"].strip().upper()
    approver_role = payload["approverRole"].strip().upper()
    approver_name = payload["approverName"].strip()
    comments = payload.get("comments")

    if decision not in VALID_DECISIONS:
        raise AppError("decision must be one of: APPROVED, REJECTED, MORE_INFO_REQUIRED", 400)

    use_case = AIUseCase.query.get(use_case_id)

    if not use_case:
        raise AppError("Use case not found", 404)

    if use_case.status in {"APPROVED", "REJECTED"}:
        raise AppError(f"Use case is already {use_case.status}", 400)

    task = ApprovalTask.query.filter_by(
        use_case_id=use_case_id,
        approver_role=approver_role,
        decision="PENDING",
    ).first()

    if not task:
        raise AppError(f"No pending approval task found for role: {approver_role}", 404)

    task.approver_name = approver_name
    task.decision = decision
    task.comments = comments
    task.approved_at = datetime.now(timezone.utc)

    if decision == "REJECTED":
        use_case.status = "REJECTED"
    elif decision == "MORE_INFO_REQUIRED":
        use_case.status = "MORE_INFO_REQUIRED"
    else:
        pending_count = ApprovalTask.query.filter_by(
            use_case_id=use_case_id,
            decision="PENDING",
        ).count()
        use_case.status = "APPROVED" if pending_count == 0 else "IN_REVIEW"

    add_audit(
        use_case_id,
        f"{approver_role}_{decision}",
        approver_name,
        comments,
    )

    db.session.commit()
    return jsonify(use_case.to_detail_dict()), 200


@use_cases_bp.post("/<int:use_case_id>/resubmit")
def resubmit_use_case(use_case_id):
    payload = request.get_json(silent=True) or {}
    performed_by = payload.get("performedBy", "SYSTEM")
    comments = payload.get("comments", "Use case resubmitted after additional information.")

    use_case = AIUseCase.query.get_or_404(use_case_id)

    if use_case.status != "MORE_INFO_REQUIRED":
        raise AppError("Only MORE_INFO_REQUIRED use cases can be resubmitted", 400)

    for task in use_case.approval_tasks:
        if task.decision == "MORE_INFO_REQUIRED":
            task.decision = "PENDING"
            task.approver_name = None
            task.comments = None
            task.approved_at = None

    use_case.status = "IN_REVIEW"
    add_audit(use_case_id, "USE_CASE_RESUBMITTED", performed_by, comments)
    db.session.commit()

    return jsonify(use_case.to_detail_dict()), 200
