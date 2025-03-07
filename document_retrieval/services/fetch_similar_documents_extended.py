from document_retrieval.utils.fetch_similar_documents_extended.process_criteria import process_criteria
from document_retrieval.utils.fetch_similar_documents_extended.fetch_trial_filters import fetch_trial_filters
from document_retrieval.utils.fetch_similar_documents_extended.process_filters import process_filters
from document_retrieval.utils.fetch_similar_documents_extended.calculate_weighted_similarity_score import process_similarity_scores
from database.document_retrieval.store_similar_trials import store_similar_trials
from database.document_retrieval.update_workflow_status import update_workflow_status


async def fetch_similar_documents_extended(documents_search_keys: dict, custom_weights: dict, document_filters: dict, user_data: dict) -> dict:
    """
    Fetch similar documents based on inclusion criteria, exclusion criteria, and trial rationale,
    ensuring unique values in the final list by retaining the entry with the highest similarity score.

    Args:
        documents_search_keys (dict): Dictionary containing search keys for documents.
        custom_weights (dict): Dictionary containing custom weights for similarity score calculation.
        document_filters (dict): Dictionary containing filters to apply on documents.
        user_data (dict): Dictionary containing user-specific data.

    Returns:
        dict: Response dictionary with success status, message, and data.
    """
    final_response = {
        "success": False,
        "message": "Failed to fetch similar documents extended.",
        "data": None,
    }

    try:
        user_inputs = documents_search_keys | document_filters

        # Process each criteria and store the results
        print(f"Pinecone DB Started")
        criteria_documents = _process_all_criteria(documents_search_keys)
        print("Documents fetched")

        # Combine all documents and ensure uniqueness by retaining the highest similarity score
        unique_documents = _combine_and_ensure_unique_documents(criteria_documents)
        print("Unique documents fetched")

        # Filter documents based on additional filters
        trial_documents = _filter_documents(unique_documents, document_filters)
        print("Trial documents fetched")

        if not trial_documents:
            _store_and_return_empty_response(user_data, user_inputs, final_response)
            return final_response

        # Calculate weighted average for similarity score
        _calculate_weighted_similarity_scores(trial_documents, documents_search_keys, custom_weights)
        print("Calculated similarity scores")

        # Sort trial documents based on weighted similarity score
        trial_documents = sorted(trial_documents, key=lambda trial_item: trial_item["weighted_similarity_score"], reverse=True)
        print("Trial documents sorted by weighted similarity score")

        # Store similar trials and update workflow status
        _store_similar_trials_and_update_status(user_data, user_inputs, trial_documents)
        print("Updated similar trials status")

        final_response["data"] = trial_documents[:100]
        final_response["success"] = True
        final_response["message"] = "Successfully fetched similar documents extended."
        return final_response

    except Exception as e:
        final_response["message"] += f"Unexpected error occurred while fetching similar documents: {e}"
        return final_response


def _process_all_criteria(documents_search_keys: dict) -> list:
    """
    Process all criteria (inclusion, exclusion, rationale, conditions, outcomes, title) and return combined documents.

    Args:
        documents_search_keys (dict): Dictionary containing search keys for documents.

    Returns:
        list: List of documents processed from all criteria.
    """
    inclusion_criteria_documents = process_criteria(
        documents_search_keys.get("inclusionCriteria"),
        module="eligibilityModule",
        document_search_data=documents_search_keys,
    )
    exclusion_criteria_documents = process_criteria(
        documents_search_keys.get("exclusionCriteria"),
        module="eligibilityModule",
        document_search_data=documents_search_keys,
    )
    trial_rationale_documents = process_criteria(
        documents_search_keys.get("rationale"),
        document_search_data=documents_search_keys,
    )
    for item in trial_rationale_documents:
        item["module"] = "trialRationale"

    trial_conditions_documents = process_criteria(
        documents_search_keys.get("condition"),
        module="conditionsModule",
        document_search_data=documents_search_keys,
    )

    trial_outcomes_documents = process_criteria(
        documents_search_keys.get("trialOutcomes"),
        module="outcomesModule",
        document_search_data=documents_search_keys,
    )

    trial_title_documents = process_criteria(
        documents_search_keys.get("title"),
        module="identificationModule",
        document_search_data=documents_search_keys,
    )

    return (
        inclusion_criteria_documents
        + exclusion_criteria_documents
        + trial_rationale_documents
        + trial_conditions_documents
        + trial_outcomes_documents
        + trial_title_documents
    )


def _combine_and_ensure_unique_documents(documents: list) -> dict:
    """
    Combine all documents and ensure uniqueness by retaining the entry with the highest similarity score.

    Args:
        documents (list): List of documents to combine.

    Returns:
        dict: Dictionary of unique documents with the highest similarity score.
    """
    unique_documents = {}
    for doc in documents:
        nctId = doc["nctId"]
        if nctId not in unique_documents or doc["similarity_score"] > unique_documents[nctId]["similarity_score"]:
            unique_documents[nctId] = doc
    return unique_documents


def _filter_documents(unique_documents: dict, document_filters: dict) -> list:
    """
    Filter documents based on additional filters.

    Args:
        unique_documents (dict): Dictionary of unique documents.
        document_filters (dict): Dictionary containing filters to apply on documents.

    Returns:
        list: List of filtered documents.
    """
    fetch_add_documents_filter_response = fetch_trial_filters(trial_documents=list(unique_documents.values()))
    if fetch_add_documents_filter_response["success"]:
        trial_documents_with_filters = fetch_add_documents_filter_response["data"]
        trial_documents = process_filters(documents=trial_documents_with_filters, filters=document_filters)
        elements_to_append = [item for item in trial_documents_with_filters if item not in trial_documents]
        trial_documents.extend(elements_to_append)
        return trial_documents
    return list(unique_documents.values())


def _store_and_return_empty_response(user_data: dict, user_inputs: dict, final_response: dict) -> None:
    """
    Store similar trials and return an empty response if no documents are found.

    Args:
        user_data (dict): Dictionary containing user-specific data.
        user_inputs (dict): Dictionary containing user inputs.
        final_response (dict): Final response dictionary to update.
    """
    db_response = store_similar_trials(
        user_name=user_data["userName"],
        ecid=user_data["ecid"],
        user_input=user_inputs,
        similar_trials=[],
    )
    print(db_response)
    final_response["message"] = "No Documents Found matching criteria."
    final_response["success"] = True
    final_response["data"] = []


def _calculate_weighted_similarity_scores(trial_documents: list, documents_search_keys: dict, custom_weights: dict) -> None:
    """
    Calculate weighted similarity scores for trial documents.

    Args:
        trial_documents (list): List of trial documents.
        documents_search_keys (dict): Dictionary containing search keys for documents.
        custom_weights (dict): Dictionary containing custom weights for similarity score calculation.
    """
    nctIds = [item["nctId"] for item in trial_documents]
    weighted_similarity_scores_response = process_similarity_scores(
        target_documents_ids=nctIds,
        user_input_document=documents_search_keys,
        weights=custom_weights,
    )
    if weighted_similarity_scores_response["success"]:
        for item in weighted_similarity_scores_response["data"]:
            for subitem in trial_documents:
                if subitem["nctId"] == item["nctId"]:
                    subitem["weighted_similarity_score"] = item["weighted_similarity_score"]
                    subitem["module_similarity_scores"] = item["similarity_scores"]


def _store_similar_trials_and_update_status(user_data: dict, user_inputs: dict, trial_documents: list) -> None:
    """
    Store similar trials and update workflow status.

    Args:
        user_data (dict): Dictionary containing user-specific data.
        user_inputs (dict): Dictionary containing user inputs.
        trial_documents (list): List of trial documents.
    """
    db_response = store_similar_trials(
        user_name=user_data["userName"],
        ecid=user_data["ecid"],
        user_input=user_inputs,
        similar_trials=trial_documents,
    )
    status_response = update_workflow_status(ecid=user_data["ecid"], step="trial-services")
    print(status_response)
    print(db_response)