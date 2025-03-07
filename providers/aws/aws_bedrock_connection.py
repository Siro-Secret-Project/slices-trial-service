import os
import boto3
import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError


class BedrockLlamaClient:
    """
    A client for interacting with AWS Bedrock Llama 3 model.

    This class provides methods to generate text responses using the Bedrock Runtime API.
    """

    def __init__(self) -> None:
        """
        Initializes the BedrockLlamaClient with AWS credentials and model parameters.
        """
        load_dotenv()

        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        region_name = os.getenv("MODEL_LLAMA_70B_REGION_NAME")
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        self.model_id = "us.meta.llama3-3-70b-instruct-v1:0"

    def generate_text_llama(self, prompt: str, max_gen_len: int = 512, temperature: float = 0.5) -> dict:
        """
        Generates a text response using Llama 3 via AWS Bedrock.

        Args:
            prompt (str): The input text prompt for the model.
            max_gen_len (int, optional): Maximum response length. Defaults to 512.
            temperature (float, optional): Controls randomness in responses. Defaults to 0.5.

        Returns:
            dict: A dictionary containing the API response, success status, and message.
        """
        formatted_prompt = f"""
        <|begin_of_text|><|start_header_id|>user<|end_header_id|>
        {prompt}
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """

        request_payload = json.dumps({
            "prompt": formatted_prompt,
            "max_gen_len": max_gen_len,
            "temperature": temperature,
        })

        final_response = {
            "success": False,
            "message": "Failed to generate text.",
            "data": None
        }

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=request_payload
            )

            model_response = json.loads(response["body"].read().decode("utf-8"))
            response_text = model_response.get("generation", "")

            final_response.update({
                "success": True,
                "message": "Successfully generated text.",
                "data": response_text
            })
        except (ClientError, Exception) as e:
            error_message = f"An error occurred while generating text: {e}"
            print(error_message)
            final_response["message"] = error_message

        return final_response
