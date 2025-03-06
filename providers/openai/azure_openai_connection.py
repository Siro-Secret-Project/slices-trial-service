import os
import json
import numpy as np
from openai import AzureOpenAI
from dotenv import load_dotenv


class AzureOpenAIClient:
    """
    A client for interacting with Azure OpenAI API.

    This class provides methods to generate responses using Azure OpenAI's chat models and create text embeddings.
    """

    def __init__(self, max_tokens: int = 4000, temperature: float = 0.1) -> None:
        """
        Initializes the AzureOpenAIClient with API credentials and default parameters.

        Args:
            max_tokens (int, optional): Maximum number of tokens to generate in a response. Defaults to 4000.
            temperature (float, optional): Controls randomness in responses. Defaults to 0.1.
        """
        load_dotenv()

        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "7219267fcc1345cabcd25ac868c686c1")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://stock-agent.openai.azure.com/")
        self.api_version = "2024-05-01-preview"

        self.max_tokens = max_tokens
        self.temperature = temperature

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )

    def generate_text(self, messages: list[dict], model: str = "model-4o", response_format: dict = None,
                      stream: bool = False) -> dict:
        """
        Generates a text response using Azure OpenAI's chat models.

        Args:
            messages (list[dict]): A list of dictionaries representing the conversation history.
            model (str, optional): The Azure OpenAI model to use for chat completion. Defaults to "model-4o".
            response_format (dict, optional): Specifies the desired response format. Defaults to None.
            stream (bool, optional): Whether to stream the response. Defaults to False.

        Returns:
            dict: A dictionary containing the API response, success status, and message.
        """
        final_response = {
            "success": False,
            "message": "Failed to generate text.",
            "data": None
        }
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                response_format=response_format if response_format else None,
                stream=stream,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            final_response.update({
                "success": True,
                "message": "Successfully generated text.",
                "data": response
            })
        except Exception as e:
            error_message = f"An error occurred while generating text: {e}"
            print(error_message)
            final_response["message"] = error_message

        return final_response

    def generate_embeddings(self, text: str, model: str = "embedding_model") -> dict:
        """
        Generates an embedding vector for the given text using Azure OpenAI's embedding model.

        Args:
            text (str): The input text to generate an embedding for.
            model (str, optional): The Azure OpenAI embedding model to use. Defaults to "embedding_model".

        Returns:
            dict: A dictionary containing the embedding vector, success status, and message.
        """
        final_response = {
            "success": False,
            "message": "Failed to generate embedding.",
            "data": None
        }
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=model
            )
            embeddings = np.array(json.loads(response.model_dump_json(indent=2))["data"][0]["embedding"]).reshape(1,
                                                                                                                  1536)

            final_response.update({
                "success": True,
                "message": "Successfully generated embedding.",
                "data": embeddings
            })
        except Exception as e:
            error_message = f"An error occurred while generating embeddings: {e}"
            print(error_message)
            final_response["message"] = error_message

        return final_response
