from app.errors import AppError

VALID_LEVELS = {"LOW", "MEDIUM", "HIGH"}
VALID_MODEL_TYPES = {"ML", "GENAI", "RULE_BASED"}


def normalize(value):
    if value is None:
        return None
    return str(value).strip().upper().replace(" ", "_")


def calculate_risk_score(payload):
    """
    Rule-based risk scoring engine.
    This simulates the type of governance scoring that could sit behind Appian.
    """
    model_type = normalize(payload.get("modelType"))
    customer_impact = normalize(payload.get("customerImpact"))
    regulatory_impact = normalize(payload.get("regulatoryImpact"))
    model_complexity = normalize(payload.get("modelComplexity"))
    uses_sensitive_data = bool(payload.get("usesSensitiveData", False))

    if model_type not in VALID_MODEL_TYPES:
        raise AppError("modelType must be one of: ML, GENAI, RULE_BASED", 400)
    if customer_impact not in VALID_LEVELS:
        raise AppError("customerImpact must be one of: LOW, MEDIUM, HIGH", 400)
    if regulatory_impact not in VALID_LEVELS:
        raise AppError("regulatoryImpact must be one of: LOW, MEDIUM, HIGH", 400)
    if model_complexity not in VALID_LEVELS:
        raise AppError("modelComplexity must be one of: LOW, MEDIUM, HIGH", 400)

    customer_impact_scores = {"LOW": 5, "MEDIUM": 15, "HIGH": 25}
    regulatory_impact_scores = {"LOW": 5, "MEDIUM": 15, "HIGH": 25}
    complexity_scores = {"LOW": 5, "MEDIUM": 15, "HIGH": 20}
    model_type_scores = {"RULE_BASED": 0, "ML": 5, "GENAI": 10}

    score = 0
    score += customer_impact_scores[customer_impact]
    score += regulatory_impact_scores[regulatory_impact]
    score += complexity_scores[model_complexity]
    score += model_type_scores[model_type]

    if uses_sensitive_data:
        score += 25

    score = min(score, 100)

    if score <= 30:
        risk_category = "LOW"
        required_approvals = ["RISK"]
    elif score <= 70:
        risk_category = "MEDIUM"
        required_approvals = ["RISK", "COMPLIANCE"]
    else:
        risk_category = "HIGH"
        required_approvals = ["RISK", "COMPLIANCE", "SECURITY"]

    return {
        "riskScore": score,
        "riskCategory": risk_category,
        "requiredApprovals": required_approvals,
        "normalizedInput": {
            "modelType": model_type,
            "customerImpact": customer_impact,
            "regulatoryImpact": regulatory_impact,
            "modelComplexity": model_complexity,
            "usesSensitiveData": uses_sensitive_data,
        },
    }
