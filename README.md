# ⚖️ Decision Companion System

> A transparent, explainable decision-making tool that evaluates real-world options using **Weighted Multi-Criteria Decision Making (WMCDM)** — no black-box AI.

**Author:** Samuel Baiju  
**Date:** March 2026  
**Stack:** Python · FastAPI · Streamlit · Pydantic

---

## 📌 Understanding of the Problem

The task was to build a system that helps users make better decisions by evaluating options against user-defined criteria. The key constraints I identified were:

1. **Dynamic Input** — Users must be able to define their own criteria, weights, and options at runtime. The system cannot be hardcoded for a specific domain (e.g., only for cars or only for hiring).

2. **Explainability** — Users must understand *why* an option ranks higher. A simple "Option A is best" is not enough — the system must show the math and reasoning behind every ranking.

3. **Transparency Over AI** — The system must not rely entirely on AI. Scoring and ranking must be deterministic and mathematically traceable. AI can assist development, but the core decision engine must be rule-based.

4. **Thinking Over Features** — The evaluation prioritizes the design process, trade-off reasoning, and architectural maturity over the number of features shipped.

My interpretation: this is fundamentally a **trust problem**. Users will only adopt a decision-support tool if they can verify and understand its output. That's why I chose WMCDM — every score can be traced back to `normalized_weight × raw_score`.

---

## 📋 Assumptions Made

| Assumption | Rationale |
|-----------|-----------|
| **Scores range from 0.0 to 10.0** | Provides enough granularity for meaningful comparison without overwhelming users. A 0–100 scale adds noise; a 1–5 scale is too coarse. |
| **Weights must be greater than 0** | A weight of 0 means the criterion doesn't matter — it should be removed entirely, not weighted at zero. Negative weights have no meaningful interpretation in WMCDM. |
| **No persistent storage needed** | The assignment focuses on the decision engine, not data management. Decisions are evaluated in real-time and results are displayed immediately. |
| **Single-user, local deployment** | The system runs on `localhost` and does not need authentication, multi-tenancy, or cloud deployment for this scope. |
| **Criteria names must be unique** | Duplicate criteria names would cause ambiguity in score mapping and contribution tracking. |
| **All options must be scored on all criteria** | Partial scoring would require imputation logic (e.g., default scores), which adds hidden assumptions. Instead, the system requires complete data. |

---

## 🏗️ Why I Structured the Solution This Way

### Client-Server Architecture (FastAPI + Streamlit)

I chose to separate the system into a **FastAPI backend** and a **Streamlit frontend** rather than building a monolithic app. Here's why:

```
┌────────────────┐     HTTP/JSON      ┌─────────────────────────┐
│   Streamlit    │ ──── POST ────────→│   FastAPI Backend       │
│   Frontend     │                    │                         │
│   (UI only)    │ ←── JSON Response──│  ├─ Pydantic Validation │
│   Port: 8501   │                    │  ├─ Decision Engine     │
└────────────────┘                    │  └─ Explanation Service │
                                      │       Port: 8001        │
                                      └─────────────────────────┘
```

**Why not a single Streamlit app?**
- Mixing UI logic with scoring logic violates separation of concerns
- The backend can be tested independently (via Swagger UI, `curl`, or automated tests)
- The architecture mirrors production systems — demonstrating real engineering maturity

**Why not a CLI tool?**
- Poor interactivity — can't dynamically adjust sliders and see results
- Harder to demonstrate and visually verify

**Why not Django?**
- Too heavy for a focused decision engine
- FastAPI provides automatic OpenAPI docs, built-in validation, and better performance for API-first design

### Modular Backend

The backend is split into three layers:

```
backend/app/
├── main.py                          ← Routing only (thin controller)
├── models/
│   └── schemas.py                   ← Input/output validation (Pydantic)
└── services/
    ├── decision_engine.py           ← WMCDM scoring + ranking
    └── explanation_service.py       ← Rule-based explanation generation
```

Each module has a **single responsibility**:
- `schemas.py` — validates input, catches bad data before it reaches the engine
- `decision_engine.py` — does the math, nothing else
- `explanation_service.py` — generates human-readable explanations from the math

This makes the system **testable**, **maintainable**, and **easy to extend**.

---

## 🧮 Design Decisions and Trade-offs

### Decision 1: WMCDM Over AI-Based Ranking

| Factor | WMCDM | AI/LLM Ranking |
|--------|-------|-----------------|
| Deterministic | ✅ Same input = same output | ❌ May vary between runs |
| Explainable | ✅ Every score is traceable | ❌ Black box reasoning |
| Transparent | ✅ User controls all weights | ❌ Hidden model biases |
| Assignment fit | ✅ Meets "not entirely AI" rule | ❌ Violates constraint |

**Trade-off accepted:** WMCDM doesn't "learn" or improve over time. It's purely mathematical. But for this scope, transparency matters more than adaptiveness.

### Decision 2: Weight Normalization

**The problem:** If User A defines weights `[10, 10, 10]` and User B defines `[1, 1, 1]`, raw weighted sums would produce different scales, making results incomparable.

**The fix:**
```
normalized_weight = weight / total_weight
```

This ensures all weights always sum to 1.0, and final scores stay on a consistent 0–10 scale.

**Trade-off accepted:** Users might expect that doubling a weight from 5 to 10 "doubles" its importance. With normalization, it depends on the *relative* proportion. This is mathematically correct but potentially unintuitive — the contribution breakdown in results helps clarify this.

### Decision 3: Rule-Based Explanations (Not AI-Generated)

The explanation service identifies:
1. **Top contributor** — the criterion with the highest absolute contribution to the final score
2. **Trade-offs** — criteria where the option performed below 70% of its maximum possible contribution

**Why 70%?** I tested with 50% (too lenient — missed obvious weaknesses), 90% (too strict — flagged everything), and settled on 70% as a balanced threshold.

**Trade-off accepted:** The explanations are formulaic, not conversational. An LLM could generate more natural-sounding text, but it would sacrifice determinism and traceability.

### Decision 4: Layered Validation (Frontend + Backend)

| Layer | What It Catches | Why |
|-------|-----------------|-----|
| **Frontend** (Streamlit) | Empty names, missing criteria/options | Prevents unnecessary API calls |
| **Backend** (Pydantic) | Type errors, range violations, duplicates, missing scores | Authoritative validation — frontend can be bypassed |

**Trade-off accepted:** Some checks are duplicated across layers. This is intentional — the backend must never trust the frontend.

---

## ⚠️ Edge Cases Considered

| Edge Case | What Could Go Wrong | How It's Handled |
|-----------|---------------------|------------------|
| **Duplicate criteria names** | Double-counting in score calculation | `validate_request()` rejects with 400 error |
| **Missing scores for a criterion** | `KeyError` during calculation | Cross-reference check in Pydantic validator |
| **Extra scores for unknown criteria** | Ignored data, potential confusion | Reverse cross-reference check |
| **Weight = 0 or negative** | Division by zero or meaningless math | `Field(gt=0)` enforces positive weights |
| **Score outside 0–10** | Unfair scaling | `@model_validator` range check |
| **Zero total weight** | Division by zero in normalization | Sum validation (`total_weight > 0`) |
| **Empty criteria/options list** | Crash on empty iteration | Length check before processing |
| **Perfect tie (equal scores)** | Ambiguous ranking | Both options get same score; ranked by input order |
| **One dominant criterion (99% weight)** | Minor criteria become irrelevant | Handled correctly — normalization ensures proportional influence |
| **Non-JSON backend response** | `JSONDecodeError` crash in frontend | Try/except wrapper with graceful error message |

---

## 🚀 How to Run the Project

### Prerequisites

- Python 3.10+
- pip

### 1. Clone the Repository

```bash
git clone <repository-url>
cd decision_companion
```

### 2. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
pip install -r requirements.txt
```

### 3. Start the Backend (FastAPI)

```bash
cd backend
python -m uvicorn app.main:app --port 8001 --reload
```

The API will be available at: `http://localhost:8001`  
Swagger documentation: `http://localhost:8001/docs`

### 4. Start the Frontend (Streamlit)

In a **separate terminal**:

```bash
cd frontend
python -m streamlit run streamlit_app.py
```

The app will open at: `http://localhost:8501`

### 5. Use the Application

1. Enter a **decision name** (e.g., "Choosing a New Car")
2. Add **criteria** with weights (e.g., Price: 5, Safety: 4, Fuel Efficiency: 3)
3. Add **options** and score each one from 0 to 10 on every criterion
4. Click **🚀 Evaluate Decision**
5. View the ranked results table and expandable rule-based explanations

### Example API Request (Direct)

You can also call the backend directly:

```bash
curl -X POST http://localhost:8001/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "decision_name": "Choosing a New Car",
    "criteria": [
      {"name": "Price", "weight": 5},
      {"name": "Fuel Efficiency", "weight": 3},
      {"name": "Safety", "weight": 4}
    ],
    "options": [
      {"name": "Car A", "scores": {"Price": 9.0, "Fuel Efficiency": 7.0, "Safety": 3.0}},
      {"name": "Car B", "scores": {"Price": 4.0, "Fuel Efficiency": 6.0, "Safety": 9.0}},
      {"name": "Car C", "scores": {"Price": 7.0, "Fuel Efficiency": 8.0, "Safety": 8.0}}
    ]
  }'
```

---

## 📁 Project Structure

```
decision_companion/
├── .gitignore                         # Ignores env, test artifacts, output files
├── README.md                          # This file
├── BUILD_PROCESS.md                   # Full build journey and thinking process
├── DESIGN_DIAGRAMS.md                 # Architecture, Data Flow, Component, Logic diagrams
├── RESEARCH_LOG.md                    # Transparent AI usage and research log
│
├── backend/
│   ├── requirements.txt               # fastapi, pydantic, uvicorn
│   └── app/
│       ├── __init__.py
│       ├── main.py                    # FastAPI app, CORS, /evaluate endpoint
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py             # Pydantic models with comprehensive validation
│       └── services/
│           ├── __init__.py
│           ├── decision_engine.py     # WMCDM scoring engine
│           └── explanation_service.py # Rule-based explanation generator
│
└── frontend/
    ├── requirements.txt               # streamlit, requests, pandas
    └── streamlit_app.py               # Interactive Streamlit UI
```

---

## 🔮 What I Would Improve With More Time

### 1. Automated Test Suite
Add `pytest` unit tests for the decision engine and explanation service. Test edge cases programmatically instead of manually. Example:

```python
def test_perfect_tie():
    """Equal weights + mirrored scores should produce identical final scores."""
    result = evaluate_decision(request_with_mirrored_options)
    assert result.ranking[0].final_score == result.ranking[1].final_score
```

### 2. Persistent Decision History
Add a lightweight database (SQLite or JSON file storage) to save past decisions. This would enable:
- Comparing decisions over time
- Re-evaluating with adjusted weights
- Sharing decision results with others

### 3. Visualization Dashboard
Add interactive charts using Plotly or Matplotlib:
- **Radar chart** comparing options across all criteria
- **Bar chart** showing contribution breakdowns side by side
- **Sensitivity analysis** — how does the ranking change if a weight is adjusted?

### 4. Containerization (Docker)
Create `Dockerfile` and `docker-compose.yml` to:
- Eliminate port conflict issues (like the one I debugged during development)
- Enable one-command deployment: `docker-compose up`
- Ensure consistent environments across machines

### 5. User Authentication & Multi-Tenancy
Add login functionality so multiple users can:
- Save their own decisions privately
- Share evaluations with team members
- Maintain separate criteria templates per domain

### 6. Advanced Explanation Generation
Use an LLM (with guardrails) to generate more natural-sounding explanations while keeping the underlying math deterministic. The LLM would only rephrase math-derived insights, never alter the scoring logic.

### 7. CI/CD Pipeline
Set up GitHub Actions to:
- Run tests on every push
- Lint code with `flake8` or `ruff`
- Build and push Docker images automatically

---

## 📚 Related Documentation

| Document | Description |
|----------|-------------|
| [BUILD_PROCESS.md](BUILD_PROCESS.md) | Complete thinking journey — from problem analysis to debugging |
| [DESIGN_DIAGRAMS.md](DESIGN_DIAGRAMS.md) | Architecture, Data Flow, Component, and Decision Logic diagrams |
| [RESEARCH_LOG.md](RESEARCH_LOG.md) | Transparent record of all AI usage and research decisions |

---

## 🔑 Core Principle

> *The system's ranking engine is **mathematically explicit, deterministic, and fully transparent**. Every score can be traced back to `normalized_weight × raw_score`. No hidden heuristics, no black-box AI, no opaque reasoning.*
