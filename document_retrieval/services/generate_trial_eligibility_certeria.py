from agents.TrialEligibilityAgent import TrialEligibilityAgent
from providers.openai.generate_embeddings import azure_client
from database.document_retrieval.fetch_processed_trial_document_with_nct_id import fetch_processed_trial_document_with_nct_id
from database.document_retrieval.record_eligibility_criteria_job import record_eligibility_criteria_job
from database.document_retrieval.fetch_similar_trials_inputs_with_ecid import fetch_similar_trials_inputs_with_ecid
from document_retrieval.utils.categorize_eligibility_criteria import categorize_eligibility_criteria
from utils.generate_object_id import generate_object_id


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
        eligibility_agent = TrialEligibilityAgent(azure_client, max_tokens=4000)

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
        print("Criteria Generated")

        eligibility_criteria = eligibility_criteria_response["data"]
        generated_inclusion_criteria = eligibility_criteria_response["data"]["inclusionCriteria"]
        filtered_inclusion_criteria = []
        for item in generated_inclusion_criteria:
            item["criteriaID"] = f"cid_{generate_object_id()}"
            filtered_inclusion_criteria.append(item)

        generated_exclusion_criteria = eligibility_criteria_response["data"]["exclusionCriteria"]
        filtered_exclusion_criteria = []
        for item in generated_exclusion_criteria:
            item["criteriaID"] = f"cid_{generate_object_id()}"
            filtered_exclusion_criteria.append(item)

        final_data = {
            "inclusionCriteria": filtered_inclusion_criteria,
            "exclusionCriteria": filtered_exclusion_criteria
        }
        print("Added IDs")

        # Format the generated eligibility criteria
        model_generated_eligibility_criteria = {}

        # Categorise response
        categorizedGeneratedData = categorize_eligibility_criteria(eligibility_agent=eligibility_agent,
                                                                   eligibility_criteria=final_data)
        categorizedGeneratedData = categorizedGeneratedData["data"]
        print("Categorized System Data")


        user_provided_criteria = {
            "inclusionCriteria": [{"criteria": inclusion_criteria,
                                  "criteriaID": f"cid_{generate_object_id()}",
                                  "source": "User Provided"}],
            "exclusionCriteria": [{"criteria": exclusion_criteria,
                                  "criteriaID": f"cid_{generate_object_id()}",
                                  "source": "User Provided"}],
        }
        categorizedUserData = categorize_eligibility_criteria(eligibility_agent=eligibility_agent,
                                                              eligibility_criteria=user_provided_criteria)
        categorizedUserData = categorizedUserData["data"]
        print("Categorized User Data")


        # Store Job in DB
        db_response = record_eligibility_criteria_job(job_id=ecid,
                                                      categorized_data=categorizedGeneratedData,
                                                      categorized_data_user=categorizedUserData)
        if db_response["success"] is True:
            final_response["message"] = db_response["message"]
        else:
            final_response["message"] = "Successfully generated trial eligibility criteria." + db_response["message"]

        print(db_response)


        # Add Categorized Data in final response
        model_generated_eligibility_criteria["categorizedData"] = categorizedGeneratedData
        model_generated_eligibility_criteria["userCategorizedData"] = categorizedUserData

        # Update the final response with the generated criteria
        final_response["data"] = model_generated_eligibility_criteria
        final_response["success"] = True
        return final_response

    except Exception as e:
        # Handle any exceptions and update the response message with the error details
        final_response['message'] = f"Failed to generate trial eligibility criteria.\n{e}"
        return final_response