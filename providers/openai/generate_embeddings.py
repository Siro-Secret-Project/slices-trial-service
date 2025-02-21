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

def validate_document_similarity(similar_documents: list, document_search_criteria: dict) -> dict:
      base_response = {
          "success": False,
          "message": None,
          "data": None
      }
      try:
          validate_document_similarity_agent_role = (
                """
                    AI Assistant Role Prompt
                    
                    1. Goal:
                       You are an AI Assistant responsible for evaluating and assigning similarity scores to clinical trial documents 
                       based on their relevance to a given set of search criteria. Your task is to assess how closely each document 
                       aligns with the specified search parameters, including inclusion criteria, exclusion criteria, rationale, 
                       objectives, and outcomes.
                    
                       - **Strict Matching for Criteria:** If a document exactly matches a specified inclusion or exclusion criterion 
                         (e.g., the search requires HbA1c between 7-10, and the document states the same range), it should be 
                         considered a **100% match**.
                       - **Conflict Handling:** If a document contains criteria that **directly contradict** the search criteria 
                         (e.g., an excluded condition appears as an inclusion in the document), it should receive a **score of 0**, 
                         as opposing criteria take priority.
                       - **Relevancy-Based Scoring for Other Aspects:** For other sections such as rationale, objectives, and outcomes, 
                         scoring should be based on their general relevance rather than exact matching.
                    
                    2. Return Format:
                       Your response should be in the following structured JSON format:
                       json_object:
                       {
                           "response": {
                               "NCT_ID": similarity_score,
                               "NCT_ID": similarity_score,
                               "NCT_ID": similarity_score
                           },
                           "reasoning": {
                               "NCT_ID": "Explanation for the assigned score",
                               "NCT_ID": "Explanation for the assigned score",
                               "NCT_ID": "Explanation for the assigned score"
                           }
                       }
                """
          )

          user_input = (
                f"4. User Inputs: 1. Trail Inclusion Criteria: {document_search_criteria.get('inclusionCriteria', 'N/A')}, "
                f"2. Trail Exclusion Criteria: {document_search_criteria.get('exclusionCriteria', 'N/A')}, "
                f"3. Trail Rationale: {document_search_criteria.get('rationale', 'N/A')}, "
                f"4. Trail Objectives: {document_search_criteria.get('objective', 'N/A')}, "
                f"5. Trail Outcomes: {document_search_criteria.get('trialOutcomes', 'N/A')}"
                f"6. Similar Documents: {similar_documents}"

          )
          input_history = [
              {"role": "system", "content": validate_document_similarity_agent_role},
              {"role": "user", "content": user_input},
          ]
          response = azure_client.chat.completions.create(
              model="model-4o",
              response_format={"type": "json_object"},
              messages=input_history,
              max_tokens=3000,
              temperature=0.1,
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