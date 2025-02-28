from database.document_retrieval.fetch_processed_trial_document_with_nct_id import \
    fetch_processed_trial_document_with_nct_id
from providers.openai.generate_embeddings import generate_embeddings_from_azure_client
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def calculate_weighted_similarity_score(user_input_document: dict, target_document: dict, weights: dict) -> dict:
    """
    Calculate the weighted similarity score between a user input document and a target document
    using cosine similarity of their embeddings.

    Args:
        user_input_document (dict): A dictionary containing different sections of the user input document.
        target_document (dict): A dictionary containing different sections of the target document.
        weights (dict): A dictionary containing different sections of the similarity weights.

    Returns:
        dict: A response dictionary with success status, message, and similarity scores.
    """
    final_response = {
        "success": False,
        "message": "Failed to calculate weighted similarity score",
        "data": None
    }
    try:

        # Identify modules that should be excluded (i.e., those with None values in user input)
        excluded_modules = [module for module, value in user_input_document.items() if value is None]

        # Generate embeddings for non-excluded modules in user input document
        embedded_user_input_document = {
            module: generate_embeddings_from_azure_client(value)["data"].flatten().tolist()
            for module, value in user_input_document.items()
            if module not in excluded_modules
        }

        # Generate embeddings for non-excluded modules in the target document (excluding 'rationale')
        embedded_target_document = {
            module: generate_embeddings_from_azure_client(value)["data"].flatten().tolist()
            for module, value in target_document.items()
            if module not in excluded_modules
        }

        # Compute cosine similarity for each section (excluding 'rationale')
        similarity_scores = {}
        for module in embedded_target_document.keys():  # Only iterate over target's modules
            user_embedding = np.array(embedded_user_input_document[module]).reshape(1, -1)
            target_embedding = np.array(embedded_target_document[module]).reshape(1, -1)
            similarity_scores[module] = cosine_similarity(user_embedding, target_embedding)[0][0]

        # Compute weighted similarity score
        weighted_similarity_score = sum(similarity_scores[module] * weights[module] for module in similarity_scores)

        # Normalize by the sum of weights
        sum_weights = sum(weights[module] for module in similarity_scores.keys())
        weighted_similarity_score /= sum_weights

        final_response["success"] = True
        final_response["message"] = "Weighted similarity score calculated successfully"
        final_response["data"] = {
            "weighted_similarity_score": weighted_similarity_score,
            "similarity_scores": similarity_scores
        }

    except Exception as e:
        final_response["message"] = f"Failed to calculate weighted similarity score: {e}"

    return final_response


def process_similarity_scores(target_documents_ids: list, user_input_document: dict, weights: dict) -> dict:
    """
    Process similarity scores for a list of target documents against a user input document.

    Args:
        target_documents_ids (list): List of target document NCT IDs.
        user_input_document (dict): Dictionary containing different sections of the user input document.
        weights (dict): Dictionary containing different sections of the similarity weights.

    Returns:
        dict: A response dictionary with success status, message, and a list of similarity scores for each target document.
    """
    final_response = {
        "success": False,
        "message": "Failed to process weighted similarity score",
        "data": None
    }
    try:
        print(weights)
        trial_target_document = []  # Store similarity scores for each document

        for nctId in target_documents_ids:
            # Fetch target document using its NCT ID
            target_document_response = fetch_processed_trial_document_with_nct_id(nct_id=nctId)
            if target_document_response["success"] is False:
                print(f"Failed to retrieve target document: {nctId}")
                continue

            fetched_target_document = target_document_response["data"]

            # Map target document fields to a structured dictionary
            target_document = {
                "inclusionCriteria": fetched_target_document["inclusionCriteria"],
                "exclusionCriteria": fetched_target_document["exclusionCriteria"],
                "title": fetched_target_document["officialTitle"],
                "trialOutcomes": fetched_target_document["primaryOutcomes"],
                "condition": fetched_target_document["conditions"]
            }

            # Calculate weighted similarity score between user input and target document
            weighted_similarity_score_response = calculate_weighted_similarity_score(user_input_document,
                                                                                     target_document,
                                                                                     weights)
            if weighted_similarity_score_response["success"] is False:
                print(f"Failed to calculate weighted similarity score for {nctId}")
                print(weighted_similarity_score_response["message"])
                continue

            # Extract results and store them
            weighted_similarity_score = weighted_similarity_score_response["data"]["weighted_similarity_score"]
            similarity_scores = weighted_similarity_score_response["data"]["similarity_scores"]
            weighted_similarity_scores = {}
            for module, value in similarity_scores.items():
                weighted_similarity_scores[module] = weights[module] * value
            trial_target_document.append({
                "nctId": nctId,
                "weighted_similarity_score": weighted_similarity_score,
                "similarity_scores": weighted_similarity_scores
            })

        final_response["success"] = True
        final_response["message"] = "Weighted similarity score calculated successfully"
        final_response["data"] = trial_target_document
    except Exception as e:
        print(f'Failed to process weighted similarity score: {e}')
        final_response["message"] = f"Failed to process weighted similarity score: {e}"

    return final_response

