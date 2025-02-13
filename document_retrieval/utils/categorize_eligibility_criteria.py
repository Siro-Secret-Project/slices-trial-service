def categorize_eligibility_criteria(eligibility_agent, eligibility_criteria) -> dict:
    """Categorize the eligibility criteria into inclusion and exclusion classes."""
    categorized_response = eligibility_agent.categorise_eligibility_criteria(eligibility_criteria=eligibility_criteria)
    if not categorized_response["success"]:
        return {"success": False, "message": categorized_response["message"], "data": None}

    categorized_data = {}
    for item in categorized_response["data"]["inclusionCriteria"]:
        item_class = item["class"]
        criteriaID = item["criteriaID"]
        value = {}
        for criteria_item in eligibility_criteria["inclusionCriteria"]:
            if criteria_item["criteriaID"] == criteriaID:
                value["criteria_id"] = criteria_item["criteriaID"]
                value["criteria"] = criteria_item["criteria"]
                value["source"] = criteria_item["source"]
        categorized_data.setdefault(item_class, {"Inclusion": [], "Exclusion": []})["Inclusion"].append(value)

    for item in categorized_response["data"]["exclusionCriteria"]:
        item_class = item["class"]
        criteriaID = item["criteriaID"]
        value = {}
        for criteria_item in eligibility_criteria["exclusionCriteria"]:
            if criteria_item["criteriaID"] == criteriaID:
                value["criteria_id"] = criteria_item["criteriaID"]
                value["criteria"] = criteria_item["criteria"]
                value["source"] = criteria_item["source"]
        categorized_data.setdefault(item_class, {"Inclusion": [], "Exclusion": []})["Exclusion"].append(value)

    return {"success": True, "data": categorized_data}