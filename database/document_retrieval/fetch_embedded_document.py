from database.mongo_db_connection import MongoDBDAO


def fetch_embedded_document(nct_id: str) -> dict:
    """
    Fetches an embedded document from the MongoDB collection based on the given NCT ID.

    This function queries the "t2dm_final_data_samples_processed_embeddings" collection
    to retrieve a document that matches the provided `nct_id`. If a matching document is found,
    it returns the document data. Otherwise, it returns a failure response.

    Args:
        nct_id (str): The NCT ID of the document to fetch.

    Returns:
        dict: A response dictionary containing:
            - "success" (bool): Indicates whether the fetch operation was successful.
            - "message" (str): Describes the result of the operation.
            - "data" (dict or None): The fetched document if found, otherwise None.
    """
    final_response = {
        "success": False,
        "message": "Failed to fetch document",
        "data": None
    }

    try:
        # Initialize MongoDB connection instance
        mongo_dao = MongoDBDAO()

        # Define projection fields to exclude "_id" (MongoDB default field)
        projection = {"_id": 0}

        # Query MongoDB for the document using the provided NCT ID
        document = mongo_dao.find_one(
            collection_name="t2dm_final_data_samples_processed_embeddings",
            query={"nctId": nct_id},
            projection=projection
        )

        # If a document is found, update the response
        if document:
            final_response["success"] = True
            final_response["data"] = document
            final_response["message"] = "Successfully fetched document"
        else:
            print(f"Failed to fetch document: {nct_id}")
            final_response["message"] = "Document not found"
            return final_response

    except Exception as e:
        # Handle unexpected errors and update the response
        final_response["message"] = f"Unexpected error while fetching MongoDB document: {e}"

    return final_response