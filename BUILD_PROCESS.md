# 🔨 BUILD PROCESS — Decision Companion System

> **Author:** Samuel Baiju  
> **Date:** March 2026  
> **Stack:** FastAPI (Backend) + Streamlit (Frontend) + Python  
> **Core Algorithm:** Weighted Multi-Criteria Decision Making (WMCDM)

This document captures my complete thinking process — from analyzing the problem, making architectural trade-offs, evolving the design, debugging production issues, and validating correctness through rigorous testing.

---

## 1. 🧠 How I Started — Problem Analysis

I began by carefully analyzing the problem statement. The key signals from the assignment were:

- The system **must not be a static comparison** — it needs to process dynamic user input.
- The user must **dynamically define criteria and options** at runtime.
- The system must be **explainable** — users should understand *why* an option ranks higher.
- AI usage is allowed but **must not replace reasoning** — no black-box scoring.
- Evaluation focuses more on **thinking and process** than feature count.

From this, I understood that the core requirement was not just to "rank options," but to build a **transparent and defensible decision engine**.

### My First Design Decision

I defined the **decision model before writing any code**.

I chose to implement **Weighted Multi-Criteria Decision Making (WMCDM)** because:

| Requirement | How WMCDM Satisfies It |
|------------|----------------------|
| Deterministic | Same inputs always produce the same ranking |
| Mathematically explainable | Every score is traceable to `normalized_weight × score` |
| Dynamic criteria support | Works with any number of criteria/weights at runtime |
| Produces ranked output | Natural ordering by final weighted score |
| Transparent | No hidden layers, no opaque AI reasoning |

Only after finalizing the decision model did I choose the technical stack.

---

## 2. 🏗️ Architectural Thinking — Why This Stack?

### Options I Considered

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| Simple CLI tool | Fast to build | No interactivity, poor demo quality | ❌ Rejected |
| Single-file Python script | Minimal setup | No separation of concerns, not production-like | ❌ Rejected |
| Streamlit-only app (all logic in frontend) | Easy to deploy | Mixes presentation and business logic | ❌ Rejected |
| **FastAPI backend + Streamlit frontend** | Clean architecture, testable, production-like | Slightly more setup | ✅ **Chosen** |

### Why I Chose Client-Server Architecture

The separation into **FastAPI (backend)** and **Streamlit (frontend)** allowed me to:

1. **Keep scoring logic independent** — the decision engine can be tested, reused, or exposed as an API without any UI dependency.
2. **Maintain clean separation of concerns** — presentation layer (Streamlit) never touches business logic.
3. **Make the system production-like** — demonstrates real-world architectural maturity with REST API design, CORS middleware, and JSON schema validation.
4. **Improve explainability** — the explanation service is a standalone module, not tangled in UI code.
5. **Enable independent testing** — backend can be validated via Swagger UI, `curl`, or automated tests without touching the frontend.

---

## 3. 🧮 Core Decision Model Evolution

### Initial Thought (v1 — Naive)

My first thought was straightforward:

```
score = weight × raw_score
final = Σ(scores)
sort descending
```

However, I quickly realized this would be **flawed if total weights varied** between different decision sessions. A decision with criteria weights `[10, 10, 10]` would produce scores on a completely different scale than `[1, 1, 1]`, making results incomparable and misleading.

### The Fix — Weight Normalization (v2 — Final)

I introduced **weight normalization** to ensure fairness:

```
normalized_weight = weight / total_weight
contribution = normalized_weight × score
final_score = Σ(contributions)
```

This ensures:
- All normalized weights always sum to **1.0** (100%).
- The final score is always on a **0–10 scale** regardless of raw weight values.
- Results are **comparable** across different decision configurations.

> **This was the first major refinement** in the logic and fundamentally shaped the correctness of the entire system.

### Contribution Breakdown (v3 — Enhancement)

Initially, the API only returned the final score and rank. Later, I added a **per-criterion contribution breakdown**:

```json
{
  "option_name": "Car C",
  "final_score": 7.58,
  "contributions": {
    "Price": 2.92,
    "Fuel Efficiency": 2.00,
    "Safety": 2.67
  }
}
```

This was a critical enhancement because it directly supports **explainability** — users can see exactly how much each criterion contributed to the final score.

---

## 4. ❌ Alternative Approaches I Considered and Rejected

### Approach 1: AI-Based Ranking (LLM Scoring)

I briefly considered using a Large Language Model to analyze options, rank them, and generate reasoning.

**Why I rejected it:**
- It would become a **black box** — users can't verify the math.
- Rankings would be **non-deterministic** — same input could produce different outputs.
- It would **reduce explainability** — contradicting the core requirement.
- It would **violate the constraint** of "must not rely entirely on AI."

**What I did instead:** Used **rule-based explanation generation** — the `explanation_service.py` identifies the top contributor and flags trade-offs using pure math (contribution ratio < 70% of maximum possible).

### Approach 2: Rule-Based Hardcoded Scoring

I considered defining static business rules such as:
- "If scalability > 8, boost score by 10%"
- "If cost < threshold, increase weight automatically"

**Why I rejected it:**
- It introduces **hidden bias** that the user doesn't control.
- It becomes **non-transparent** — the system is quietly modifying user-defined weights.
- It **violates generality** — the system needs to work for *any* decision domain (cars, hiring, lunch, etc.), not just predefined ones.

### Approach 3: Advanced Decision Models (AHP / ML / Multi-Objective Optimization)

I considered:
- **Analytic Hierarchy Process (AHP)** — pairwise comparison matrices
- **Machine learning-based scoring** — trained on historical decision data
- **Multi-objective optimization** — Pareto-optimal solutions

**Why I rejected them:**
- **Overengineering** for the scope of this assignment.
- **Harder to explain** — AHP requires eigenvalue computation, ML requires training data.
- **Adds complexity without proportional benefit** — the assignment values thinking over feature count.

> **WMCDM was chosen as the most appropriate balance between simplicity and rigor.**

---

## 5. ✅ Validation Strategy — From Prototype to Defensible System

### Evolution of Input Validation

Initially, I did minimal validation — just checking if the JSON was well-formed. Through iterative development, I identified edge cases and added **strict layered validation**:

#### Frontend Validation (Streamlit)
| Check | Error Message |
|-------|---------------|
| Empty decision name | "Please enter a decision name." |
| No valid criteria | "Please add at least one valid criterion." |
| Empty option names | "Please add at least one valid option with a name." |

#### Backend Validation (Pydantic Schemas)
| Check | Error Type | Implementation |
|-------|-----------|----------------|
| Weight ≤ 0 | `422 Unprocessable Entity` | `Field(..., gt=0)` on Criterion model |
| Score outside 0–10 | `422 Unprocessable Entity` | `@model_validator` on Option model |
| Duplicate criterion names | `400 Bad Request` | Set comparison in `validate_request()` |
| Missing scores for a criterion | `400 Bad Request` | Cross-reference check in `validate_request()` |
| Extra scores for unknown criteria | `400 Bad Request` | Reverse cross-reference check |
| Zero total weight | `400 Bad Request` | Sum validation in `validate_request()` |
| Empty criteria/options list | `400 Bad Request` | Length check in `validate_request()` |

> **This was an important evolution from "working prototype" to "defensible system."** Each validation rule was added after encountering a real edge case during testing.

---

## 6. 🔧 Refactoring Decisions

### Separation of Concerns

Originally, I had all scoring logic directly inside the FastAPI route handler (`main.py`). This worked but was messy — the route was doing validation, calculation, explanation generation, and response construction all in one function.

I refactored into **three distinct modules**:

```
backend/app/
├── main.py                      ← API routing only
├── models/
│   └── schemas.py               ← Data validation (Pydantic)
└── services/
    ├── decision_engine.py       ← WMCDM scoring + ranking
    └── explanation_service.py   ← Rule-based explanation generation
```

**Benefits of this refactoring:**
- **Readability** — each file has a single, clear purpose.
- **Testability** — `decision_engine.py` can be unit-tested without HTTP.
- **Maintainability** — changing the explanation logic doesn't touch scoring.
- **Architectural clarity** — mirrors real-world service-oriented design.

### Explanation Service Design

The explanation service (`explanation_service.py`) uses a **rule-based approach** with two key analyses:

1. **Top Contributor Detection** — identifies which criterion contributed the most absolute score to the final result.
2. **Trade-off Detection** — calculates each criterion's *relative performance* as a ratio of its contribution to its maximum possible contribution (`norm_weight × 10`). If any criterion falls below **70%** of its potential, it's flagged as a notable trade-off.

This threshold (70%) was chosen deliberately — it balances sensitivity (catching meaningful weaknesses) with noise reduction (not flagging minor variations).

---

## 7. 🐛 Debugging Journey — The Port Mismatch Bug

### The Problem

After deploying the backend and frontend locally, clicking "Evaluate Decision" in the Streamlit UI produced:

```
requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

### Root Cause Analysis

The investigation revealed a **port mismatch**:

1. The Streamlit frontend was configured to call `http://localhost:8000/evaluate`.
2. Port `8000` was already occupied by **another service** on the machine.
3. The FastAPI backend was started on port `8001` instead.
4. When Streamlit hit port `8000`, it received an **HTML 404 page** (from the other service), not JSON.
5. Calling `response.json()` on HTML content threw the `JSONDecodeError`.

### The Fix

| Change | File | Before | After |
|--------|------|--------|-------|
| Backend port | `uvicorn` command | `--port 8000` | `--port 8001` |
| Frontend API URL | `streamlit_app.py` | `localhost:8000/evaluate` | `localhost:8001/evaluate` |
| Error handling | `streamlit_app.py` | Direct `.json()` call | Try/except with graceful fallback message |

### Defensive Code Added

```python
# Before (fragile):
st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

# After (defensive):
try:
    error_detail = response.json().get('detail', 'Unknown error')
except requests.exceptions.JSONDecodeError:
    error_detail = f"Server responded with status {response.status_code} and non-JSON content."
st.error(f"Error from backend: {error_detail}")
```

> **Lesson learned:** Always handle non-JSON error responses defensively. In production, upstream services may return HTML error pages, proxy errors, or empty responses.

---

## 8. 🧪 Testing and Validation

### End-to-End Test Scenarios

I validated the system against **five distinct test scenarios** covering happy paths, edge cases, and error handling:

#### Test 1: Happy Path — "Choosing a New Car"
- **Criteria:** Price (5), Fuel Efficiency (3), Safety (4)
- **Options:** Car A (cheap but unsafe), Car B (expensive but safe), Car C (well-rounded)
- **Result:** Car C wins (7.58) — balanced scores across all weighted criteria
- **Validation:** ✅ Explanation correctly highlights Price as top contributor for Car C

#### Test 2: One Heavy Criterion — "Hiring a Software Engineer"
- **Criteria:** Python Skills (10), Communication (1), Design Sense (1)
- **Options:** Candidate A (Python: 9, others: 2), Candidate B (Python: 5, others: 10)
- **Result:** Candidate A wins (7.83 vs 5.83)
- **Validation:** ✅ Python Skills weight (10/12 ≈ 83%) correctly dominates the calculation

#### Test 3: Perfect Tie — "Where to eat lunch?"
- **Criteria:** Taste (5), Distance (5) — equal weights
- **Options:** Place 1 (Taste: 8, Distance: 4), Place 2 (Taste: 4, Distance: 8)
- **Result:** Both score exactly 6.00 — a perfect mathematical tie
- **Validation:** ✅ System handles ties gracefully, ranks by input order

#### Test 4: Validation Errors
- Empty decision name → frontend blocks submission
- No criteria → frontend blocks submission
- Negative weight → backend returns 422
- Missing scores → backend returns 400

#### Test 5: Post-Fix Verification
- After the port mismatch fix, re-tested the full pipeline
- Confirmed JSON responses flow correctly from backend to frontend
- No `JSONDecodeError` or connection errors

---

## 9. 📁 Final Project Structure

```
decision_companion/
├── .gitignore                     # Ignores env, test files, output
├── README.md                      # Setup & usage instructions
├── BUILD_PROCESS.md               # This file — thinking process
├── DESIGN_DIAGRAMS.md             # Architecture, Data Flow, Component, Logic diagrams
│
├── backend/
│   ├── requirements.txt           # fastapi, pydantic, uvicorn
│   └── app/
│       ├── __init__.py
│       ├── main.py                # FastAPI app + CORS + /evaluate route
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py         # Pydantic models with validation
│       └── services/
│           ├── __init__.py
│           ├── decision_engine.py # WMCDM scoring engine
│           └── explanation_service.py # Rule-based explanations
│
└── frontend/
    ├── requirements.txt           # streamlit, requests, pandas
    └── streamlit_app.py           # Interactive UI
```

---

## 10. 🔑 Key Takeaways and Reflections

### What Went Well
- **Model-first thinking** — defining WMCDM before coding prevented scope creep and kept the system focused.
- **Layered validation** — catching errors at both frontend and backend made the system robust.
- **Separation of concerns** — the refactoring into distinct services paid off during debugging and testing.
- **Explainability by design** — the contribution breakdown and trade-off detection were baked into the architecture, not bolted on.

### What I Would Do Differently
- **Containerize earlier** — using Docker from the start would have avoided the port mismatch issue entirely.
- **Add automated unit tests** — while I thoroughly tested manually and through end-to-end browser automation, a formal `pytest` suite would improve CI/CD readiness.
- **Consider persistent storage** — currently, decisions are not saved. Adding a lightweight database (SQLite) would allow decision history and comparison over time.

### Skills Demonstrated
| Skill | Evidence |
|-------|----------|
| **Systems Design** | Client-server architecture with REST API |
| **Algorithm Design** | WMCDM with weight normalization |
| **Data Modeling** | Pydantic schemas with cross-field validation |
| **Debugging** | Port mismatch root cause analysis |
| **Defensive Programming** | Graceful error handling for non-JSON responses |
| **Explainable Computing** | Rule-based trade-off detection |
| **Documentation** | Architecture diagrams, build process, README |

---

> *"The goal was never to build the most feature-rich tool — it was to demonstrate clear thinking, defensible decisions, and an understanding of what makes software production-ready."*
