from agents.TrialEligibilityAgent import TrialEligibilityAgent
from providers.openai.generate_embeddings import azure_client
from database.document_retrieval.fetch_processed_trial_document_with_nct_id import fetch_processed_trial_document_with_nct_id
from database.document_retrieval.record_eligibility_criteria_job import record_eligibility_criteria_job
from database.document_retrieval.fetch_similar_trials_inputs_with_ecid import fetch_similar_trials_inputs_with_ecid
from document_retrieval.utils.categorize_eligibility_criteria import categorize_eligibility_criteria
from utils.generate_object_id import generate_object_id
from database.document_retrieval.store_notification_data import store_notification_data
from database.document_retrieval.update_workflow_status import update_workflow_status


async def generate_trial_eligibility_criteria(ecid: str, trail_documents_ids: list) -> dict:
    """
    Generate trial eligibility criteria in batches of 2 documents.
    """
    final_response = {
        "success": False,
        "message": "",
        "data": None
    }

    try:
        # Fetch User Inputs from DB
        similar_trials_input_response = fetch_similar_trials_inputs_with_ecid(ecid=ecid)
        if similar_trials_input_response["success"] is False:
            final_response["message"] = similar_trials_input_response["message"]
            return final_response

        user_inputs = similar_trials_input_response["data"]["userInput"]
        trial_rationale = user_inputs.get("rationale", "No rationale provided")
        inclusion_criteria = user_inputs.get("inclusionCriteria", "No inclusion criteria provided")
        exclusion_criteria = user_inputs.get("exclusionCriteria", "No exclusion criteria provided")
        trial_objectives = user_inputs.get("objective", "No trial objectives provided")
        trialOutcomes = user_inputs.get("trialOutcomes", "No trial outcomes provided")

        trial_documents = similar_trials_input_response["data"]["similarTrials"]

        # Process and prepare similar trial documents
        similar_documents = []
        for item in trial_documents:
            nct_id = item["nctId"]
            if nct_id in trail_documents_ids:
                similarity_score = item["similarity_score"]
                doc = fetch_processed_trial_document_with_nct_id(nct_id=nct_id)["data"]
                similar_documents.append({
                    "nctId": nct_id,
                    "similarity_score": similarity_score,
                    "document": {
                        "title": doc["officialTitle"],
                        "inclusionCriteria": doc["inclusionCriteria"],
                        "exclusionCriteria": doc["exclusionCriteria"]
                    }
                })

        # Sort trials by score
        similar_documents.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Initialize the TrialEligibilityAgent
        eligibility_agent = TrialEligibilityAgent(azure_client, max_tokens=4000)

        # Initialize lists to store generated criteria
        generated_inclusion_criteria = []
        generated_exclusion_criteria = []

        # Process documents in batches of 2
        for i in range(0, len(similar_documents), 2):
            batch = similar_documents[i:i + 2]

            eligibility_criteria_response = eligibility_agent.draft_eligibility_criteria(
                sample_trial_rationale=trial_rationale,
                similar_trial_documents=batch,
                user_provided_inclusion_criteria=inclusion_criteria,
                user_provided_exclusion_criteria=exclusion_criteria,
                user_provided_trial_outcome=trialOutcomes,
                user_provided_trial_objective=trial_objectives,
                generated_inclusion_criteria=generated_inclusion_criteria,
                generated_exclusion_criteria=generated_exclusion_criteria
            )

            if eligibility_criteria_response["success"] is False:
                final_response["message"] = eligibility_criteria_response["message"]
                return final_response

            # Append batch results
            generated_inclusion_criteria.extend(eligibility_criteria_response["data"]["inclusionCriteria"])
            generated_exclusion_criteria.extend(eligibility_criteria_response["data"]["exclusionCriteria"])

        # Assign unique IDs
        for item in generated_inclusion_criteria:
            item["criteriaID"] = f"cid_{generate_object_id()}"
        for item in generated_exclusion_criteria:
            item["criteriaID"] = f"cid_{generate_object_id()}"

        final_data = {
            "inclusionCriteria": generated_inclusion_criteria,
            "exclusionCriteria": generated_exclusion_criteria
        }

        user_provided_criteria = {
            "inclusionCriteria": [{
                "criteria": inclusion_criteria,
                "criteriaID": f"cid_{generate_object_id()}",
                "source": "User Provided"
            }],
            "exclusionCriteria": [{
                "criteria": exclusion_criteria,
                "criteriaID": f"cid_{generate_object_id()}",
                "source": "User Provided"
            }]
        }

        # Categorize response
        categorizedGeneratedDataResponse = categorize_eligibility_criteria(eligibility_agent, final_data)
        if categorizedGeneratedDataResponse["success"] is False:
            print(categorizedGeneratedDataResponse["message"])
            categorizedGeneratedData = {}
        else:
            categorizedGeneratedData = categorizedGeneratedDataResponse["data"]

        categorizedUserDataResponse = categorize_eligibility_criteria(eligibility_agent, user_provided_criteria)
        if categorizedUserDataResponse["success"] is False:
            print(categorizedUserDataResponse["message"])
            categorizedUserData = {}
        else:
            categorizedUserData = categorizedUserDataResponse["data"]

        # Store job in DB
        db_response = record_eligibility_criteria_job(ecid, categorizedGeneratedData, categorizedUserData)
        notification_response = store_notification_data(ecid=ecid)
        workflow_status_response = update_workflow_status(ecid=ecid,
                                                          step="similar-criteria")
        print(workflow_status_response["message"])
        print(notification_response["message"])
        final_response["message"] = db_response.get("message", "Successfully generated trial eligibility criteria.")

        inclusion_criteria = [ item["criteria"] for item in generated_inclusion_criteria]
        exclusion_criteria = [ item["criteria"] for item in generated_exclusion_criteria]

        # Prepare final response
        model_generated_eligibility_criteria = {
            "inclusionCriteria": inclusion_criteria,
            "exclusionCriteria": exclusion_criteria,
            "categorizedData": categorizedGeneratedData,
            "userCategorizedData": categorizedUserData,
        }

        final_response["data"] = model_generated_eligibility_criteria
        final_response["success"] = True
        return final_response

    except Exception as e:
        final_response['message'] = f"Failed to generate trial eligibility criteria. Error: {e}"
        return final_response