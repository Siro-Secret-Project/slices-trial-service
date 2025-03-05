import concurrent.futures
from database.mongo_db_connection import MongoDBDAO
from typing import Dict, List, Any
from agents.TrialEligibilityAgent import TrialEligibilityAgent
from providers.openai.openai_connection import OpenAIClient
from database.document_retrieval.fetch_processed_trial_document_with_nct_id import fetch_processed_trial_document_with_nct_id
from database.document_retrieval.record_eligibility_criteria_job import record_eligibility_criteria_job
from database.document_retrieval.fetch_similar_trials_inputs_with_ecid import fetch_similar_trials_inputs_with_ecid
from document_retrieval.utils.categorize_eligibility_criteria import categorize_eligibility_criteria
from utils.generate_object_id import generate_object_id
from database.document_retrieval.store_notification_data import store_notification_data
from database.document_retrieval.update_workflow_status import update_workflow_status
from document_retrieval.utils.categorize_generated_criteria import categorize_generated_criteria
from document_retrieval.utils.merge_duplicate_values import merge_duplicate_values, normalize_bmi_ranges


def fetch_user_inputs(ecid: str) -> Dict[str, Any]:
    """Fetch user inputs from the database."""
    response = fetch_similar_trials_inputs_with_ecid(ecid=ecid)
    if not response["success"]:
        raise ValueError(response["message"])
    return response["data"]


def prepare_similar_documents(trial_documents: List[Dict[str, Any]], trail_documents_ids: List[str]) -> List[Dict[str, Any]]:
    """Prepare and sort similar trial documents."""
    similar_documents = []
    for item in trial_documents:
        nct_id = item["nctId"]
        if nct_id in trail_documents_ids:
            similarity_score = item["similarity_score"]
            doc = fetch_processed_trial_document_with_nct_id(nct_id=nct_id)["data"]
            similar_documents.append({
                "nctId": nct_id,
                "similarity_score": similarity_score,
                "document": {
                    "title": doc["officialTitle"],
                    "inclusionCriteria": doc["inclusionCriteria"],
                    "exclusionCriteria": doc["exclusionCriteria"],
                    "primaryOutcomes": doc["primaryOutcomes"],
                    "secondaryOutcomes": doc["secondaryOutcomes"],
                    "interventions": doc["interventions"]
                }
            })
    similar_documents.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similar_documents


def process_batch(batch: Dict[str, Any], eligibility_agent: TrialEligibilityAgent, user_inputs: Dict[str, Any],
                 generated_inclusion_criteria: List[Any], generated_exclusion_criteria: List[Any]) -> Dict[str, Any]:
    """Process a batch of similar trial documents."""
    response = eligibility_agent.draft_eligibility_criteria(
        sample_trial_rationale=user_inputs.get("rationale", "No rationale provided"),
        similar_trial_documents=batch,
        user_provided_inclusion_criteria=user_inputs.get("inclusionCriteria", "No inclusion criteria provided"),
        user_provided_exclusion_criteria=user_inputs.get("exclusionCriteria", "No exclusion criteria provided"),
        user_provided_trial_outcome=user_inputs.get("trialOutcomes", "No trial outcomes provided"),
        user_provided_trial_conditions=user_inputs.get("condition", "No trial conditions provided"),
        generated_inclusion_criteria=generated_inclusion_criteria,
        generated_exclusion_criteria=generated_exclusion_criteria
    )
    if not response["success"]:
        return {"error": response["message"]}
    return response["data"]


def assign_unique_ids(criteria_list: List[Dict[str, Any]]) -> None:
    """Assign unique IDs to criteria items."""
    for item in criteria_list:
        item["criteriaID"] = f"cid_{generate_object_id()}"


def categorize_and_merge_data(generated_inclusion_criteria: List[Dict[str, Any]],
                             generated_exclusion_criteria: List[Dict[str, Any]],
                             drug_ranges: List[Dict[str, Any]], time_line: List[Dict[str, Any]],
                             eligibility_agent: TrialEligibilityAgent, inclusion_criteria: str, exclusion_criteria: str) -> Dict[str, Any]:
    """Categorize and merge generated and user data."""
    categorized_generated_data = categorize_generated_criteria(
        generated_inclusion_criteria=generated_inclusion_criteria,
        generated_exclusion_criteria=generated_exclusion_criteria
    )
    categorized_user_data_response = categorize_eligibility_criteria(eligibility_agent, inclusion_criteria, exclusion_criteria)
    categorized_user_data = categorized_user_data_response["data"] if categorized_user_data_response["success"] else {}

    drug_ranges = normalize_bmi_ranges(drug_ranges)
    drug_ranges = merge_duplicate_values(drug_ranges)
    time_line = merge_duplicate_values(time_line)

    metrics_data = {"timeline":[]}

    # Initialize MongoDBDAO
    mongo_dao = MongoDBDAO()

    # Query DB to fetch Prompt
    response = mongo_dao.find_one(collection_name="LOVs", query={"name": "metrics_prompt_data"})
    if response is None:
        return {}
    else:
        values = response["values"]

    keys = [item["value"].lower() for item in values]

    # Initialize metrics_data dynamically based on keys
    metrics_data = {"timeline": []}
    for key in keys:
        metrics_data[key] = []

    # Categorize drug ranges dynamically
    for item in drug_ranges:
        value = item["value"].lower()
        for key in keys:  # Check if any key is present in value
            if key in value:
                metrics_data[key].append(item)
                break  # Avoid duplicate assignments
    for item in time_line:
        metrics_data["timeline"].append(item)

    return {
        "categorized_generated_data": categorized_generated_data,
        "categorized_user_data": categorized_user_data,
        "metrics_data": metrics_data
    }


async def generate_trial_eligibility_criteria(ecid: str, trail_documents_ids: List[str]) -> Dict[str, Any]:
    """Generate trial eligibility criteria in batches of 2 documents."""
    final_response = {
        "success": False,
        "message": "",
        "data": None
    }

    try:
        user_inputs_data = fetch_user_inputs(ecid)
        user_inputs = user_inputs_data["userInput"]
        trial_documents = user_inputs_data["similarTrials"]

        similar_documents = prepare_similar_documents(trial_documents, trail_documents_ids)

        openai_client = OpenAIClient()
        eligibility_agent = TrialEligibilityAgent(openai_client, response_format={"type": "json_object"})

        generated_inclusion_criteria = []
        generated_exclusion_criteria = []
        drug_ranges = []
        time_line = []

        batches = [similar_documents[i] for i in range(0, len(similar_documents))]

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_to_batch = {executor.submit(process_batch, batch, eligibility_agent, user_inputs, generated_inclusion_criteria, generated_exclusion_criteria): batch for batch in batches}

            for future in concurrent.futures.as_completed(future_to_batch):
                result = future.result()
                if "error" in result:
                    final_response["message"] = result["error"]
                    break
                generated_inclusion_criteria.extend(result["inclusionCriteria"])
                generated_exclusion_criteria.extend(result["exclusionCriteria"])
                drug_ranges.extend(result["drugRanges"])
                time_line.extend(result["timeFrame"])

        assign_unique_ids(generated_inclusion_criteria)
        assign_unique_ids(generated_exclusion_criteria)

        categorized_data = categorize_and_merge_data(
            generated_inclusion_criteria, generated_exclusion_criteria, drug_ranges, time_line,
            eligibility_agent, user_inputs.get("inclusionCriteria", "No inclusion criteria provided"),
            user_inputs.get("exclusionCriteria", "No exclusion criteria provided")
        )

        db_response = record_eligibility_criteria_job(ecid, categorized_data["categorized_generated_data"], categorized_data["categorized_user_data"], categorized_data["metrics_data"])
        store_notification_data(ecid=ecid)
        update_workflow_status(ecid=ecid, step="similar-criteria")

        final_response["data"] = {
            "inclusionCriteria": [item["criteria"] for item in generated_inclusion_criteria],
            "exclusionCriteria": [item["criteria"] for item in generated_exclusion_criteria],
            "categorizedData": categorized_data["categorized_generated_data"],
            "userCategorizedData": categorized_data["categorized_user_data"],
            "metrics": categorized_data["metrics_data"]
        }
        final_response["success"] = True
        final_response["message"] = db_response.get("message", "Successfully generated trial eligibility criteria.")

    except Exception as e:
        final_response['message'] = f"Failed to generate trial eligibility criteria. Error: {e}"

    return final_response