from providers.openai.generate_embeddings import validate_document_similarity
from providers.pinecone.similarity_search_service import query_pinecone_db_extended, pinecone_index
from providers.openai.generate_embeddings import azure_client
from database.document_retrieval.fetch_processed_trial_document_with_nct_id import t2dm_collection, fetch_processed_trial_document_with_nct_id
from document_retrieval.utils.fetch_trial_filters import fetch_trial_filters
from document_retrieval.utils.calculate_weighted_similarity_score import process_similarity_scores
from agents.TrialEligibilityAgent import TrialEligibilityAgent

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
                {"nctId": nctId, "similarity_score": score, "module": module} for nctId, score in validity_score.items() if score >= 85
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
        for item in trial_rationale_documents:
            item["module"] = "trialRationale"

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
            trial_documents = fetch_add_documents_filter_response["data"]
        else:
            trial_documents = list(unique_documents.values())

        # Calculate weighted average for similarity score
        # nctIds = [item["nctId"] for item in trial_documents]
        # weighted_similarity_scores_response = process_similarity_scores(target_documents_ids=nctIds,
        #                                                        user_input_document=documents_search_keys)
        # if weighted_similarity_scores_response["success"] is True:
        #     for item in weighted_similarity_scores_response["data"]:
        #         for subitem in trial_documents:
        #             if subitem["nctId"] == item["nctId"]:
        #                 subitem["weighted_similarity_score"] = item["weighted_similarity_score"]
        #         print("Calculated weighted_similarity_score")

        # Generate Eligibility Criteria

        eligibility_agent = TrialEligibilityAgent(azure_client,
                                                  max_tokens=300,
                                                  documents_collection=t2dm_collection,
                                                  pinecone_index=pinecone_index
                                                  )
        # Similar trial documents
        similar_documents = []
        for item in trial_documents:
            doc = fetch_processed_trial_document_with_nct_id(nct_id=item["nctId"])["data"]
            similarity_score = item["similarity_score"]
            similar_documents.append({"nctId": item["nctId"], "similarity_score": similarity_score, "document": doc})

        eligibility_criteria = eligibility_agent.draft_eligibility_criteria(sample_trial_rationale=documents_search_keys["rationale"],
                                                                            similar_trial_documents=similar_documents)
        # filtered_inclusion_criteria = eligibility_agent.filter_eligibility_criteria(eligibility_criteria["inclusionCriteria"],
        #                                                                             documents_search_keys["rationale"])
        # filtered_exclusion_criteria = eligibility_agent.filter_eligibility_criteria(eligibility_criteria["exclusionCriteria"],
        #                                                                 documents_search_keys["rationale"])
        model_generated_eligibility_criteria = {
            "inclusionCriteria": [item["criteria"] for item in eligibility_criteria["inclusionCriteria"]],
            "exclusionCriteria": [item["criteria"] for item in eligibility_criteria["exclusionCriteria"]],
        }

        # Sort trial based on score
        trial_documents = [item for item in trial_documents if item["similarity_score"] >= 90]
        trial_documents = sorted(trial_documents, key=lambda trial_item: trial_item["similarity_score"], reverse=True)

        final_response["data"] = trial_documents
        final_response["success"] = True
        final_response["message"] = "Successfully fetched similar documents extended."
        final_response["eligibilityCriteria"] = model_generated_eligibility_criteria
        return final_response

    except Exception as e:
        final_response["message"] += f" {e}"
        return final_response
