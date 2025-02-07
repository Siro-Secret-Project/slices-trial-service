from database.mongo_db_connection import MongoDBDAO

def fetch_preprocessed_trial_document_with_nct_id(nct_id: str) -> dict:
    """
    Fetches a preprocessed medical trial document from MongoDB using the provided nct_id.

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
        # Initialize MongoDBDAO
        mongo_dao = MongoDBDAO()

        # Perform a search for the document using MongoDBDAO
        preprocessed_trial_document_response = mongo_dao.find_one(
            collection_name="t2dm_data_preprocessed",
            query={"protocolSection.identificationModule.nctId": nct_id},
            projection={"_id": 0}
        )

        if preprocessed_trial_document_response:
            final_response["data"] = preprocessed_trial_document_response
            final_response["success"] = True
            final_response["message"] = "Preprocessed trial document found"
    except Exception as e:
        # Handle any exceptions that occur during the database query
        final_response["success"] = False
        final_response["message"] = f"Error fetching document: {str(e)}"
        final_response["data"] = None

    return final_response
