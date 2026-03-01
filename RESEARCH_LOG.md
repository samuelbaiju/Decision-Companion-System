# RESEARCH LOG – Decision Companion System

**Author:** Samuel Baiju  
**Date:** February–March 2026  
**AI Tools Used:** Antigravity (Google DeepMind IDE Assistant), Chatgpt  

This document transparently records all AI usage, research queries, and reasoning decisions made during development. The goal is to show not only what I used, but how I evaluated, modified, or rejected suggestions — and where things went wrong.

---

## 1. Initial Problem Interpretation & System Design

### Prompt Used (ChatGPT)

> *"Design and build a Decision Companion System that helps users make better decisions by evaluating options based on user-defined criteria. The system should not rely entirely on AI. Use Python backend and suggest architecture."*

### AI Response Summary

ChatGPT suggested:
- Using Weighted Multi-Criteria Decision Making (WMCDM) as the core algorithm
- FastAPI for the backend, Streamlit for the frontend
- Modular structure with separate validation, scoring, and explanation layers
- Deterministic scoring with weight normalization

### What I Accepted

- WMCDM as the decision model — it's deterministic, explainable, and fits the assignment perfectly
- The client-server architecture suggestion (FastAPI + Streamlit)
- Weight normalization formula: `normalized_weight = weight / total_weight`

### What I Rejected

- ChatGPT briefly mentioned using an LLM to generate "intelligent rankings" — I rejected this because it would make the system a black box and violate the assignment's transparency requirement
- It suggested using SQLite for persistence — I decided this was out of scope for the initial version

---

## 2. Full Code Generation With Antigravity

### Prompt Used (Antigravity)

> *"Design and build a Decision Companion System. The system must not rely entirely on AI. Document your thinking process, design decisions, and build process thoroughly, including a README, design diagram, BUILD_PROCESS.md, and RESEARCH_LOG.md. The deadline for submission is March 2, 2026."*

Antigravity generated the **entire initial codebase** in one session:

- `backend/app/main.py` — FastAPI app with CORS middleware
- `backend/app/models/schemas.py` — Pydantic models with validation
- `backend/app/services/decision_engine.py` — WMCDM engine
- `backend/app/services/explanation_service.py` — Rule-based explanations
- `frontend/streamlit_app.py` — Dynamic Streamlit UI
- `README.md` — Setup instructions
- Separate `requirements.txt` for backend and frontend

### Follow-up Prompt (Antigravity)

> *"Continue"* (multiple times during the code generation process)

I used this to let Antigravity complete the full implementation step by step. It generated each module sequentially, and I reviewed the output at each stage before proceeding.

### What I Accepted

- The **modular file structure** — clean separation of concerns
- The **WMCDM formula** — I verified the math manually and confirmed it was correct
- The **Pydantic validation** rules — `Field(gt=0)` for weights, `@model_validator` for cross-field checks
- The **contribution breakdown** in the API response — essential for explainability
- The **explanation service logic** — identifies top contributor and flags trade-offs below 70% threshold

### What I Modified Later

- Port configuration (8000 → 8001) after discovering a conflict
- Error handling in the frontend (added try/except for non-JSON responses)

---

## 3. Debugging the JSONDecodeError

### Prompt Used (Antigravity)

> *"requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0) — Traceback: File streamlit_app.py, line 136 — st.error(f"Error from backend: {response.json().get('detail', 'Unknown error')}") — this error came while checking and tell me what is the issue here"*

This was a **real error** I encountered when I first ran the complete system. The Streamlit UI was crashing when I clicked "Evaluate Decision."

### What Antigravity Did

Antigravity investigated systematically:

1. Ran `netstat -ano | findstr :8000` — found port 8000 was occupied by another service
2. Checked the FastAPI logs — confirmed backend was actually running on port 8001
3. Tested backend directly via Swagger UI (`http://localhost:8001/docs`) — backend was working fine
4. Identified the root cause: **frontend was calling port 8000, backend was on port 8001**

### Fix Applied

- Changed `API_URL` in `streamlit_app.py` from `localhost:8000` to `localhost:8001`
- Updated `README.md` to reflect the correct port

### What I Learned

This was the most valuable debugging moment in the project. The error message was misleading — `JSONDecodeError` sounds like a data format problem, but the real issue was a **network configuration mismatch**. The frontend was getting an HTML 404 page from the wrong service and trying to parse it as JSON.

---

## 4. First Round of Testing

### Prompt Used (Antigravity)

> *"Test the webapp for me and show me the output and if any errors arise fix that for me"*

### What Happened

Antigravity used its browser automation to:
- Open `http://localhost:8501`
- Fill in test criteria (Speed: weight 7, Cost: weight 3)
- Fill in test options (Option X and Option Y with scores)
- Click "Evaluate Decision"

**Result:** The error appeared again — the old Streamlit process was still running with the cached port 8000 URL.

### Follow-up Prompt (Antigravity)

> *"Fix this error and fix this issue and then test again"*

### What Antigravity Did

Added **defensive error handling** to the frontend:

```python
# Before (crashes on non-JSON response):
st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

# After (gracefully handles any response):
try:
    error_detail = response.json().get('detail', 'Unknown error')
except requests.exceptions.JSONDecodeError:
    error_detail = f"Server responded with status {response.status_code} and non-JSON content."
st.error(f"Error from backend: {error_detail}")
```

### What I Accepted

This was a good defensive programming practice. In production, upstream services can return HTML error pages, proxy errors, or empty responses. The code should never assume `.json()` will succeed.

---

## 5. Full Restart and Re-Testing

### Prompt Used (Antigravity)

> *"Test the whole website for me here and make sure whether this problem arises again or not and if error arises then fix the code and test again until the webapp displays the output properly in the webapp"*

### What Antigravity Did

1. **Force-killed** all old Python/Streamlit processes
2. **Restarted** the FastAPI backend on port 8001
3. **Restarted** the Streamlit frontend
4. Ran an automated browser test with fresh inputs:
   - Criteria: Performance (weight 8), Security (weight 4)
   - Options: Cloud (Perf: 9, Sec: 6), On-Premises (Perf: 5, Sec: 9)

### Result

**Success!** The evaluation table rendered correctly:
- Cloud: 8.00 (Rank 1)
- On-Premises: 6.33 (Rank 2)

The math checked out:
- Cloud: `(9 × 8/12) + (6 × 4/12) = 6.00 + 2.00 = 8.00` ✅
- On-Premises: `(5 × 8/12) + (9 × 4/12) = 3.33 + 3.00 = 6.33` ✅

No errors, no crashes. The port mismatch issue was fully resolved.

---

## 6. Edge Case Testing

### Prompt Used (Antigravity)

> *"Test these conditions in the webapp for me and display and show me the outputs:*
> *1. Happy Path — 'Choosing a New Car' with Price (5), Fuel Efficiency (3), Safety (4)*
> *2. One Heavy Criterion — 'Hiring a Software Engineer' with Python Skills (10), Communication (1), Design Sense (1)*
> *3. Perfect Tie — 'Where to eat lunch?' with Taste (5), Distance (5)"*

### Results

| Test | Winner | Score | Expected? |
|------|--------|-------|-----------|
| Choosing a New Car | Car C (well-rounded) | 7.58 | ✅ Yes — balanced high scores win |
| Hiring a Software Engineer | Candidate A | 7.83 vs 5.83 | ✅ Yes — Python Skills (83% weight) dominates |
| Where to eat lunch? | Tie | Both 6.00 | ✅ Yes — mirrored scores with equal weights |

### What This Proved

- The WMCDM formula handles **any number of criteria and options** correctly
- **Weight dominance** works as expected — a heavily weighted criterion overwhelms minor ones
- The system handles **perfect ties** gracefully
- The explanation service correctly identifies **top contributors and trade-offs**

---

## 7. Validation Strategy Research

### Prompt Used (ChatGPT)

> *"What are all the edge cases I should validate in a weighted multi-criteria decision making system?"*

### ChatGPT's Response

Suggested validating:
- Duplicate criteria names
- Missing scores per option
- Zero or negative weights
- Scores outside the allowed range
- Empty input lists
- Extra scores for non-existent criteria

### Prompt Used (ChatGPT)

> *"FastAPI input validation best practices with Pydantic"*

### What I Accepted

All the edge cases were legitimate — I verified each one could cause a real problem (division by zero, KeyError, misleading results).

### What I Rejected

ChatGPT suggested enforcing a maximum of 10 criteria. I rejected this because the system should be **domain-independent** — some decisions genuinely have many criteria.

---

## 8. Explanation Logic Research

### Prompt Used (ChatGPT)

> *"How to generate rule-based explanation for weighted scoring without using AI model?"*

### ChatGPT's Suggestion

- Highlight the highest contributing criterion
- Compare against the most important (highest-weighted) criterion
- Flag trade-offs where performance is weak relative to the criterion's weight

### What I Accepted

The contribution-based approach made sense — tying explanations directly to computed numbers.

### What I Modified

ChatGPT suggested using generic phrasing like "This option performs well." I made the explanation **data-dependent** — it mentions specific criterion names, exact contribution values, and only flags trade-offs when the relative performance drops below 70% of maximum.

### Why 70%?

I tested with several thresholds:
- 50% — too lenient, missed obvious weaknesses
- 90% — too strict, flagged almost everything
- **70%** — balanced, catches meaningful weaknesses without noise

---

## 9. Design Diagrams

### Prompt Used (Antigravity)

> *"Provide at least one: Architecture diagram, Data flow diagram, Component diagram, or decision logic diagram — provide me these in the project"*

### What Antigravity Generated

All four diagrams in a single `DESIGN_DIAGRAMS.md` file using Mermaid syntax (renders on GitHub):
1. **Architecture Diagram** — system overview with color-coded layers
2. **Data Flow Diagram** — traces data from user input to ranked output
3. **Component Diagram** — UML class diagram of all modules
4. **Decision Logic Flowchart** — step-by-step algorithm with validation branches

### What I Accepted

All four diagrams — they accurately reflected the actual codebase and were well-structured.

---

## 10. Build Process Documentation

### Prompt Used (Antigravity)

> *"Create me the perfect BUILD_PROCESS.md file for the project and create it on the basis of my project chat and our chat here in Antigravity"*

### What Antigravity Generated

A comprehensive document covering:
- Problem analysis and initial thinking
- Architecture trade-offs (table comparing 4 approaches)
- Decision model evolution (v1 naive → v2 normalized → v3 with contributions)
- Alternative approaches rejected (AI ranking, AHP, ML)
- Validation strategy evolution
- The debugging journey (port mismatch)
- Testing results
- Reflections

### What I Accepted

The structure and content accurately represented my development journey. I accepted it because it was based on our actual conversation flow.

---

## 11. Project Hygiene

### Prompt Used (Antigravity)

> *"Add a gitignore file and ignore env files and the readme file and test results file and output txt file here"*

### What Antigravity Generated

A `.gitignore` covering:
- `env/`, `venv/`, `.env` — virtual environments
- `__pycache__/`, `*.pyc` — Python bytecode
- `test_results.txt`, `output.txt` — test artifacts
- `.vscode/`, `.idea/` — IDE configs

### What I Modified

Antigravity asked whether I really wanted to ignore `README.md` — I agreed it should stay tracked, so it was excluded from `.gitignore`.

---

## 12. Continued Use of AI Going Forward

I plan to continue using Antigravity for:

- **Code refinement** — improving type hints, docstrings, and code style
- **Refactoring suggestions** — identifying areas where modules can be simplified
- **Unit test generation** — creating `pytest` skeletons for the decision engine
- **Documentation improvements** — polishing markdown structure

However, I will:

- **Manually validate all AI outputs** before accepting them
- **Never use AI for ranking logic** — WMCDM must remain human-designed
- **Not accept suggestions blindly** — every recommendation gets evaluated

**I treat AI as a collaborative assistant, not a decision maker.**

---

## 13. AI Usage Summary

### AI Was Used For:

| Purpose | Tool | Prompt Summary | Validated? |
|---------|------|----------------|-----------|
| System design brainstorming | ChatGPT | "Design a Decision Companion System using WMCDM" | ✅ Verified architecture and formula |
| Full code generation | Antigravity | "Design and build a Decision Companion System..." | ✅ Reviewed every file, verified math |
| Debugging JSONDecodeError | Antigravity | Pasted the full error traceback | ✅ Confirmed fix via e2e testing |
| Defensive error handling | Antigravity | "Fix this error and test again" | ✅ Tested with fresh browser session |
| Edge case discovery | ChatGPT | "What edge cases should I validate?" | ✅ Evaluated each against real risks |
| Explanation logic design | ChatGPT | "Rule-based explanation without AI model?" | ✅ Modified generic output to data-driven |
| End-to-end testing | Antigravity | "Test these conditions in the webapp..." | ✅ Verified math manually |
| Design diagrams | Antigravity | "Provide Architecture, Data Flow, Component, Logic diagrams" | ✅ Checked accuracy against codebase |
| Build process documentation | Antigravity | "Create BUILD_PROCESS.md based on our chat" | ✅ Reviewed and accepted |
| Git hygiene | Antigravity | "Add a gitignore file and ignore env files..." | ✅ Modified (kept README tracked) |

### AI Was NOT Used For:

- Making ranking decisions or choosing winners
- Replacing WMCDM logic with any AI/ML model
- Generating hidden scoring heuristics or biases
- Designing the core algorithm (WMCDM was chosen through independent research)

---

## 14. Reflection on Responsible AI Use

Throughout development, I applied a simple filter to every AI suggestion:

1. **Is this deterministic?** — Same input must always produce the same output.
2. **Is this explainable?** — Can I trace every number back to the formula?
3. **Does this reduce transparency?** — If yes, reject it.
4. **Does this violate assignment constraints?** — If yes, reject it.

When AI generated code I didn't fully understand, I didn't just use it. I read through it, tested it with edge cases, and verified the math manually. The port mismatch bug is a perfect example — AI generated code that assumed port 8000 was free, but my environment was different. That debugging process was entirely human.

**The biggest lesson:** AI is excellent at scaffolding and catching blind spots, but the critical thinking has to be mine. The system's core reasoning engine is mathematically explicit, deterministic, and fully transparent — exactly as the assignment requires.

---

## Final Statement

AI tools — Antigravity and ChatGPT — were used as collaborative development assistants throughout this project. They helped me build faster, catch edge cases, debug real issues, and structure documentation.

However, **all critical design decisions were consciously evaluated by me:**

- Choosing WMCDM over AI-based ranking
- Choosing client-server over monolithic architecture
- Designing the validation strategy
- Setting the 70% trade-off threshold
- Deciding what to accept, modify, or reject from every AI suggestion

The system's core reasoning engine remains **mathematically explicit, deterministic, and fully transparent**.
