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