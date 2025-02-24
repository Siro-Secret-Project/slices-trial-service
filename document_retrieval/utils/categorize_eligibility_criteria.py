def categorize_eligibility_criteria(eligibility_agent, eligibility_criteria) -> dict:
    """Categorize the eligibility criteria into inclusion and exclusion classes."""
    try:
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

        return {"success": True, "message": "Successfully categorized eligibility criteria.", "data": categorized_data}
    except Exception as e:
        print(f"Error occurred while categorizing eligibility criteria: {str(e)}")
        return {"success": False, "message": f"Error occurred while categorizing eligibility criteria: {str(e)}", "data": None}