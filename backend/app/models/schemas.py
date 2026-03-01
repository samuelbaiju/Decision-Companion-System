from pydantic import BaseModel, Field, conlist, model_validator
from typing import List, Dict, Any

class Criterion(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the criterion")
    weight: float = Field(..., gt=0, description="Weight of the criterion (must be > 0)")

class Option(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the option")
    scores: Dict[str, float] = Field(..., description="Scores for each criterion (0-10)")

    @model_validator(mode='after')
    def validate_scores(self) -> 'Option':
        for criterion_name, score in self.scores.items():
            if not (0 <= score <= 10):
                raise ValueError(f"Score for '{criterion_name}' must be between 0 and 10. Got {score}.")
        return self

class DecisionRequest(BaseModel):
    decision_name: str = Field(..., min_length=1)
    criteria: List[Criterion]
    options: List[Option]

    @model_validator(mode='after')
    def validate_request(self) -> 'DecisionRequest':
        if not self.criteria:
            raise ValueError("At least one criterion is required.")
        if not self.options:
            raise ValueError("At least one option is required.")

        # Check duplicate criteria names
        criteria_names = [c.name for c in self.criteria]
        if len(criteria_names) != len(set(criteria_names)):
            raise ValueError("Duplicate criteria names are not allowed.")

        # Check total weight > 0 (handled by individual weights > 0, but just to be sure)
        total_weight = sum(c.weight for c in self.criteria)
        if total_weight <= 0:
            raise ValueError("Total weight of all criteria must be greater than 0.")

        # Check options have all required scores
        for option in self.options:
            missing_criteria = [name for name in criteria_names if name not in option.scores]
            if missing_criteria:
                raise ValueError(f"Option '{option.name}' is missing scores for: {', '.join(missing_criteria)}")
            
            # Check for extra scores that don't match any criteria
            extra_criteria = [name for name in option.scores if name not in criteria_names]
            if extra_criteria:
                raise ValueError(f"Option '{option.name}' has scores for unknown criteria: {', '.join(extra_criteria)}")

        return self

class RankingResult(BaseModel):
    option_name: str
    rank: int
    final_score: float
    contributions: Dict[str, float]
    explanation: str

class DecisionResponse(BaseModel):
    decision_name: str
    ranking: List[RankingResult]
