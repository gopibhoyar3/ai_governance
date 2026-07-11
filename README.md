# AI Governance Control Hub - Flask Backend

A local backend for an Appian AI governance workflow project.

This backend provides:

- AI use-case submission APIs
- Rule-based risk scoring
- Multi-stage approval tasks
- Audit logs
- Dashboard summary APIs
- Mock watsonx.governance-style model status API

Tech stack:

- Python Flask
- PostgreSQL
- Flask-SQLAlchemy
- Flask-Migrate

---

## 1. Project structure

```text
ai-governance-control-hub-backend/
  app/
    routes/
      dashboard.py
      governance.py
      health.py
      risk_routes.py
      use_cases.py
    __init__.py
    config.py
    errors.py
    extensions.py
    models.py
    risk.py
  .env.example
  create_db.py
  README.md
  requirements.txt
  run.py
```


## 7. API reference

All error responses share this shape:

```json
{
  "error": "<message>"
}
```

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service liveness check |

---

### Risk

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/risk/calculate` | Calculate a risk score without creating a use case |

**Calculate risk only**

```bash
curl -X POST http://localhost:5000/api/risk/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "modelType": "GENAI",
    "customerImpact": "HIGH",
    "usesSensitiveData": true,
    "regulatoryImpact": "HIGH",
    "modelComplexity": "HIGH"
  }'
```

---

### Use cases

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/use-cases` | Submit a new AI use case |
| GET | `/api/use-cases` | List use cases (optional filters) |
| GET | `/api/use-cases/byId?usecaseId={id}` | Get one use case by ID |
| POST | `/api/use-cases/decision?usecaseId={id}` | Submit an approval/rejection decision |
| POST | `/api/use-cases/{id}/resubmit` | Resubmit a use case after more info was requested |

**Submit AI use case**

```bash
curl -X POST http://localhost:5000/api/use-cases \
  -H "Content-Type: application/json" \
  -d '{
    "modelName": "Transaction Failure Prediction Model",
    "businessUnit": "Regulatory Reporting",
    "modelType": "ML",
    "description": "Predicts transaction failures before regulatory submission.",
    "submittedBy": "Gopi",
    "customerImpact": "MEDIUM",
    "usesSensitiveData": true,
    "regulatoryImpact": "HIGH",
    "modelComplexity": "MEDIUM",
    "cloudPlatform": "AWS",
    "apiDetails": "POST /predict/failure"
  }'
```

**List all use cases**

```bash
curl http://localhost:5000/api/use-cases
```

Filter examples:

```bash
curl "http://localhost:5000/api/use-cases?status=IN_REVIEW"
curl "http://localhost:5000/api/use-cases?riskCategory=HIGH"
```

**Get one use case by ID**

`usecaseId` is passed as a query parameter, not a path segment:

```bash
curl "http://localhost:5000/api/use-cases/byId?usecaseId=1"
```

**Submit approval decision**

`usecaseId` is passed as a query parameter:

```bash
curl -X POST "http://localhost:5000/api/use-cases/decision?usecaseId=1" \
  -H "Content-Type: application/json" \
  -d '{
    "approverRole": "RISK",
    "approverName": "Risk Reviewer 1",
    "decision": "APPROVED",
    "comments": "Risk controls look acceptable."
  }'
```

Valid `decision` values:

```text
APPROVED
REJECTED
MORE_INFO_REQUIRED
```

**Resubmit after more information requested**

```bash
curl -X POST http://localhost:5000/api/use-cases/1/resubmit \
  -H "Content-Type: application/json" \
  -d '{
    "performedBy": "Gopi",
    "comments": "Added updated risk control details."
  }'
```

---

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard/summary` | Aggregate counts across use cases, risk, and approvals |

```bash
curl http://localhost:5000/api/dashboard/summary
```

---

### Governance

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/governance/status?usecaseId={id}` | Mock watsonx.governance-style model status |

`usecaseId` is passed as a query parameter (no trailing slash):

```bash
curl "http://localhost:5000/api/governance/status?usecaseId=1"
```

---

## 8. How Appian should integrate with this backend

### Appian objects to create

1. Record Type: `AI Use Case`
2. Record Type: `Approval Task`
3. Record Type: `Risk Assessment`
4. Interface: `Submit AI Use Case Form`
5. Interface: `Review AI Use Case Screen`
6. Interface: `Governance Dashboard`
7. Integration: `POST /api/use-cases`
8. Integration: `GET /api/use-cases`
9. Integration: `GET /api/use-cases/byId?usecaseId={id}`
10. Integration: `POST /api/use-cases/decision?usecaseId={id}`
11. Integration: `GET /api/dashboard/summary`

### Appian workflow idea

```text
Submit AI Use Case Form
        ↓
Call POST /api/use-cases
        ↓
Display created approval tasks
        ↓
Reviewer opens task screen
        ↓
Call POST /api/use-cases/decision?usecaseId={id}
        ↓
Refresh record/dashboard
```

---

## 9. Resume bullet after building this

```text
Built an Appian-integrated AI Governance Control Hub using Flask, PostgreSQL, and REST APIs to automate model risk scoring, multi-stage approval workflows, audit logging, and governance dashboards for AI/ML use cases across risk, compliance, security, and architecture teams.
```
