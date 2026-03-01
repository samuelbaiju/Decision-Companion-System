from typing import Dict, List

def generate_explanation(
    option_name: str, 
    contributions: Dict[str, float], 
    normalized_weights: Dict[str, float],
    is_top_choice: bool
) -> str:
    """
    Generates a rule-based explanation for why an option received its score.
    Does NOT use AI. Purely math and rule-based.
    """
    if not contributions:
        return "No criteria available for explanation."

    # Identify heavily weighted criteria
    sorted_weights = sorted(normalized_weights.items(), key=lambda x: x[1], reverse=True)
    top_weight_criterion = sorted_weights[0][0]

    # Identify highest contributing criteria for this option
    sorted_contributions = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    top_contribution = sorted_contributions[0]
    
    # Identify weaknesses (lowest contribution relative to weight)
    relative_performances = {}
    for crit, cont in contributions.items():
        max_possible = normalized_weights[crit] * 10
        if max_possible > 0:
            relative_performances[crit] = cont / max_possible
        else:
            relative_performances[crit] = 0

    sorted_performance = sorted(relative_performances.items(), key=lambda x: x[1])
    weakest_criterion = sorted_performance[0][0]
    
    explanation_parts = []
    
    if is_top_choice:
        explanation_parts.append(f"'{option_name}' is the top choice.")
    
    explanation_parts.append(
        f"Its strongest performance was in '{top_contribution[0]}', "
        f"contributing {top_contribution[1]:.2f} to the final score."
    )

    if top_weight_criterion == top_contribution[0]:
        explanation_parts.append(f"This is highly aligned with your most important criterion ('{top_weight_criterion}').")
    
    if len(contributions) > 1:
        weakness_ratio = relative_performances[weakest_criterion]
        # Only mention trade-off if it performed less than 70% of maximum possible
        if weakness_ratio < 0.7:
            explanation_parts.append(
                f"However, a notable trade-off is its performance in '{weakest_criterion}', "
                "where it scored the lowest relative to the criterion's importance."
            )

    return " ".join(explanation_parts)
