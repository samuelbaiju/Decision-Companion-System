# Decision Companion System

A full-stack Python application that evaluates real-world decisions using Weighted Multi-Criteria Decision Making (WMCDM).

## Features
- Dynamic definition of criteria and weights.
- Dynamic options and scoring per option.
- Automated ranking using deterministic math (no AI black box).
- Rule-based explanations highlighting strengths and trade-offs.

## Project Structure
- `backend/`: FastAPI application enforcing business logic and validation.
- `frontend/`: Streamlit web app providing a clean, dynamic UI.

## Requirements
- Python 3.9+

## How to Run

### 1. Run the Backend
Open a terminal and navigate to the backend directory:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
```
The FastAPI backend will start on `http://127.0.0.1:8001`.
You can view API documentation at `http://127.0.0.1:8001/docs`.

### 2. Run the Frontend
Open a **new** terminal and navigate to the frontend directory:
```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```
The Streamlit app will normally open automatically in your browser at `http://localhost:8501`.

## Example JSON Payload
If you want to test the API directly using cURL, Postman, or the `/docs` UI, here is an example payload for the `POST /evaluate` endpoint:

```json
{
  "decision_name": "Choosing a New Smartphone",
  "criteria": [
    {
      "name": "Battery Life",
      "weight": 8
    },
    {
      "name": "Camera Quality",
      "weight": 6
    },
    {
      "name": "Price",
      "weight": 9
    }
  ],
  "options": [
    {
      "name": "Phone A",
      "scores": {
        "Battery Life": 8.5,
        "Camera Quality": 9.0,
        "Price": 6.0
      }
    },
    {
      "name": "Phone B",
      "scores": {
        "Battery Life": 9.5,
        "Camera Quality": 7.0,
        "Price": 8.0
      }
    }
  ]
}
```
