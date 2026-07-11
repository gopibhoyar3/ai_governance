from flask import Blueprint, jsonify
from sqlalchemy import func

from app.extensions import db
from app.models import AIUseCase, ApprovalTask, ModelRiskAssessment

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/summary")
def dashboard_summary():
    total_use_cases = AIUseCase.query.count()

    status_counts = dict(
        db.session.query(AIUseCase.status, func.count(AIUseCase.id))
        .group_by(AIUseCase.status)
        .all()
    )

    risk_counts = dict(
        db.session.query(ModelRiskAssessment.risk_category, func.count(ModelRiskAssessment.id))
        .group_by(ModelRiskAssessment.risk_category)
        .all()
    )

    pending_approvals = ApprovalTask.query.filter_by(decision="PENDING").count()
    high_risk_pending = (
        db.session.query(AIUseCase)
        .join(ModelRiskAssessment)
        .filter(ModelRiskAssessment.risk_category == "HIGH")
        .filter(AIUseCase.status == "IN_REVIEW")
        .count()
    )

    return jsonify(
        {
            "totalUseCases": total_use_cases,
            "statusCounts": status_counts,
            "riskCounts": risk_counts,
            "pendingApprovals": pending_approvals,
            "highRiskPending": high_risk_pending,
        }
    ), 200
