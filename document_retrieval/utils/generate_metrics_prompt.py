import random

def generate_nct_id():
    return f"NCT{random.randint(10000000, 99999999)}"

def categorize_criteria(sample_data):
    inclusion = []
    exclusion = []

    for item in sample_data:
        if item["key"].lower() == "pregnant" or "eGFR" in item["key"]:
            exclusion.append(item["statement"])
        else:
            inclusion.append(item["statement"])

    return "\n".join([f"{i+1}. {statement}" for i, statement in enumerate(inclusion)]), " ".join(exclusion)

def generate_output(sample_data, num_trials=2):
    trials = []
    nct_ids = [generate_nct_id() for _ in range(num_trials)]

    criteria_summary = {}
    for item in sample_data:
        key = item["key"]
        if key not in criteria_summary:
            criteria_summary[key] = []
        criteria_summary[key].append({"value": key, "count": num_trials, "source": nct_ids})

    for i in range(num_trials):
        inclusion, exclusion = categorize_criteria(sample_data)

        trials.append({
            "nctId": nct_ids[i],
            "inclusionCriteria": inclusion,
            "exclusionCriteria": exclusion
        })

    return {"trials": trials, "criteria_summary": criteria_summary}


def generate_metrics_prompt(values: list):

    # Create a base prompt
    drug_metrics_keys = [item["value"] for item in values]
    drug_metrics_keys = list(set(drug_metrics_keys))
    str_drug_metrics_keys = ", ".join(drug_metrics_keys)

    metrics_base_prompt = (
    f"""
    Given a list of Eligibility criteria for T2DM clinical trials, extract all unique {str_drug_metrics_keys} ranges/medical terms, 
    count their occurrences, and return the source document IDs where each criterion appears.
    ### Input Format:
    A list of dictionaries where:
      - "nctId" represents the unique study ID.
      - "inclusionCriteria"/"exclusionCriteria" contains text specifying {str_drug_metrics_keys} ranges/medical terms.

    ### Instructions:
      1. Extract all unique {str_drug_metrics_keys} ranges/medical terms.
      2. Normalize the ranges:
        - If a statement says "greater than 7.0", replace it with ">7.5".
        - If it says "less than 10.0", replace it with "<9.5".
      3. Count occurrences of each unique range.
      4. Track the source document IDs where each range appears.
      5. Return a structured JSON output.
    """
    )

    output = generate_output(values, num_trials=2)
    input_document = output["trials"]

    sample_input_prompt = (
        f"""
        ### Example Input:
          ```json
          {input_document}
      """
    )

    output_examples = []
    for metric, entries in output["criteria_summary"].items():
        for entry in entries:
            output_examples.append(entry)



    response = f"response:{output_examples}"

    sample_output_prompt = (
        f"""
        ### Expected Output:

        json_object:
        {response}
        """
    )

    return metrics_base_prompt + sample_input_prompt + sample_output_prompt

