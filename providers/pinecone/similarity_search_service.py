import time
from pinecone import Pinecone, ServerlessSpec
from collections import defaultdict

PINECONE_API_KEY = "pcsk_5Pm2YN_LaNZs81DEwZtnWTrRGfMUrJgGphmu8tc7g93piQnUzCJYamDSpf9rebWYshfqz2"

# Name of vector index DB
index_name = "final-similarity-1"

pc = Pinecone(api_key=PINECONE_API_KEY)

existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    while not pc.describe_index(index_name).status["ready"]:
        time.sleep(1)

# Initialize the Pinecone Vector Store
index = pc.Index(index_name)

def query_pinecone_db(embedding: list, module: str = None) -> dict:
    final_response = {
        "success": False,
        "message": "failed to fetch documents",
        "data": None
    }
    try:
        # Query Pinecone and fetch similar documents
        if module is not None:
            result = index.query(vector=embedding,
                                 top_k=30,
                                 include_metadata=True,
                                 include_values=True,
                                 filter={
                                     "module": {"$eq": module},
                                 },
            )
        else:
            result = index.query(vector=embedding,
                                top_k=30,
                                include_metadata=True,
                                include_values=True,
            )

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

