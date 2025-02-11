from agents.TrialEligibilityAgent import TrialEligibilityAgent
from providers.openai.generate_embeddings import azure_client
from database.document_retrieval.fetch_processed_trial_document_with_nct_id import fetch_processed_trial_document_with_nct_id
from database.document_retrieval.record_eligibility_criteria_job import record_eligibility_criteria_job
from database.document_retrieval.fetch_similar_trials_inputs_with_ecid import fetch_similar_trials_inputs_with_ecid
from document_retrieval.utils.categorize_eligibility_criteria import categorize_eligibility_criteria


async def generate_trial_eligibility_criteria(ecid: str, trail_documents_ids: list) -> dict:
    """

    """
    # Initialize the final response structure
    final_response = {
        "success": False,
        "message": "Failed to generate trial eligibility criteria.",
        "data": None
    }

    try:
        # Fetch User Inputs from DB
        similar_trials_input_response = fetch_similar_trials_inputs_with_ecid(ecid=ecid)
        if similar_trials_input_response["success"] is False:
            final_response["message"] = similar_trials_input_response["message"]
            return final_response

        user_inputs = similar_trials_input_response["data"]["userInput"]
        trial_rationale = user_inputs["rationale"] if user_inputs["rationale"] is not None else "No rationale provided"
        inclusion_criteria = user_inputs["inclusionCriteria"] if user_inputs["inclusionCriteria"] is not None else "No inclusion criteria provided"
        exclusion_criteria = user_inputs["exclusionCriteria"] if user_inputs["exclusionCriteria"] is not None else "No exclusion criteria provided"
        trial_objectives = user_inputs["objective"] if user_inputs["objective"] is not None else "No trial objectives provided"
        trialOutcomes = user_inputs["trialOutcomes"] if user_inputs["trialOutcomes"] is not None else "No trial outcomes provided"

        trial_documents = similar_trials_input_response["data"]["similarTrials"]

        # Process and prepare similar trial documents for eligibility criteria generation
        similar_documents = []
        for item in trial_documents:
            # Fetch the processed trial document using the NCT ID
            nct_id = item["nctId"]
            if nct_id in trail_documents_ids:
                similarity_score = item["similarity_score"]
                doc = fetch_processed_trial_document_with_nct_id(nct_id=nct_id)["data"]
                similar_documents.append({
                    "nctId": nct_id,
                    "similarity_score": similarity_score,
                    "document": doc
                })
            else:
                continue

        # Initialize the TrialEligibilityAgent with required parameters
        eligibility_agent = TrialEligibilityAgent(azure_client, max_tokens=3000)

        # Generate eligibility criteria using the eligibility agent
        eligibility_criteria_response = eligibility_agent.draft_eligibility_criteria(
            sample_trial_rationale=trial_rationale,
            similar_trial_documents=similar_documents,
            user_provided_inclusion_criteria=inclusion_criteria,
            user_provided_exclusion_criteria=exclusion_criteria,
            user_provided_trial_outcome=trialOutcomes,
            user_provided_trial_objective=trial_objectives
        )
        if eligibility_criteria_response["success"] is False:
            final_response["message"] = eligibility_criteria_response["message"]
            return final_response

        eligibility_criteria = eligibility_criteria_response["data"]

        # Format the generated eligibility criteria
        model_generated_eligibility_criteria = {
            "inclusionCriteria": [item["criteria"] for item in eligibility_criteria["inclusionCriteria"]],
            "exclusionCriteria": [item["criteria"] for item in eligibility_criteria["exclusionCriteria"]],
        }

        # Categorise response
        categorizedGeneratedData = categorize_eligibility_criteria(eligibility_agent=eligibility_agent,
                                                                   eligibility_criteria=eligibility_criteria)
        categorizedGeneratedData = categorizedGeneratedData["data"]

        user_provided_criteria = f"Inclusion Criteria: {inclusion_criteria}, Exclusion Criteria: {exclusion_criteria}"
        categorizedUserData = categorize_eligibility_criteria(eligibility_agent=eligibility_agent,
                                                              eligibility_criteria=user_provided_criteria)
        categorizedUserData = categorizedUserData["data"]

        # Store Job in DB
        db_response = record_eligibility_criteria_job(job_id=ecid,
                                                      trial_inclusion_criteria=model_generated_eligibility_criteria["inclusionCriteria"],
                                                      trial_exclusion_criteria=model_generated_eligibility_criteria["exclusionCriteria"],
                                                      categorized_data=categorizedGeneratedData,
                                                      categorized_data_user=categorizedUserData,
                                                      trial_documents=trial_documents)
        if db_response["success"] is True:
            final_response["message"] = db_response["message"]
        else:
            final_response["message"] = "Successfully generated trial eligibility criteria." + db_response["message"]


        # Add Categorized Data in final response
        model_generated_eligibility_criteria["categorizedData"] = categorizedGeneratedData
        model_generated_eligibility_criteria["userCategorizedData"] = categorizedUserData
        model_generated_eligibility_criteria["trialDocuments"] = trial_documents

        # Update the final response with the generated criteria
        final_response["data"] = model_generated_eligibility_criteria
        final_response["success"] = True
        return final_response

    except Exception as e:
        # Handle any exceptions and update the response message with the error details
        final_response['message'] = f"Failed to generate trial eligibility criteria.\n{e}"
        return final_response