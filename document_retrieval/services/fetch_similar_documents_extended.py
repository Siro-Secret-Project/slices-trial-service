from providers.openai.generate_embeddings import validate_document_similarity
from providers.pinecone.similarity_search_service import query_pinecone_db_extended

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

            return [
                {"nctId": nctId, "similarity_score": score}
                for nctId, score in validity_score.items() if score >= 90
            ]

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

        # Combine all documents and ensure uniqueness by retaining the highest similarity score
        combined_documents = (
            inclusion_criteria_documents +
            exclusion_criteria_documents +
            trial_rationale_documents
        )
        unique_documents = {}
        for doc in combined_documents:
            nctId = doc["nctId"]
            if nctId not in unique_documents or doc["similarity_score"] > unique_documents[nctId]["similarity_score"]:
                unique_documents[nctId] = doc

        final_response.update({
            "success": True,
            "message": "Successfully fetched similar documents extended.",
            "data": list(unique_documents.values())
        })
        return final_response

    except Exception as e:
        final_response["message"] += f" {e}"
        return final_response
