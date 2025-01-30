from database.mongo_db_connection import db

# Get the MongoDB collection containing processed trial data
t2dm_collection = db["t2dm_final_data_samples_processed"]

def fetch_processed_trial_document_with_nct_id(nct_id: str, module: str = None) -> dict:
    """
    Fetches a processed medical trial document from MongoDB using the provided nct_id.
    If a specific module is requested, only the relevant fields are returned.

    Parameters:
    nct_id (str): The unique NCT ID of the trial document.
    module (str, optional): The specific module to retrieve data from. Defaults to None.

    Returns:
    dict: A response dictionary containing success status, message, and requested data (if found).
    """
    final_response = {
        "success": False,
        "message": "Failed to fetch document",
        "data": None
    }

    try:
        # Mapping of module names to their corresponding fields in the database
        mapping = {
            "identificationModule": ["officialTitle"],
            "conditionsModule": ["conditions"],
            "eligibilityModule": ["inclusionCriteria", "exclusionCriteria"],
            "outcomesModule": ["primaryOutcomes", "secondaryOutcomes"],
            "designModule": ["designModule"]
        }

        # Query MongoDB for the document using the nct_id (excluding _id and keywords fields)
        document = t2dm_collection.find_one({"nctId": nct_id}, {"_id": 0, "keywords": 0})

        if document:
            if module is None:
                # If no specific module is requested, return the entire document
                final_response["data"] = document
            else:
                # If a module is requested, extract only relevant fields
                if module in mapping:
                    document_data = {item: document[item] for item in mapping[module] if item in document}
                    final_response["data"] = document_data
                else:
                    final_response["message"] = f"Invalid module '{module}' requested"
                    return final_response

            final_response["message"] = "Successfully fetched MongoDB document"
            final_response["success"] = True
        else:
            final_response["message"] = f"Document with nctId '{nct_id}' not found"

    except Exception as e:
        final_response["message"] = f"Unexpected error while fetching MongoDB document: {e}"

    return final_response
