def categorize_eligibility_criteria(eligibility_agent, eligibility_criteria) -> dict:
    """Categorize the eligibility criteria into inclusion and exclusion classes."""
    categorized_response = eligibility_agent.categorise_eligibility_criteria(eligibility_criteria=eligibility_criteria)
    if not categorized_response["success"]:
        return {"success": False, "message": categorized_response["message"], "data": None}

    categorized_data = {}
    for item in categorized_response["data"]["inclusionCriteria"]:
        item_class = item["class"]
        categorized_data.setdefault(item_class, {"Inclusion": [], "Exclusion": []})["Inclusion"].append(item["criteria"])

    for item in categorized_response["data"]["exclusionCriteria"]:
        item_class = item["class"]
        categorized_data.setdefault(item_class, {"Inclusion": [], "Exclusion": []})["Exclusion"].append(item["criteria"])

    return {"success": True, "data": categorized_data}
