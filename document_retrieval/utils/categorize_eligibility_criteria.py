from utils.generate_object_id import generate_object_id

def categorize_eligibility_criteria(eligibility_agent, inclusion_criteria, exclusion_criteria ) -> dict:
    """Categorize the eligibility criteria into inclusion and exclusion classes."""
    try:
        filtered_criteria_response = eligibility_agent.filter_generated_criteria(inclusionCriteria=inclusion_criteria,
                                                                                 exclusionCriteria=exclusion_criteria)

        user_provided_criteria = {}
        if filtered_criteria_response["success"] is False:
            print(filtered_criteria_response["message"])
            provided_inclusion_criteria = inclusion_criteria
            provided_exclusion_criteria = exclusion_criteria

            user_provided_criteria = {
                "inclusionCriteria": [{
                    "criteria": provided_inclusion_criteria,
                    "criteriaID": f"cid_{generate_object_id()}",
                    "source": {
                        "User Provided": inclusion_criteria
                    }
                }],
                "exclusionCriteria": [{
                    "criteria": provided_exclusion_criteria,
                    "criteriaID": f"cid_{generate_object_id()}",
                    "source": {
                        "User Provided": exclusion_criteria
                    }
                }]
            }
        else:
            provided_criteria = filtered_criteria_response["data"]
            provided_inclusion_criteria = []
            for item in provided_criteria["inclusionCriteria"]:
                new_item = {
                    "criteriaID": f"cid_{generate_object_id()}",
                    "criteria": item,
                    "source": {
                        "User Provided": item
                    }
                }
                provided_inclusion_criteria.append(new_item)
            provided_exclusion_criteria = []
            for item in provided_criteria["exclusionCriteria"]:
                new_item = {
                    "criteriaID": f"cid_{generate_object_id()}",
                    "criteria": item,
                    "source": {
                        "User Provided": exclusion_criteria
                    }
                }
                provided_exclusion_criteria.append(new_item)
                user_provided_criteria = {
                    "inclusionCriteria": provided_inclusion_criteria,
                    "exclusionCriteria": provided_exclusion_criteria
                }

        categorized_response = eligibility_agent.categorise_eligibility_criteria(eligibility_criteria=user_provided_criteria)
        if not categorized_response["success"]:
            return {"success": False, "message": categorized_response["message"], "data": None}

        categorized_data = {}
        for item in categorized_response["data"]["inclusionCriteria"]:
            item_class = item["class"]
            criteriaID = item["criteriaID"]
            value = {}
            for criteria_item in user_provided_criteria["inclusionCriteria"]:
                if criteria_item["criteriaID"] == criteriaID:
                    value["criteria_id"] = criteria_item["criteriaID"]
                    value["criteria"] = criteria_item["criteria"]
                    value["source"] = criteria_item["source"]
            categorized_data.setdefault(item_class, {"Inclusion": [], "Exclusion": []})["Inclusion"].append(value)

        for item in categorized_response["data"]["exclusionCriteria"]:
            item_class = item["class"]
            criteriaID = item["criteriaID"]
            value = {}
            for criteria_item in user_provided_criteria["exclusionCriteria"]:
                if criteria_item["criteriaID"] == criteriaID:
                    value["criteria_id"] = criteria_item["criteriaID"]
                    value["criteria"] = criteria_item["criteria"]
                    value["source"] = criteria_item["source"]
            categorized_data.setdefault(item_class, {"Inclusion": [], "Exclusion": []})["Exclusion"].append(value)
            
        return {"success": True, "message": "Successfully categorized eligibility criteria.", "data": categorized_data}
    except Exception as e:
        print(f"Error occurred while categorizing eligibility criteria: {str(e)}")
        return {"success": False, "message": f"Error occurred while categorizing eligibility criteria: {str(e)}", "data": None}
