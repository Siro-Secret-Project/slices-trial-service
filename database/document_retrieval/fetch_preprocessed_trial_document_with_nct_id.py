from database.mongo_db_connection import db

# Get the MongoDB collection containing preprocessed trial data
preprocessed_trial_document_collection = db['t2dm_data_preprocessed']


def fetch_preprocessed_trial_document_with_nct_id(nct_id: str) -> dict:
    """
    fetches a preprocessed medical trial document from MongoDB using the provided nct_id.

    Parameters:
    nct_id (str): The unique NCT ID of the trial document.

    Returns:
    dict: A response dictionary containing success status, message, and requested data (if found).
    """
    final_response = {
        "success": False,
        "message": "No preprocessed trial document found",
        "data": None
    }
    try:

        # Perform a search for the document
        preprocessed_trial_document_response = preprocessed_trial_document_collection.find_one(
            {"protocolSection.identificationModule.nctId": nct_id},
            {"_id": 0}
        )

        if preprocessed_trial_document_response:
            final_response["data"] = preprocessed_trial_document_response
            final_response["success"] = True
            final_response["message"] = 'Preprocessed trial document found'
    except Exception as e:
        # Handle any exceptions that occur during the database query
        final_response["success"] = False
        final_response["message"] = f"Error fetching document: {str(e)}"
        final_response["data"] = None

    return final_response


