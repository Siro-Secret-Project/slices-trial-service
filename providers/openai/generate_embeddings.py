import numpy as np
import os
import json
from openai import AzureOpenAI


# Set up environment variables
os.environ["AZURE_OPENAI_API_KEY"] = "7219267fcc1345cabcd25ac868c686c1"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://stock-agent.openai.azure.com/"
azure_client = AzureOpenAI(
  api_key = os.environ.get("AZURE_OPENAI_API_KEY"),
  api_version = "2024-05-01-preview",
  azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
)

def generate_embeddings_from_azure_client(text) -> dict:
  final_response = {
      "success": False,
      "message": "Failed to generate embeddings.",
      "data": None
  }
  try:
        response = azure_client.embeddings.create(
            input=text,
            model="embedding_model"
        )
        # Extract and flatten the embedding
        embedding = np.array(json.loads(response.model_dump_json(indent=2))["data"][0]["embedding"])
        final_response["success"] = True
        final_response["data"] = embedding.reshape(1, 1536)
        final_response["message"] = "Successfully generated embeddings."
        return final_response
  except Exception as e:
        print(f"Error generating embeddings: {e}")
        final_response["success"] = False
        final_response["message"] = f"Error generating embeddings: {e}"
        return final_response

def validate_document_similarity(query: str, similar_documents: list):
      base_response = {
          "success": False,
          "message": None,
          "data": None
      }
      try:
          validate_document_similarity_agent_role = (
              """
              You are an AI Assistant tasked with processing input queries and evaluating the similarity of documents 
              to those queries. 
              Your goal is to determine whether a document aligns with the input query and assign a similarity score 
              between 0 and 100 (integer format).

              Your data will pertain to medical trials, where the most critical factors for determining document 
              relevance are **lab values**, **age**, and **specific conditions that are considered in trial like BMI or 
              some drug**. 
              Common elements like informed consent should be ignored, as they are not significant for this task.

              Respond in the following format:
              json_object:
              {
                "response": {
                  "NCT_ID": similarity_score,
                  "NCT_ID": similarity_score,
                  "NCT_ID": similarity_score,
                  "NCT_ID": similarity_score
                }
              }

              Note: Each NCT_ID represents a unique document ID.

              """
          )
          input_history = [
              {"role": "system", "content": validate_document_similarity_agent_role},
              {"role": "user", "content": f"Trial Document: {query}, Similar Documents: {similar_documents}"},
          ]
          response = azure_client.chat.completions.create(
              model="model-4o",
              response_format={"type": "json_object"},
              messages=input_history,
              max_tokens=500,
              temperature=0.3,
          )
          response_message = response.choices[0].message.content
          base_response["success"] = True
          base_response["message"] = "Response Received Successfully"
          base_response["data"] = json.loads(response_message)
          return base_response
      except Exception as e:
          print(f"Error while extracting JSON Intent: {str(e)}")
          base_response["message"] = f"Error while extracting JSON Intent : {str(e)}"
          print(f"Final Response From Model: {base_response}")
          return base_response