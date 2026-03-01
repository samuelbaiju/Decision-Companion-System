from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import DecisionRequest, DecisionResponse
from app.services.decision_engine import evaluate_decision

app = FastAPI(
    title="Decision Companion API",
    description="API for evaluating real-world decisions using Weighted Multi-Criteria Decision Making (WMCDM)",
    version="1.0.0"
)

# Enable CORS for the Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Decision Companion API"}

@app.post("/evaluate", response_model=DecisionResponse)
def evaluate(request: DecisionRequest):
    try:
        response = evaluate_decision(request)
        return response
    except ValueError as e:
        # Catch any value errors from validation or standard processing
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
