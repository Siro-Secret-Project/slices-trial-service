#from providers.openai.generate_embeddings import validate_document_similarity
from providers.pinecone.similarity_search_service import query_pinecone_db_extended

def process_criteria(criteria: str, document_search_data: dict, module: str = None) -> list:
    """
    Process a single search criteria, query the Pinecone DB, validate documents,
    and return a list of documents with high similarity scores.
    """
    if not criteria:
        return []
    print(f"Pinecone DB Started")
    pinecone_response = query_pinecone_db_extended(query=criteria, module=module)
    print(f"Pinecone DB Finished")

    # document_validation = validate_document_similarity(
    #     similar_documents=pinecone_response["data"],
    #     document_search_criteria=document_search_data
    # )
    # validity_score = document_validation["data"]["response"]

    # generate a final data list
    final_list = []
    for item in pinecone_response["data"]:
        new_item = {
            "nctId": item["nctId"],
            "module": item["module"],
            "similarity_score": item["similarity_score"],
        }
        final_list.append(new_item)

    return final_list

