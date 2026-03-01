from typing import Dict, List
from app.models.schemas import DecisionRequest, RankingResult, DecisionResponse, Criterion, Option
from app.services.explanation_service import generate_explanation

def evaluate_decision(request: DecisionRequest) -> DecisionResponse:
    """
    Evaluates the decision using Weighted Multi-Criteria Decision Making (WMCDM).
    Formula:
      Normalized Weight = weight / total_weight
      Final Score = sum(normalized_weight * score)
    """
    criteria = request.criteria
    options = request.options

    # 1. Calculate total weight
    total_weight = sum(c.weight for c in criteria)

    # 2. Normalize weights
    normalized_weights: Dict[str, float] = {}
    for c in criteria:
        normalized_weights[c.name] = c.weight / total_weight

    # 3. Calculate scores and contributions for each option
    results = []
    
    for option in options:
        final_score = 0.0
        contributions: Dict[str, float] = {}
        
        for c in criteria:
            crit_name = c.name
            score = option.scores[crit_name]
            norm_weight = normalized_weights[crit_name]
            
            # contribution for this criterion
            contribution = norm_weight * score
            contributions[crit_name] = round(contribution, 4)
            final_score += contribution
            
        results.append({
            "option_name": option.name,
            "final_score": round(final_score, 4),
            "contributions": contributions
        })

    # 4. Rank options descending by final score
    results.sort(key=lambda x: x["final_score"], reverse=True)

    # 5. Assign rank numbers and generate explanations
    ranking: List[RankingResult] = []
    for index, res in enumerate(results):
        rank = index + 1
        is_top_choice = (rank == 1)
        
        explanation = generate_explanation(
            option_name=res["option_name"],
            contributions=res["contributions"],
            normalized_weights=normalized_weights,
            is_top_choice=is_top_choice
        )
        
        ranking.append(
            RankingResult(
                option_name=res["option_name"],
                rank=rank,
                final_score=res["final_score"],
                contributions=res["contributions"],
                explanation=explanation
            )
        )

    return DecisionResponse(
        decision_name=request.decision_name,
        ranking=ranking
    )
