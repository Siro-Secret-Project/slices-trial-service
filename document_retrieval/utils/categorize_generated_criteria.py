import json
from utils.generate_object_id import generate_object_id
from document_retrieval.utils.prompts import merge_prompt
from providers.openai.generate_embeddings import azure_client

criteria_categories = [
    "Age",
    "Gender",
    "Health Condition/Status",
    "Clinical and Laboratory Parameters",
    "Medication Status",
    "Informed Consent",
    "Ability to Comply with Study Procedures",
    "Lifestyle Requirements",
    "Reproductive Status",
    "Co-morbid Conditions",
    "Recent Participation in Other Clinical Trials",
    "Allergies and Drug Reactions",
    "Mental Health Disorders",
    "Infectious Diseases",
    "Other"
]


def categorize_generated_criteria(generated_inclusion_criteria, generated_exclusion_criteria):
    """
    Processes inclusion and exclusion criteria, merges similar criteria, updates source mappings,
    and assigns new object IDs.

    Args:
        generated_inclusion_criteria (list): List of dictionaries containing inclusion criteria.
        generated_exclusion_criteria (list): List of dictionaries containing exclusion criteria.

    Returns:
        dict: Categorized data with merged inclusion and exclusion criteria.
    """
    categorized_data = {}

    for criteria_category in criteria_categories:
        # Process Inclusion Criteria
        inclusion_temp = [item for item in generated_inclusion_criteria if item["class"] == criteria_category]

        if inclusion_temp:
            messages = [
                {"role": "system", "content": merge_prompt},
                {"role": "user", "content": json.dumps(inclusion_temp)}
            ]

            response = azure_client.chat.completions.create(
                model="model-4o",
                response_format={"type": "json_object"},
                messages=messages,
                stream=False,
                max_tokens=4000,
                temperature=0,
            )

            merged_inclusion_response = json.loads(response.choices[0].message.content)["response"]

            # Initialize the final merged inclusion response with source dictionary
            for res in merged_inclusion_response:
                res["source"] = {}

                for criteria_id in res["criteriaID"]:
                    for entry in inclusion_temp:
                        if entry["criteriaID"] == criteria_id:
                            res["source"].update(entry["source"])

            # Assign new object IDs
            for res in merged_inclusion_response:
                res["criteriaID"] = generate_object_id()

            categorized_data.setdefault(criteria_category, {"Inclusion": [], "Exclusion": []})["Inclusion"].extend(merged_inclusion_response)

        # Process Exclusion Criteria
        exclusion_temp = [item for item in generated_exclusion_criteria if item["class"] == criteria_category]

        if exclusion_temp:
            messages = [
                {"role": "system", "content": merge_prompt},
                {"role": "user", "content": json.dumps(exclusion_temp)}
            ]

            response = azure_client.chat.completions.create(
                model="model-4o",
                response_format={"type": "json_object"},
                messages=messages,
                stream=False,
                max_tokens=4000,
                temperature=0,
            )

            merged_exclusion_response = json.loads(response.choices[0].message.content)["response"]

            # Initialize the final merged exclusion response with source dictionary
            for res in merged_exclusion_response:
                res["source"] = {}

                for criteria_id in res["criteriaID"]:
                    for entry in exclusion_temp:
                        if entry["criteriaID"] == criteria_id:
                            res["source"].update(entry["source"])

            # Assign new object IDs
            for res in merged_exclusion_response:
                res["criteriaID"] = generate_object_id()

            categorized_data.setdefault(criteria_category, {"Inclusion": [], "Exclusion": []})["Exclusion"].extend(merged_exclusion_response)

    return categorized_data
