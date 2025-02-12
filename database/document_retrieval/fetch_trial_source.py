from database.mongo_db_connection import MongoDBDAO


def fetch_trial_source(target_id: list, ecid: str, criteria_id: str) -> dict:
    """
    Fetches a preprocessed medical trial document from MongoDB using the provided ecid.

    Parameters:
    target_id (list): The target trial IDs to filter sources.
    ecid (str): The unique ECID of the trial document.
    criteria_id (str): The criteria ID to locate the specific trial data.

    Returns:
    dict: A response dictionary containing success status, message, and requested data (if found).
    """
    final_response = {
        "success": False,
        "message": "No preprocessed trial document found",
        "data": None
    }
    try:
        # Initialize MongoDBDAO
        mongo_dao = MongoDBDAO()

        # Query to fetch the trial document based on ECID
        query = {"ecid": ecid}

        # Perform a search for the document using MongoDBDAO
        similar_trial_document = mongo_dao.find_one(
            collection_name="similar_trials_criteria_results",
            query=query,
            projection={"categorizedData": 1, "userCategorizedData": 1}
        )

        if not similar_trial_document:
            return final_response

        # Extract categorizedData and userCategorizedData
        categorized_data = similar_trial_document.get("categorizedData", {})
        user_categorized_data = similar_trial_document.get("userCategorizedData", {})

        # Search for the matching criteria_id within categorizedData and userCategorizedData
        def find_criteria(data):
            for category, subcategories in data.items():
                for inclusion_exclusion, criteria_list in subcategories.items():
                    for criteria in criteria_list:
                        if criteria.get("criteria_id") == criteria_id:
                            return criteria.get("source", {})
            return None

        source_data = find_criteria(categorized_data) or find_criteria(user_categorized_data)

        if source_data:
            # Filter source data based on target_id list
            filtered_sources = {k: v for k, v in source_data.items() if k in target_id}

            if filtered_sources:
                final_response.update({
                    "success": True,
                    "message": "Successfully fetched trial source data",
                    "data": filtered_sources
                })

    except Exception as e:
        final_response["message"] = f"Error fetching trial data: {str(e)}"

    return final_response
