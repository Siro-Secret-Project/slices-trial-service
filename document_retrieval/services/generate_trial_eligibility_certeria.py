from Tools.scripts.summarize_stats import categorized_counts

from providers.pinecone.similarity_search_service import pinecone_index
from document_retrieval.services.fetch_similar_documents_extended import fetch_similar_documents_extended
from agents.TrialEligibilityAgent import TrialEligibilityAgent
from providers.openai.generate_embeddings import azure_client
from database.document_retrieval.fetch_processed_trial_document_with_nct_id import t2dm_collection, fetch_processed_trial_document_with_nct_id
from database.document_retrieval.record_eligibility_criteria_job import record_eligibility_criteria_job


async def generate_trial_eligibility_criteria(documents_search_keys: dict, ecid: str) -> dict:
    """
    Generates trial eligibility criteria based on similar trial documents and a provided rationale.

    This function fetches similar trial documents using the provided search keys, processes them,
    and uses an eligibility agent to draft inclusion and exclusion criteria for a new trial.

    Args:
        documents_search_keys (dict): A dictionary containing search keys, including a rationale
                                     for the trial and other parameters required to fetch similar
                                     trial documents.
        ecid (str): The Job ID for the Eligibility Agent.

    Returns:
        dict: A response dictionary containing:
              - success (bool): Indicates whether the operation was successful.
              - message (str): A message describing the outcome of the operation.
              - data (dict or None): Contains the generated eligibility criteria if successful,
                                     otherwise None.
    """
    # Initialize the final response structure
    final_response = {
        "success": False,
        "message": "Failed to generate trial eligibility criteria.",
        "data": None
    }

    try:
        # Fetch similar trial documents using the provided search keys
        trial_documents_response = await fetch_similar_documents_extended(documents_search_keys=documents_search_keys)
        inclusion_criteria = documents_search_keys["inclusion_criteria"]
        inclusion_criteria = inclusion_criteria if inclusion_criteria is not None else "No inclusion criteria provided"
        exclusion_criteria = documents_search_keys["exclusion_criteria"]
        exclusion_criteria = exclusion_criteria if exclusion_criteria is not None else "No exclusion criteria provided"

        # Check if fetching similar documents was unsuccessful
        if trial_documents_response["success"] is False:
            final_response["message"] = trial_documents_response["message"]
            return final_response

        # Extract the list of similar trial documents
        trial_documents = trial_documents_response["data"]

        # Initialize the TrialEligibilityAgent with required parameters
        eligibility_agent = TrialEligibilityAgent(
            azure_client,
            max_tokens=3000,
            documents_collection=t2dm_collection,
            pinecone_index=pinecone_index
        )

        # Process and prepare similar trial documents for eligibility criteria generation
        similar_documents = []
        for item in trial_documents:
            # Fetch the processed trial document using the NCT ID
            doc = fetch_processed_trial_document_with_nct_id(nct_id=item["nctId"])["data"]
            similarity_score = item["similarity_score"]
            similar_documents.append({
                "nctId": item["nctId"],
                "similarity_score": similarity_score,
                "document": doc
            })

        # Generate eligibility criteria using the eligibility agent
        eligibility_criteria_response = eligibility_agent.draft_eligibility_criteria(
            sample_trial_rationale=documents_search_keys["rationale"],
            similar_trial_documents=similar_documents,
            user_provided_inclusion_criteria=inclusion_criteria,
            user_provided_exclusion_criteria=exclusion_criteria,
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
        categorized_agent_response = eligibility_agent.categorise_eligibility_criteria(eligibility_criteria=eligibility_criteria)
        if categorized_agent_response["success"] is False:
            final_response["message"] = categorized_agent_response["message"]
            return final_response


        # Categorize the data
        categorizedData = {}
        for item in categorized_agent_response["data"]["inclusionCriteria"]:
            item_class = item["class"]
            categorizedData[item_class] = {"Inclusion": [], "Exclusion": []}
            criteria = item["criteria"]
            categorizedData[item_class]["Inclusion"].append(criteria)

        for item in categorized_agent_response["data"]["exclusionCriteria"]:
            item_class = item["class"]
            categorizedData[item_class] = {"Inclusion": [], "Exclusion": []}
            criteria = item["criteria"]
            categorizedData[item_class]["Exclusion"].append(criteria)

        # Categorize user data
        categorized_user_data = eligibility_agent.categorise_eligibility_criteria(eligibility_criteria=f"Inclusion: {inclusion_criteria}, Exclusion: {exclusion_criteria}")
        # Categorize the data
        categorizedDataUser = {}
        for item in categorized_user_data["data"]["inclusionCriteria"]:
            item_class = item["class"]
            categorizedDataUser[item_class] = {"Inclusion": [], "Exclusion": []}
            criteria = item["criteria"]
            categorizedDataUser[item_class]["Inclusion"].append(criteria)

        for item in categorized_user_data["data"]["exclusionCriteria"]:
            item_class = item["class"]
            categorizedDataUser[item_class] = {"Inclusion": [], "Exclusion": []}
            criteria = item["criteria"]
            categorizedDataUser[item_class]["Exclusion"].append(criteria)



        # Store Job in DB
        db_response = record_eligibility_criteria_job(job_id=ecid,
                                                      trial_inclusion_criteria=model_generated_eligibility_criteria["inclusionCriteria"],
                                                      trial_exclusion_criteria=model_generated_eligibility_criteria["exclusionCriteria"],
                                                      categorized_data=categorizedData,
                                                      categorized_data_user=categorized_user_data["data"])
        if db_response["success"] is True:
            final_response["message"] = db_response["message"]
        else:
            final_response["message"] = "Successfully generated trial eligibility criteria." + db_response["message"]

        # Add Categorized Data in final response
        model_generated_eligibility_criteria["categorizedData"] = categorizedData
        model_generated_eligibility_criteria["userCategorizedData"] = categorizedDataUser

        # Update the final response with the generated criteria
        final_response["data"] = model_generated_eligibility_criteria
        final_response["success"] = True
        return final_response

    except Exception as e:
        # Handle any exceptions and update the response message with the error details
        final_response['message'] = f"Failed to generate trial eligibility criteria.\n{e}"
        return final_response