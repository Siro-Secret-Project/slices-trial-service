from database.document_retrieval.fetch_processed_trial_document_with_nct_id import fetch_processed_trial_document_with_nct_id
from providers.openai.generate_embeddings import generate_embeddings_from_azure_client
from sklearn.metrics.pairwise import cosine_similarity


def calculate_weighted_similarity_score(user_input_document: dict, target_document: dict) -> dict:
    final_response = {
        "success": False,
        "message": "Failed to calculate weighted similarity score",
        "data": None
    }
    try:
        weights = {
            "eligibilityModule": 0.175,
            "conditionsModule": 0.105,
            "identificationModule": 0.14,
            "outcomesModule": 0.14,
            "interventionsModule": 0.14,
            "trialRationale": 0.30,
        }

        # Generate embeddings for the target document
        embedded_target_document = {
            module: generate_embeddings_from_azure_client(value)
            for module, value in target_document.items() if value is not None
        }

        # Generate embeddings for the user input document (only for present modules)
        embedded_user_input_document = {
            module: generate_embeddings_from_azure_client(value)
            for module, value in user_input_document.items() if value is not None
        }

        # Calculate weighted similarity
        total_weight = 0
        weighted_similarity_sum = 0

        for module, user_embedding in embedded_user_input_document.items():
            if module in embedded_target_document:
                target_embedding = embedded_target_document[module]

                # Ensure embeddings are 2D
                similarity_score = cosine_similarity(user_embedding, target_embedding)[0][0]

                weight = weights.get(module, 0)  # Use 0 if module weight is missing
                weighted_similarity_sum += similarity_score * weight
                total_weight += weight

        if total_weight > 0:
            weighted_similarity_score = weighted_similarity_sum / total_weight
            final_response = {
                "success": True,
                "message": "Weighted similarity score calculated successfully",
                "data": {
                    "weighted_similarity_score": weighted_similarity_score
                }
            }
        else:
            final_response["message"] = "No valid modules found for comparison"

    except Exception as e:
        final_response["message"] = f"Failed to calculate weighted similarity score: {e}"

    return final_response

def process_similarity_scores(target_documents_ids: list, user_input_document: dict) -> dict:
    final_response = {
        "success": False,
        "message": "Failed to process weighted similarity score",
        "data": None
    }
    try:
        mapping = {
            "officialTitle": "identificationModule",
            "conditions": "conditionsModule",
            "inclusionCriteria": "eligibilityModule",
            "exclusionCriteria": "eligibilityModule",
            "primaryOutcomes": "outcomesModule",
            "secondaryOutcomes": "outcomesModule",
            "designModule": "designModule",
            "interventions": "interventionsModule",
        }
        # fetch and process input documents
        processed_target_documents = []
        for target_document_id in target_documents_ids:
            target_document_response = fetch_processed_trial_document_with_nct_id(nct_id=target_document_id)
            if target_document_response["success"] is True:
                target_document = target_document_response["data"]
                processed_target_document = {}
                for key, value in target_document.items():
                    if key == "designModule":
                        value = " ,".join(value)
                    key = mapping.get(key, key)
                    processed_target_document[key] = value

                processed_target_documents.append(processed_target_document)
                # Calculate Similarity Scores
                similarity_score_response = calculate_weighted_similarity_score(processed_target_document, user_input_document)
                if similarity_score_response["success"] is True:
                    processed_target_document["weighted_similarity_score"] = round((similarity_score_response["data"]["weighted_similarity_score"] * 100), 2)


        # return response
        final_response["data"] = processed_target_documents
        final_response["message"] = "Successfully calculated weighted similarity score"
        final_response["success"] = True

        return final_response

    except Exception as e:
        print(f'Failed to process weighted similarity score: {e}')
        final_response["message"] = f"Failed to process weighted similarity score: {e}"

    return final_response