from database.mongo_db_connection import MongoDBDAO
from datetime import datetime
from document_retrieval.models.db_models import StoreSimilarTrials

# Initialize MongoDB Data Access Object (DAO)
mongo_dao = MongoDBDAO()

def store_similar_trials(user_name: str, ecid: str, user_input: dict, similar_trials: list) -> dict:
    """
    Stores the results of similar trials in the MongoDB database.

    Args:
        user_name (str): The name of the user performing the operation.
        ecid (str): The ECID (Electronic Case Identifier) for the trial.
        user_input (dict): The user-provided input details.
        similar_trials (list): A list of similar trial results to be stored.

    Returns:
        dict: A dictionary containing the status of the operation, message, and stored data if successful.
    """
    final_response = {
        "success": False,
        "message": "Failed to store similar trials results",
        "data": None
    }

    try:
        # Create a document instance using the StoreSimilarTrials model
        document = StoreSimilarTrials(
            userName=user_name,
            ecid=ecid,
            userInput=user_input,
            similarTrials=similar_trials,
            created_at=datetime.now(),  # Timestamp for record creation
            updated_at=datetime.now()   # Timestamp for record update
        ).dict()

        # Insert the document into the MongoDB collection using DAO
        db_response = mongo_dao.insert("similar_trials_results", document)

        # Check if the document was successfully inserted
        if db_response:
            final_response["success"] = True
            final_response["message"] = f"Successfully stored similar trials results: {db_response.inserted_id}"
            final_response["data"] = db_response

    except Exception as e:
        # Handle any exceptions and update the response with the error message
        final_response["message"] = f"Error storing similar trials criteria results: {e}"

    return final_response
