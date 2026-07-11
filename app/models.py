from datetime import datetime, timezone

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class AIUseCase(db.Model):
    __tablename__ = "ai_use_cases"

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(150), nullable=False)
    business_unit = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # ML, GENAI, RULES_BASED
    description = db.Column(db.Text, nullable=True)
    submitted_by = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="IN_REVIEW")
    cloud_platform = db.Column(db.String(80), nullable=True)
    api_details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    risk_assessment = db.relationship(
        "ModelRiskAssessment",
        back_populates="use_case",
        uselist=False,
        cascade="all, delete-orphan",
    )
    approval_tasks = db.relationship(
        "ApprovalTask",
        back_populates="use_case",
        cascade="all, delete-orphan",
        order_by="ApprovalTask.id",
    )
    audit_logs = db.relationship(
        "AuditLog",
        back_populates="use_case",
        cascade="all, delete-orphan",
        order_by="AuditLog.id",
    )

    def to_summary_dict(self):
        return {
            "id": self.id,
            "modelName": self.model_name,
            "businessUnit": self.business_unit,
            "modelType": self.model_type,
            "submittedBy": self.submitted_by,
            "status": self.status,
            "riskCategory": self.risk_assessment.risk_category if self.risk_assessment else None,
            "riskScore": self.risk_assessment.total_risk_score if self.risk_assessment else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_detail_dict(self):
        data = self.to_summary_dict()
        data.update(
            {
                "description": self.description,
                "cloudPlatform": self.cloud_platform,
                "apiDetails": self.api_details,
                "riskAssessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
                "approvalTasks": [task.to_dict() for task in self.approval_tasks],
                "auditLogs": [log.to_dict() for log in self.audit_logs],
            }
        )
        return data


class ModelRiskAssessment(db.Model):
    __tablename__ = "model_risk_assessments"

    id = db.Column(db.Integer, primary_key=True)
    use_case_id = db.Column(db.Integer, db.ForeignKey("ai_use_cases.id"), nullable=False, unique=True)
    customer_impact = db.Column(db.String(20), nullable=False)
    uses_sensitive_data = db.Column(db.Boolean, nullable=False, default=False)
    regulatory_impact = db.Column(db.String(20), nullable=False)
    model_complexity = db.Column(db.String(20), nullable=False)
    total_risk_score = db.Column(db.Integer, nullable=False)
    risk_category = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    use_case = db.relationship("AIUseCase", back_populates="risk_assessment")

    def to_dict(self):
        return {
            "id": self.id,
            "useCaseId": self.use_case_id,
            "customerImpact": self.customer_impact,
            "usesSensitiveData": self.uses_sensitive_data,
            "regulatoryImpact": self.regulatory_impact,
            "modelComplexity": self.model_complexity,
            "riskScore": self.total_risk_score,
            "riskCategory": self.risk_category,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class ApprovalTask(db.Model):
    __tablename__ = "approval_tasks"

    id = db.Column(db.Integer, primary_key=True)
    use_case_id = db.Column(db.Integer, db.ForeignKey("ai_use_cases.id"), nullable=False)
    approver_role = db.Column(db.String(50), nullable=False)  # RISK, COMPLIANCE, SECURITY, etc.
    approver_name = db.Column(db.String(120), nullable=True)
    decision = db.Column(db.String(50), nullable=False, default="PENDING")
    comments = db.Column(db.Text, nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    use_case = db.relationship("AIUseCase", back_populates="approval_tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "useCaseId": self.use_case_id,
            "approverRole": self.approver_role,
            "approverName": self.approver_name,
            "decision": self.decision,
            "comments": self.comments,
            "approvedAt": self.approved_at.isoformat() if self.approved_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    use_case_id = db.Column(db.Integer, db.ForeignKey("ai_use_cases.id"), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    performed_by = db.Column(db.String(120), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    use_case = db.relationship("AIUseCase", back_populates="audit_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "useCaseId": self.use_case_id,
            "action": self.action,
            "performedBy": self.performed_by,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
