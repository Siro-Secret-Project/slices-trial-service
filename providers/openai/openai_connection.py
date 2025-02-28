import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np


class OpenAIClient:
    """
    A client for interacting with the OpenAI API.

    This class provides methods to generate responses using OpenAI's chat models and create text embeddings.
    """

    def __init__(self, max_tokens: int = 4000, temperature: float = 0.1) -> None:
        """
        Initializes the OpenAIClient with API credentials and default parameters.

        Args:
            max_tokens (int, optional): Maximum number of tokens to generate in a response. Defaults to 4000.
            temperature (float, optional): Controls randomness in responses. Higher values (e.g., 1.0) produce more varied outputs,
                                          while lower values (e.g., 0.2) make it more deterministic. Defaults to 0.7.

        Raises:
            ValueError: If the OpenAI API key is not set in environment variables.
        """
        load_dotenv()

        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables.")

        openai.api_key = self.api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = OpenAI()

    def generate_text(self, messages: list[dict], model: str = "gpt-4o",
                      response_format: dict = None, stream: bool = False) -> dict:
        """
        Generates a text response using OpenAI's chat models.

        Args:
            messages (list[dict]): A list of dictionaries representing the conversation history.
                                   Each dictionary must contain `role` ("system", "user", or "assistant")
                                   and `content` (text string).
            model (str, optional): The OpenAI model to use for chat completion. Defaults to "gpt-4o".
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

    def generate_embeddings(self, text: str, model: str = "text-embedding-3-small") -> dict:
        """
        Generates an embedding vector for the given text using OpenAI's embedding model.

        Args:
            text (str): The input text to generate an embedding for.
            model (str, optional): The OpenAI embedding model to use. Defaults to "text-embedding-3-small".

        Returns:
            dict: A dictionary containing the embedding vector, success status, and message.
        """
        final_response = {
            "success": False,
            "message": "Failed to generate embedding.",
            "data": None
        }
        try:
            embedding_response = self.client.embeddings.create(input=[text], model=model)
            embeddings = np.array(embedding_response.data[0].embedding).reshape(1, -1)

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
