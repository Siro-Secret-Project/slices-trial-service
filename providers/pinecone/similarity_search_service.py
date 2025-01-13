import time
from pinecone import Pinecone, ServerlessSpec
from collections import defaultdict

PINECONE_API_KEY = "pcsk_3Jqu5B_M57uQKr7AMDnpwZ4L8H9p4iXYHdpkZMPnR3zatmSMci5kfRHskfaGVF3PMHcw6N"

# ------------------OpenAI----------------- #
# Name of vector index DB
openai_index_name = "similarity-search-service-1536"

pc = Pinecone(api_key=PINECONE_API_KEY)

existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

if openai_index_name not in existing_indexes:
    pc.create_index(
        name=openai_index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    while not pc.describe_index(openai_index_name).status["ready"]:
        time.sleep(1)

# Initialize the Pinecone Vector Store
openai_index = pc.Index(openai_index_name)

# ------------------BioBERT----------------- #
# Name of vector index DB
bert_index_name = "similarity-search-service-768"

pc = Pinecone(api_key=PINECONE_API_KEY)

existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

if bert_index_name not in existing_indexes:
    pc.create_index(
        name=bert_index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    while not pc.describe_index(bert_index_name).status["ready"]:
        time.sleep(1)

# Initialize the Pinecone Vector Store
bert_index = pc.Index(bert_index_name)

def query_pinecone_db(embedding: list, embedding_model: str) -> dict:
    final_response = {
        "success": False,
        "message": "failed to fetch documents",
        "data": None
    }
    try:
        # Query Pinecone and fetch similar documents
        if embedding_model == "OpenAI":
            result = openai_index.query(vector=embedding, top_k=30, include_metadata=True, include_values=True)
        elif embedding_model == "BioBert":
            result = bert_index.query(vector=embedding, top_k=30, include_metadata=True, include_values=True)
        else:
            final_response["message"] = "unknown embedding model"
            return final_response

        # Process the Response Results
        data = result

        # Prepare a dictionary to store NCT IDs with their related information
        nct_data = defaultdict(lambda: {'count': 0, 'max_score': 0, 'module_max_score': ''})

        # Process the data
        for match in data['matches']:
            nct_id = match['metadata']['nctId']
            module = match['metadata']['module']
            score = match['score']
            value = match['values']

            # Update the count
            nct_data[nct_id]['count'] += 1

            # Update the max score and corresponding module
            if score > nct_data[nct_id]['max_score']:
                nct_data[nct_id]['max_score'] = score
                nct_data[nct_id]['module_max_score'] = module
                nct_data[nct_id]['embeddings'] = value

        # Return the final response
        final_response['data'] = nct_data
        final_response['success'] = True
        final_response['message'] = "Successfully fetched documents"
        return final_response

    except Exception as e:
        print(f"Unexpected error while fetching Pinecone Documents: {e}")
        final_response["message"] = f"Unexpected error while fetching Pinecone Documents: {e}"
        return final_response

