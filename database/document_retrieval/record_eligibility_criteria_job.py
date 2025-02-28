from database.mongo_db_connection import MongoDBDAO
from datetime import datetime
from document_retrieval.models.db_models import StoreEligibilityCriteria

# Initialize MongoDBDAO
mongo_dao = MongoDBDAO()

def record_eligibility_criteria_job(job_id: str,
                                    categorized_data: dict,
                                    categorized_data_user: dict,
                                    metrics_data: dict) -> dict:
    """
    Stores the generated eligibility criteria (inclusion and exclusion) as a job in MongoDB.

    If the document already exists, retains the original created_at date.

    Args:
        job_id (str): The unique identifier for the job (ECID).
        categorized_data (dict): Categorized eligibility criteria in 14 categories.
        categorized_data_user (dict): Categorized user-provided eligibility criteria in 14 categories.
        metrics_data (dict): Metrics data for this job.

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
        # Check if the document already exists
        existing_doc = mongo_dao.find_one("similar_trials_criteria_results", {"ecid": job_id})

        created_at = existing_doc["createdAt"] if existing_doc else datetime.now()

        # Create a document using the StoreEligibilityCriteria model
        document = StoreEligibilityCriteria(
            ecid=job_id,
            categorizedData=categorized_data,
            userCategorizedData=categorized_data_user,
            metrics=metrics_data,
            createdAt=created_at,
            updatedAt=datetime.now(),
        ).dict()

        # Insert or update the document using MongoDBDAO
        db_response = mongo_dao.update(
            collection_name="similar_trials_criteria_results",
            update_values=document,
            query={"ecid": job_id},
            upsert=True
        )

        # Check if the document was successfully inserted or updated
        if db_response:
            final_response["success"] = True
            final_response["message"] = f"Successfully stored similar trials criteria results: {db_response}"

    except Exception as e:
        final_response["message"] = f"Error storing similar trials criteria results: {e}"

    return final_response
