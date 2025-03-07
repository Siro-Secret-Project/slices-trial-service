from utils.generate_object_id import generate_object_id
from document_retrieval.utils.generate_trial_eligibility_certeria.categorize_generated_criteria import _generate_tags

def filter_criteria(eligibility_agent, inclusion_criteria, exclusion_criteria):
    """Filter the inclusion and exclusion criteria using the eligibility agent."""
    return eligibility_agent.filter_generated_criteria(
        inclusionCriteria=inclusion_criteria,
        exclusionCriteria=exclusion_criteria
    )

def prepare_user_provided_criteria(inclusion_criteria, exclusion_criteria):
    """Prepare the user-provided criteria with unique IDs and source information."""
    return {
        "inclusionCriteria": [{
            "criteria": inclusion_criteria,
            "criteriaID": f"cid_{generate_object_id()}",
            "source": {"User Provided": inclusion_criteria}
        }],
        "exclusionCriteria": [{
            "criteria": exclusion_criteria,
            "criteriaID": f"cid_{generate_object_id()}",
            "source": {"User Provided": exclusion_criteria}
        }]
    }

def prepare_filtered_criteria(filtered_criteria):
    """Prepare the filtered criteria with unique IDs and source information."""
    provided_inclusion_criteria = [
        {
            "criteriaID": f"cid_{generate_object_id()}",
            "criteria": item,
            "source": {"User Provided": item}
        }
        for item in filtered_criteria["inclusionCriteria"]
    ]
    provided_exclusion_criteria = [
        {
            "criteriaID": f"cid_{generate_object_id()}",
            "criteria": item,
            "source": {"User Provided": item}
        }
        for item in filtered_criteria["exclusionCriteria"]
    ]
    return {
        "inclusionCriteria": provided_inclusion_criteria,
        "exclusionCriteria": provided_exclusion_criteria
    }

def categorize_criteria(eligibility_agent, user_provided_criteria):
    """Categorize the eligibility criteria using the eligibility agent."""
    return eligibility_agent.categorise_eligibility_criteria(
        eligibility_criteria=user_provided_criteria
    )

def build_categorized_data(categorized_response, user_provided_criteria):
    """Build the categorized data structure from the categorized response."""
    categorized_data = {}
    for item in categorized_response["data"]["inclusionCriteria"]:
        item_class = item["class"]
        criteria_id = item["criteriaID"]
        value = next(
            (criteria_item for criteria_item in user_provided_criteria["inclusionCriteria"]
            if criteria_item["criteriaID"] == criteria_id),
            {}
        )
        categorized_data.setdefault(item_class, {"Inclusion": [], "Exclusion": []})["Inclusion"].append({
            "criteria_id": value.get("criteriaID"),
            "criteria": value.get("criteria"),
            "source": value.get("source")
        })

    for item in categorized_response["data"]["exclusionCriteria"]:
        item_class = item["class"]
        criteria_id = item["criteriaID"]
        value = next(
            (criteria_item for criteria_item in user_provided_criteria["exclusionCriteria"]
            if criteria_item["criteriaID"] == criteria_id),
            {}
        )
        categorized_data.setdefault(item_class, {"Inclusion": [], "Exclusion": []})["Exclusion"].append({
            "criteria_id": value.get("criteriaID"),
            "criteria": value.get("criteria"),
            "source": value.get("source")
        })

    return categorized_data

def categorize_eligibility_criteria(eligibility_agent, inclusion_criteria, exclusion_criteria):
    """Categorize the eligibility criteria into inclusion and exclusion classes."""
    try:
        filtered_criteria_response = filter_criteria(eligibility_agent, inclusion_criteria, exclusion_criteria)

        if not filtered_criteria_response["success"]:
            print(filtered_criteria_response["message"])
            user_provided_criteria = prepare_user_provided_criteria(inclusion_criteria, exclusion_criteria)
        else:
            user_provided_criteria = prepare_filtered_criteria(filtered_criteria_response["data"])

        categorized_response = categorize_criteria(eligibility_agent, user_provided_criteria)
        if not categorized_response["success"]:
            return {"success": False, "message": categorized_response["message"], "data": None}

        categorized_data = build_categorized_data(categorized_response, user_provided_criteria)
        for category, value in categorized_data.items():
            for key, criteria in value.items():
                for item in criteria:
                    item["tags"] = _generate_tags(criteria_text=item["criteria"])
        return {"success": True, "message": "Successfully categorized eligibility criteria.", "data": categorized_data}

    except Exception as e:
        print(f"Error occurred while categorizing eligibility criteria: {str(e)}")
        return {"success": False, "message": f"Error occurred while categorizing eligibility criteria: {str(e)}", "data": None}