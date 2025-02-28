import concurrent.futures
from collections import defaultdict
from agents.TrialEligibilityAgent import TrialEligibilityAgent
from providers.openai.generate_embeddings import azure_client
from database.document_retrieval.fetch_processed_trial_document_with_nct_id import fetch_processed_trial_document_with_nct_id
from database.document_retrieval.record_eligibility_criteria_job import record_eligibility_criteria_job
from database.document_retrieval.fetch_similar_trials_inputs_with_ecid import fetch_similar_trials_inputs_with_ecid
from document_retrieval.utils.categorize_eligibility_criteria import categorize_eligibility_criteria
from utils.generate_object_id import generate_object_id
from database.document_retrieval.store_notification_data import store_notification_data
from database.document_retrieval.update_workflow_status import update_workflow_status
from document_retrieval.utils.categorize_generated_criteria import categorize_generated_criteria
from document_retrieval.utils.merge_duplicate_values import merge_duplicate_values, normalize_bmi_ranges


async def generate_trial_eligibility_criteria(ecid: str, trail_documents_ids: list) -> dict:
    """
    Generate trial eligibility criteria in batches of 2 documents.
    """
    final_response = {
        "success": False,
        "message": "",
        "data": None
    }

    try:
        # Fetch User Inputs from DB
        similar_trials_input_response = fetch_similar_trials_inputs_with_ecid(ecid=ecid)
        if similar_trials_input_response["success"] is False:
            final_response["message"] = similar_trials_input_response["message"]
            return final_response

        user_inputs = similar_trials_input_response["data"]["userInput"]
        inclusion_criteria = user_inputs.get("inclusionCriteria", "No inclusion criteria provided")
        exclusion_criteria = user_inputs.get("exclusionCriteria", "No exclusion criteria provided")

        trial_documents = similar_trials_input_response["data"]["similarTrials"]

        # Process and prepare similar trial documents
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
                        "primaryOutcomes": doc["primaryOutcomes"]
                    }
                })

        # Sort documents by similarity score
        similar_documents.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Initialize the TrialEligibilityAgent
        eligibility_agent = TrialEligibilityAgent(azure_client, max_tokens=4000)

        print("Started generating criteria")
        # Initialize lists to store generated criteria
        generated_inclusion_criteria = []
        generated_exclusion_criteria = []
        drug_ranges = []
        time_line = []

        # Function to process a batch
        def process_batch(batch):
            response = eligibility_agent.draft_eligibility_criteria(
                sample_trial_rationale=user_inputs.get("rationale", "No rationale provided"),
                similar_trial_documents=batch,
                user_provided_inclusion_criteria=inclusion_criteria,
                user_provided_exclusion_criteria=exclusion_criteria,
                user_provided_trial_outcome=user_inputs.get("trialOutcomes", "No trial outcomes provided"),
                user_provided_trial_conditions=user_inputs.get("condition", "No trial conditions provided"),
                generated_inclusion_criteria=generated_inclusion_criteria,
                generated_exclusion_criteria=generated_exclusion_criteria
            )
            if not response["success"]:
                return {"error": response["message"]}

            return response["data"]

        # Process documents in batches of 1
        batches = [similar_documents[i] for i in range(0, len(similar_documents))]

        # Run batches in parallel (10 at a time)
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            future_to_batch = {executor.submit(process_batch, batch): batch for batch in batches}

            for future in concurrent.futures.as_completed(future_to_batch):
                result = future.result()
                if "error" in result:
                    final_response["message"] = result["error"]
                    break
                generated_inclusion_criteria.extend(result["inclusionCriteria"])
                generated_exclusion_criteria.extend(result["exclusionCriteria"])
                drug_ranges.extend(result["drugRanges"])
                time_line.extend(result["timeFrame"])
                print("Completed One batch")


        print("Finished generating criteria")

        # Assign unique IDs
        for item in generated_inclusion_criteria:
            item["criteriaID"] = f"cid_{generate_object_id()}"
        for item in generated_exclusion_criteria:
            item["criteriaID"] = f"cid_{generate_object_id()}"


        categorizedGeneratedData = categorize_generated_criteria(generated_inclusion_criteria=generated_inclusion_criteria,
                                                                 generated_exclusion_criteria=generated_exclusion_criteria)
        print("Categorized Generated Criteria")
        categorizedUserDataResponse = categorize_eligibility_criteria(eligibility_agent, inclusion_criteria, exclusion_criteria)
        if categorizedUserDataResponse["success"] is False:
            print(categorizedUserDataResponse["message"])
            categorizedUserData = {}
        else:
            categorizedUserData = categorizedUserDataResponse["data"]

        # Merge Duplicates Values
        drug_ranges = normalize_bmi_ranges(drug_ranges)
        drug_ranges = merge_duplicate_values(drug_ranges)
        time_line = merge_duplicate_values(time_line)

        # Initialize the default dictionary
        metrics_data = defaultdict(lambda: {"hba1c": [], "bmi": [], "timeline": []})

        for item in drug_ranges:
            value = item["value"].lower()
            if "hba1c" in value:
                metrics_data["key"]["hba1c"].append(item)  # Use a common key like "key"
            else:
                metrics_data["key"]["bmi"].append(item)

        for item in time_line:
            metrics_data["key"]["timeline"].append(item)

        # Store job in DB
        db_response = record_eligibility_criteria_job(ecid, categorizedGeneratedData, categorizedUserData, metrics_data["key"])
        notification_response = store_notification_data(ecid=ecid)
        workflow_status_response = update_workflow_status(ecid=ecid, step="similar-criteria")

        print(workflow_status_response["message"])
        print(notification_response["message"])
        final_response["message"] = db_response.get("message", "Successfully generated trial eligibility criteria.")

            # Prepare final response
        model_generated_eligibility_criteria = {
            "inclusionCriteria": [ item["criteria"] for item in generated_inclusion_criteria],
            "exclusionCriteria": [ item["criteria"] for item in generated_exclusion_criteria],
            "categorizedData": categorizedGeneratedData,
            "userCategorizedData": categorizedUserData,
            "metrics": metrics_data["key"]
        }

        final_response["data"] = model_generated_eligibility_criteria
        final_response["success"] = True
        return final_response

    except Exception as e:
        final_response['message'] = f"Failed to generate trial eligibility criteria. Error: {e}"
        return final_response