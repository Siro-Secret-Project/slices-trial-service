# from database.mongo_db_connection import db
# from datetime import datetime
# from document_retrieval.models.db_models import StoreEligibilityCriteria
#
# # Collection to store the job in MongoDB
# similar_trials_criteria_results_collection = db['similar_trials_criteria_results']
#
# def record_eligibility_criteria_job(job_id: str,
#                                     trial_inclusion_criteria: list,
#                                     trial_exclusion_criteria: list,
#                                     categorized_data: dict,
#                                     categorized_data_user: dict,
#                                     trial_documents: list) -> dict:
#     """
#     Stores the generated eligibility criteria (inclusion and exclusion) as a job in MongoDB.
#
#     This function creates a document using the provided job ID, inclusion criteria, and exclusion criteria,
#     and inserts it into the MongoDB collection for storing similar trials criteria results.
#
#     Args:
#         job_id (str): The unique identifier for the job (ECID).
#         trial_inclusion_criteria (list): A list of inclusion criteria for the trial.
#         trial_exclusion_criteria (list): A list of exclusion criteria for the trial.
#         categorized_data (dict): Categorized eligibility criteria in 14 categories.
#         categorized_data_user (dict): Categorized user provided eligibility criteria in 14 categories.
#         trial_documents (list): Similar trial documents associated with this job.
#
#     Returns:
#         dict: A response dictionary containing:
#               - success (bool): Indicates whether the operation was successful.
#               - message (str): A message describing the outcome of the operation.
#               - data (str or None): The ID of the inserted document if successful, otherwise None.
#     """
#     # Initialize the final response structure
#     final_response = {
#         "success": True,
#         "message": "",
#         "data": None
#     }
#
#     try:
#         # Create a document for MongoDB using the StoreEligibilityCriteria model
#         document = StoreEligibilityCriteria(
#             ecid=job_id,
#             inclusion_criteria=trial_inclusion_criteria,
#             exclusion_criteria=trial_exclusion_criteria,
#             categorizedData=categorized_data,
#             userCategorizedData=categorized_data_user,
#             trailDocuments=trial_documents,
#             created_at=datetime.now(),  # Timestamp for when the document is created
#             updated_at=datetime.now(),  # Timestamp for when the document is last updated
#         )
#
#         # Insert the document into the MongoDB collection
#         db_response = similar_trials_criteria_results_collection.insert_one(document.dict())
#
#         # Check if the document was successfully inserted
#         if db_response.inserted_id:
#             final_response["success"] = True
#             final_response["message"] = f"Successfully generated and stored similar trials criteria results: {db_response.inserted_id}"
#             final_response["data"] = db_response.inserted_id
#         else:
#             # If insertion failed, update the response message
#             final_response["success"] = False
#             final_response["message"] = "Failed to store similar trials criteria results"
#
#     except Exception as e:
#         # Handle any exceptions and update the response message with the error details
#         final_response['success'] = False
#         final_response['message'] = f"Failed to store similar trials criteria results: {e}"
#
#     return final_response