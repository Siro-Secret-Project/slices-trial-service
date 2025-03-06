import json
import re
from utils.generate_object_id import generate_object_id
from document_retrieval.utils.prompts import merge_prompt, llama_prompt
from providers.openai.azure_openai_connection import AzureOpenAIClient
import concurrent.futures
from providers.aws_bedrock.aws_bedrock_connection import BedrockLlamaClient


criteria_categories = [
    "Gender", "Health Condition/Status", "Clinical and Laboratory Parameters",
    "Medication Status", "Informed Consent", "Ability to Comply with Study Procedures",
    "Lifestyle Requirements", "Reproductive Status", "Co-morbid Conditions",
    "Recent Participation in Other Clinical Trials", "Allergies and Drug Reactions",
    "Mental Health Disorders", "Infectious Diseases", "Other", "Age"
]


def _generate_tags(criteria_text):
    """
    Generates tags for the given criteria text using Bedrock Llama model.

    Args:
        criteria_text (str): The criteria text to extract tags from.

    Returns:
        list: A list of extracted tags.
    """
    bedrock_llama_client = BedrockLlamaClient()
    processed_input = f"""
      ### Now, extract tags from the following input:
      {criteria_text}
    """
    model_input_prompt = llama_prompt + processed_input
    response = bedrock_llama_client.generate_text_llama(model_input_prompt)

    if response["success"] is False:
        return []

    pattern = r'\{[\s\S]*\}'  # Regex pattern to extract JSON
    match = re.search(pattern, response["data"])
    if match:
        json_str = match.group(0)
        response_json = json.loads(json_str)
        return response_json.get("tags", [])

    return []


def _process_criteria(criteria_list, category):
    try:
        print(f"Processing criteria for {category}")
        filtered_criteria = [item for item in criteria_list if item["class"] == category]

        if not filtered_criteria:
            return []

        # If the filtered list is greater than 25, split it into two
        if len(filtered_criteria) > 25:
            mid = len(filtered_criteria) // 2
            first_half = filtered_criteria[:mid]
            second_half = filtered_criteria[mid:]

            return _process_criteria(first_half, category) + _process_criteria(second_half, category)

        print(f"Found {len(filtered_criteria)} criteria for {category}.")

        messages = [
            {"role": "system", "content": merge_prompt},
            {"role": "user", "content": json.dumps(filtered_criteria)}
        ]

        openai_client = AzureOpenAIClient()
        response = openai_client.generate_text(messages=messages, response_format={"type": "json_object"})
        try:
            merged_response = json.loads(response["data"].choices[0].message.content).get("response", [])
        except Exception as e:
            print(f"Failed to parse merged response:{category} {e}")
            return filtered_criteria

        for res in merged_response:
            res["source"] = {}
            for criteria_id in res["criteriaID"]:
                for entry in filtered_criteria:
                    if entry["criteriaID"] == criteria_id:
                        res["source"].update(entry["source"])
            res["criteriaID"] = generate_object_id()

            # Generate Tags
            res["tags"] = _generate_tags(res["criteria"])

        return merged_response
    except Exception as e:
        print(f"Error processing criteria {category}: {e}")
        return []


def categorize_generated_criteria(generated_inclusion_criteria, generated_exclusion_criteria):
    """
    Processes inclusion and exclusion criteria in parallel, merges similar criteria,
    updates source mappings, and assigns new object IDs.
    """
    categorized_data = {}

    # Use ThreadPoolExecutor for parallel processing
    # Change max_workers=len(criteria_categories)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit tasks for inclusion criteria
        inclusion_futures = {
            executor.submit(
                _process_criteria, generated_inclusion_criteria, criteria_category
            ): (criteria_category, "Inclusion")
            for criteria_category in criteria_categories
        }

        # Submit tasks for exclusion criteria
        exclusion_futures = {
            executor.submit(
                _process_criteria, generated_exclusion_criteria, criteria_category
            ): (criteria_category, "Exclusion")
            for criteria_category in criteria_categories
        }

        # Combine all futures
        all_futures = {**inclusion_futures, **exclusion_futures}

        # Process results as they complete
        for future in concurrent.futures.as_completed(all_futures):
            criteria_category, criteria_type = all_futures[future]
            try:
                result = future.result()
                categorized_data.setdefault(criteria_category, {"Inclusion": [], "Exclusion": []})
                categorized_data[criteria_category][criteria_type].extend(result)
            except Exception as e:
                print(f"Error processing {criteria_type} criteria for {criteria_category}: {e}")

    return categorized_data