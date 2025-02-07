from document_retrieval.utils.process_criteria import process_criteria
from document_retrieval.utils.fetch_trial_filters import fetch_trial_filters
from document_retrieval.utils.calculate_weighted_similarity_score import process_similarity_scores

# Defaults weights
default_weights = {
    "inclusionCriteria": 0.2,
    "exclusionCriteria": 0.2,
    "objective": 0.2,
    "rationale": 0.2,
    "trialOutcomes": 0.2
}


async def fetch_similar_documents_extended(documents_search_keys: dict, custom_weights: dict = None) -> dict:
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
        # Process each criteria and store the results
        inclusion_criteria_documents = process_criteria(
            documents_search_keys.get("inclusionCriteria"), module="eligibilityModule"
        )
        exclusion_criteria_documents = process_criteria(
            documents_search_keys.get("exclusionCriteria"), module="eligibilityModule"
        )
        trial_rationale_documents = process_criteria(
            documents_search_keys.get("rationale")
        )
        for item in trial_rationale_documents:
            item["module"] = "trialRationale"

        trial_objective_documents = process_criteria(
            documents_search_keys.get("objective"), module="identificationModule"
        )

        trial_outcomes_documents = process_criteria(
            documents_search_keys.get("trialOutcomes"), module="outcomesModule"
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
        else:
            trial_documents = list(unique_documents.values())

        # Calculate weighted average for similarity score
        nctIds = [item["nctId"] for item in trial_documents]
        weights = custom_weights if custom_weights is not None else default_weights
        weighted_similarity_scores_response = process_similarity_scores(target_documents_ids=nctIds,
                                                                        user_input_document=documents_search_keys,
                                                                        weights=weights)
        if weighted_similarity_scores_response["success"] is True:
            for item in weighted_similarity_scores_response["data"]:
                for subitem in trial_documents:
                    if subitem["nctId"] == item["nctId"]:
                        subitem["weighted_similarity_score"] = item["weighted_similarity_score"]
                        subitem["module_similarity_scores"] = item["similarity_scores"]

        print("Calculated weighted_similarity_score")

        # Sort trial based on score
        trial_documents = [item for item in trial_documents if item["similarity_score"] >= 90]
        trial_documents = sorted(trial_documents, key=lambda trial_item: trial_item["similarity_score"], reverse=True)

        final_response["data"] = trial_documents
        final_response["success"] = True
        final_response["message"] = "Successfully fetched similar documents extended."
        return final_response

    except Exception as e:
        final_response["message"] += f"Unexpected error occurred while fetching similar documents: {e}"
        return final_response
