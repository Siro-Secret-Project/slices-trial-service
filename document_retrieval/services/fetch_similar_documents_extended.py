from providers.openai.generate_embeddings import validate_document_similarity
from providers.pinecone.similarity_search_service import query_pinecone_db_extended
from document_retrieval.utils.fetch_trial_filters import fetch_trial_filters

async def fetch_similar_documents_extended(documents_search_keys: dict) -> dict:
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
        def process_criteria(criteria: str, module: str = None) -> list:
            """
            Process a single search criteria, query the Pinecone DB, validate documents,
            and return a list of documents with high similarity scores.
            """
            if not criteria:
                return []

            pinecone_response = query_pinecone_db_extended(query=criteria, module=module)
            for item in pinecone_response["data"]:
                del item["similarity_score"]

            document_validation = validate_document_similarity(
                query=criteria, similar_documents=pinecone_response["data"]
            )
            validity_score = document_validation["data"]["response"]

            # generate a final data list
            final_list = [
                {"nctId": nctId, "similarity_score": score, "module": module} for nctId, score in validity_score.items() if score >= 90
            ]

            return final_list

        # Process each criteria and store the results
        inclusion_criteria_documents = process_criteria(
            documents_search_keys.get("inclusion_criteria"), module="eligibilityModule"
        )
        exclusion_criteria_documents = process_criteria(
            documents_search_keys.get("exclusion_criteria"), module="eligibilityModule"
        )
        trial_rationale_documents = process_criteria(
            documents_search_keys.get("rationale")
        )

        trial_objective_documents = process_criteria(
            documents_search_keys.get("objective"), module="identificationModule"
        )

        trial_outcomes_documents = process_criteria(
            documents_search_keys.get("trial_outcomes"), module="outcomesModule"
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
            final_response.update({
                "data": fetch_add_documents_filter_response["data"],
                "success": True,
                "message": "Successfully fetched additional documents.",
            }
            )
            return final_response

        final_response.update({
            "success": True,
            "message": "Successfully fetched similar documents extended.",
            "data": list(unique_documents.values())
        })
        return final_response

    except Exception as e:
        final_response["message"] += f" {e}"
        return final_response
