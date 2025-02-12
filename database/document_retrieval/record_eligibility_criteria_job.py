from database.mongo_db_connection import MongoDBDAO
from datetime import datetime
from document_retrieval.models.db_models import StoreEligibilityCriteria

# Initialize MongoDBDAO
mongo_dao = MongoDBDAO()

def record_eligibility_criteria_job(job_id: str,
                                    categorized_data: dict,
                                    categorized_data_user: dict) -> dict:
    """
    Stores the generated eligibility criteria (inclusion and exclusion) as a job in MongoDB.

    This function creates a document using the provided job ID, inclusion criteria, and exclusion criteria,
    and inserts it into the MongoDB collection for storing similar trials criteria results.

    Args:
        job_id (str): The unique identifier for the job (ECID).
        categorized_data (dict): Categorized eligibility criteria in 14 categories.
        categorized_data_user (dict): Categorized user provided eligibility criteria in 14 categories.

    Returns:
        dict: A response dictionary containing:
              - success (bool): Indicates whether the operation was successful.
              - message (str): A message describing the outcome of the operation.
              - data (str or None): The ID of the inserted document if successful, otherwise None.
    """
    final_response = {
        "success": False,
        "message": "Failed to store similar trials criteria results",
        "data": None
    }

    try:
        # Create a document using the StoreEligibilityCriteria model
        document = StoreEligibilityCriteria(
            ecid=job_id,
            categorizedData=categorized_data,
            userCategorizedData=categorized_data_user,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ).dict()

        # Insert the document using MongoDBDAO
        db_response = mongo_dao.insert("similar_trials_criteria_results", document)

        # Check if the document was successfully inserted
        if db_response:
            final_response["success"] = True
            final_response["message"] = f"Successfully stored similar trials criteria results: {db_response.inserted_id}"

    except Exception as e:
        final_response["message"] = f"Error storing similar trials criteria results: {e}"

    return final_response
