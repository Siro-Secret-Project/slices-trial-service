import os
import re
import json
import tempfile
from typing import Dict, Any
from dotenv import load_dotenv
from providers.aws.aws_s3_connection import AWSS3Client
from utils.generate_object_id import generate_object_id
from providers.openai.azure_openai_connection import AzureOpenAIClient


def validate_pdf(file) -> Dict[str, Any]:
    """Validates if the uploaded file is a PDF."""
    if file.content_type != "application/pdf":
        return {"success": False, "message": "Only PDF files are allowed."}
    return {"success": True}


def save_temp_file(file) -> str:
    """Saves the uploaded file to a temporary location."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file.file.read())
        return temp_file.name


def process_s3_upload(temp_file_path: str) -> Dict[str, Any]:
    """Uploads a file to S3 and returns the response."""
    s3_client = AWSS3Client()
    new_file_name = generate_object_id()
    return s3_client.upload_file_to_s3(file_path=temp_file_path, new_name=new_file_name)


def download_index_file() -> Dict[str, Any]:
    """Downloads the index file from S3."""
    s3_client = AWSS3Client()
    load_dotenv()
    index_file_path = "index.pdf"
    index_file_url = os.environ.get("PROTOCOL_INDEX_FILE_S3_URL")
    return s3_client.download_file_from_s3(s3_url=index_file_url, local_path=index_file_path)


def generate_mapping_prompt(index_keys: Dict[str, Any]) -> str:
    """Generates a prompt to map index keys to target keys."""
    target_keys = [
        "inclusionCriteria", "exclusionCriteria", "rationaleText", "safetyAssessment",
        "efficacyEndpoints", "startDate", "endDate", "sponsor", "sampleSizeMin", "sampleSizeMax",
        "studyDesign", "primaryObjective", "secondaryObjective", "primaryOutcomes",
        "secondaryOutcomes", "endpoints", "outcomeMeasures"
    ]
    index_json_str = json.dumps(index_keys, indent=4)
    return (
        f"""
        You are given an index object in JSON format as follows:
        {index_json_str}

        For each of the following target keys:
        {", ".join(target_keys)}

        Identify which keys from the index object match each target key.
        Match by checking if the target key appears as a substring in the index key (ignore case and whitespace differences).
        Output a JSON object where each target key maps to an array of matching index keys.
        If no index key is applicable for a target key, then the array should be empty.
        Return a JSON object only so that I can use it in my code later.
        """
    )


def get_index_mapping(index_keys: Dict[str, Any]) -> Dict[str, Any]:
    """Gets index mapping using AI-based key extraction."""
    client = AzureOpenAIClient()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": generate_mapping_prompt(index_keys)}
    ]
    ai_response = client.generate_text(messages=messages)
    if not ai_response["success"]:
        raise ValueError(ai_response["message"])
    json_str = re.sub(r"^```(?:json)?\s*|```$", "", ai_response["data"].choices[0].message.content.strip(),
                      flags=re.MULTILINE)
    return json.loads(json_str)


def map_sections_to_targets(sections: Dict[str, str], mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Maps extracted sections to target keys."""
    final_data = {}
    for target_key, index_keys_list in mapping.items():
        final_data[target_key] = [{idx_key: sections.get(idx_key, "")} for idx_key in index_keys_list]
    return final_data


