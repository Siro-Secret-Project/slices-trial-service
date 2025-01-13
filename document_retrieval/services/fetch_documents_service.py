from providers.openai.generate_embeddings import generate_embeddings_from_azure_client
from providers.pinecone.similarity_search_service import query_pinecone_db
from providers.bio_bert.generate_embdedings_bio_bert import generated_aggregated_embeddings

async def fetch_documents_service(query: str, similarity_threshold: int, embedding_model: str) -> dict:
  final_response = {
    "success": False,
    "message": "Failed to fetch documents openai service",
    "data": None

  }
  try:
    # generate embeddings for query
    if embedding_model == "OpenAI":
      input_query_embedding_response = generate_embeddings_from_azure_client(query)
    elif embedding_model == "BioBert":
      input_query_embedding_response = generated_aggregated_embeddings(query)
    else:
      final_response["success"] = False
      final_response["message"] = "Unknown embedding model"
      return final_response

    if input_query_embedding_response["success"] is False:
      final_response["message"] = input_query_embedding_response["message"]
      return final_response
    input_query_embedding = input_query_embedding_response["data"]


    # Query Pinecone DB
    pinecone_response = query_pinecone_db(input_query_embedding.tolist(),
                                          embedding_model=embedding_model)

    if pinecone_response["success"] is False:
      final_response["message"] = pinecone_response["message"]
      return final_response

    similar_documents = pinecone_response["data"]

    # Compute Required results
    final_list = [{"NctId": key, "similarity_score": round(value["max_score"] * 100, 2)} for key, value in similar_documents.items()]
    final_response["success"] = True
    final_response["data"] = final_list
    final_response["message"] = f"Successfully fetched documents {embedding_model} service"
    return final_response
  except Exception as e:
    print(f"Failed to fetch documents openai service: {e}")
    final_response["message"] = f"Failed to fetch documents {embedding_model} service: {e}"
    return final_response