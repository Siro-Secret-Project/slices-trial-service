from document_retrieval.utils.process_criteria import process_criteria
from document_retrieval.utils.fetch_trial_filters import fetch_trial_filters
from document_retrieval.utils.process_filters import process_filters
from document_retrieval.utils.calculate_weighted_similarity_score import process_similarity_scores
from database.document_retrieval.store_similar_trials import store_similar_trials


async def fetch_similar_documents_extended(documents_search_keys: dict, custom_weights: dict, document_filters: dict, user_data: dict) -> dict:
    """
    Fetch similar documents based on inclusion criteria, exclusion criteria, and trial rationale,
    ensuring unique values in the final list by retaining the entry with the highest similarity score.
    """
    final_response = {
        "success": False,
        "message": "Failed to fetch similar documents extended.",
        "data": None
    }

    try:
        user_inputs = documents_search_keys | document_filters

        # Process each criteria and store the results
        inclusion_criteria_documents = process_criteria(
            documents_search_keys.get("inclusionCriteria"),
            module="eligibilityModule",
            document_search_data=documents_search_keys
        )
        exclusion_criteria_documents = process_criteria(
            documents_search_keys.get("exclusionCriteria"),
            module="eligibilityModule",
            document_search_data=documents_search_keys
        )
        trial_rationale_documents = process_criteria(
            documents_search_keys.get("rationale"),
            document_search_data=documents_search_keys
        )
        for item in trial_rationale_documents:
            item["module"] = "trialRationale"

        trial_objective_documents = process_criteria(
            documents_search_keys.get("objective"),
            module="identificationModule",
            document_search_data=documents_search_keys
        )

        trial_outcomes_documents = process_criteria(
            documents_search_keys.get("trialOutcomes"),
            module="outcomesModule",
            document_search_data=documents_search_keys
        )
        # Combine all documents and ensure uniqueness by retaining the highest similarity score
        combined_documents = (
            inclusion_criteria_documents +
            exclusion_criteria_documents +
            trial_rationale_documents +
            trial_objective_documents +
            trial_outcomes_documents
        )
        unique_documents = {}
        for doc in combined_documents:
            nctId = doc["nctId"]
            if nctId not in unique_documents or doc["similarity_score"] > unique_documents[nctId]["similarity_score"]:
                unique_documents[nctId] = doc

        # filter documents
        fetch_add_documents_filter_response = fetch_trial_filters(trial_documents=list(unique_documents.values()))
        if fetch_add_documents_filter_response["success"] is True:
            trial_documents = fetch_add_documents_filter_response["data"]
            print(f"Documents length: {len(trial_documents)}")
            trial_documents = process_filters(documents=trial_documents, filters=document_filters)
            print(f"Documents length: {len(trial_documents)}")
            if len(trial_documents) == 0:
                db_response = store_similar_trials(user_name=user_data["userName"],
                                                   ecid=user_data["ecid"],
                                                   user_input=user_inputs,
                                                   similar_trials=trial_documents)
                print(db_response)
                final_response["message"] = "No Documents Found matching criteria."
                final_response["success"] = True
                final_response["data"] = []
                return final_response
        else:
            trial_documents = list(unique_documents.values())

        # Calculate weighted average for similarity score
        nctIds = [item["nctId"] for item in trial_documents]
        weighted_similarity_scores_response = process_similarity_scores(target_documents_ids=nctIds,
                                                                        user_input_document=documents_search_keys,
                                                                        weights=custom_weights)
        if weighted_similarity_scores_response["success"] is True:
            for item in weighted_similarity_scores_response["data"]:
                for subitem in trial_documents:
                    if subitem["nctId"] == item["nctId"]:
                        subitem["weighted_similarity_score"] = item["weighted_similarity_score"]
                        subitem["module_similarity_scores"] = item["similarity_scores"]

        print("Calculated weighted_similarity_score")

        # Sort trial based on score
        trial_documents = sorted(trial_documents, key=lambda trial_item: trial_item["weighted_similarity_score"], reverse=True)

        # Store Similar trials
        db_response = store_similar_trials(user_name=user_data["userName"],
                                           ecid=user_data["ecid"],
                                           user_input=user_inputs,
                                           similar_trials=trial_documents)

        print(db_response)

        final_response["data"] = trial_documents
        final_response["success"] = True
        final_response["message"] = "Successfully fetched similar documents extended."
        return final_response

    except Exception as e:
        final_response["message"] += f"Unexpected error occurred while fetching similar documents: {e}"
        return final_response
