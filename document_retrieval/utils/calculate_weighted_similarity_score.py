"""Module for calculating weighted similarity scores between user input documents and target trial documents."""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from database.document_retrieval.fetch_processed_trial_document_with_nct_id import (
    fetch_processed_trial_document_with_nct_id,
)
from providers.openai.openai_connection import OpenAIClient

def _generate_document_embeddings(document: dict) -> dict:
    """Generates embeddings for each section of the provided document.

    Args:
        document (dict): Dictionary containing different sections of the document.

    Returns:
        dict: Dictionary containing section-wise embeddings.
    """
    openai_client = OpenAIClient()
    return {
        section: openai_client.generate_embeddings(content)["data"].flatten().tolist()
        for section, content in document.items()
        if content is not None
    }

def _calculate_cosine_similarity(user_embedding: list, target_embedding: list) -> float:
    """Computes cosine similarity between two embeddings.

    Args:
        user_embedding (list): Embedding vector for user input.
        target_embedding (list): Embedding vector for target document.

    Returns:
        float: Cosine similarity score.
    """
    return cosine_similarity(
        np.array(user_embedding).reshape(1, -1),
        np.array(target_embedding).reshape(1, -1)
    )[0][0]

def _calculate_weighted_similarity_score(
    user_input_document: dict, target_document: dict, weights: dict
) -> dict:
    """Calculates the weighted similarity score between a user input document and a target document.

    Args:
        user_input_document (dict): User input document with different sections.
        target_document (dict): Target document with different sections.
        weights (dict): Dictionary containing similarity weights for each section.

    Returns:
        dict: Dictionary with success status, message, and similarity scores.
    """
    try:
        print("Embedding documents...")
        user_embeddings = _generate_document_embeddings(user_input_document)
        target_embeddings = _generate_document_embeddings(target_document)
        print("Calculating weighted similarity score...")

        similarity_scores = {
            module: _calculate_cosine_similarity(user_embeddings[module], target_embeddings[module])
            for module in target_embeddings.keys()
        }

        sum_weights = sum(weights[module] for module in similarity_scores.keys())
        weighted_similarity_score = (
            sum(similarity_scores[module] * weights[module] for module in similarity_scores)
            / sum_weights
        )

        return {
            "success": True,
            "message": "Weighted similarity score calculated successfully",
            "data": {
                "weighted_similarity_score": weighted_similarity_score,
                "similarity_scores": similarity_scores,
            },
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to calculate weighted similarity score: {e}",
            "data": None,
        }

def process_similarity_scores(
    target_documents_ids: list, user_input_document: dict, weights: dict
) -> dict:
    """Processes similarity scores for a list of target documents against a user input document.

    Args:
        target_documents_ids (list): List of target document NCT IDs.
        user_input_document (dict): User-provided document sections.
        weights (dict): Dictionary containing similarity weights.

    Returns:
        dict: Dictionary with success status, message, and list of similarity scores per document.
    """
    try:
        trial_target_documents = []

        for nct_id in target_documents_ids:
            target_document_response = fetch_processed_trial_document_with_nct_id(nct_id=nct_id)
            if not target_document_response["success"]:
                print(f"Failed to retrieve target document: {nct_id}")
                continue

            target_document = {
                "inclusionCriteria": target_document_response["data"].get("inclusionCriteria"),
                "exclusionCriteria": target_document_response["data"].get("exclusionCriteria"),
                "title": target_document_response["data"].get("officialTitle"),
                "trialOutcomes": target_document_response["data"].get("primaryOutcomes"),
                "condition": target_document_response["data"].get("conditions"),
            }

            similarity_response = _calculate_weighted_similarity_score(
                user_input_document, target_document, weights
            )
            if not similarity_response["success"]:
                print(f"Failed to calculate weighted similarity score for {nct_id}")
                continue

            trial_target_documents.append({
                "nctId": nct_id,
                "weighted_similarity_score": similarity_response["data"]["weighted_similarity_score"],
                "similarity_scores": {
                    module: weights[module] * value
                    for module, value in similarity_response["data"]["similarity_scores"].items()
                },
            })

        return {
            "success": True,
            "message": "Weighted similarity scores processed successfully",
            "data": trial_target_documents,
        }
    except Exception as e:
        print(f"Failed to process weighted similarity scores: {e}")
        return {
            "success": False,
            "message": f"Failed to process weighted similarity scores: {e}",
            "data": None,
        }
