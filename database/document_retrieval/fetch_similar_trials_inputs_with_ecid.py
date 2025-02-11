from database.mongo_db_connection import MongoDBDAO


def fetch_similar_trials_inputs_with_ecid(ecid: str) -> dict:
    """
    Fetches user inputs related to similar trial searches from the MongoDB collection
    using the provided `ecid` Job ID.

    Args:
        ecid (str): The unique identifier for the Job.

    Returns:
        dict: A response dictionary containing:
            - "success" (bool): Indicates whether the document was found successfully.
            - "message" (str): A descriptive message about the operation result.
            - "data" (dict | None): The fetched document data if found, otherwise None.
    """
    # Initialize the default response structure
    final_response = {
        "success": False,
        "message": f"No User Inputs Found for ecid: {ecid}",
        "data": None
    }

    try:
        # Initialize MongoDB Data Access Object (DAO)
        mongo_dao = MongoDBDAO()

        # Query the MongoDB collection for a document matching the given ecid
        db_response = mongo_dao.find_one(
            collection_name="similar_trials_results",  # Collection storing similar trials inputs
            query={"ecid": ecid},  # Filter criteria to find the relevant document
            projection={"_id": 0}  # Exclude the MongoDB default `_id` field from the result
        )

        # If a document is found, update the response
        if db_response:
            final_response["data"] = db_response
            final_response["success"] = True
            final_response["message"] = "Similar Trials Input Found"

    except Exception as e:
        # Handle any errors during database query execution
        final_response["success"] = False
        final_response["message"] = f"Error fetching document: {str(e)}"
        final_response["data"] = None

    return final_response
