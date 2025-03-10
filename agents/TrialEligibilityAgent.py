import re
import json
from document_retrieval.utils import prompts
from typing import Dict, List
from database.mongo_db_connection import MongoDBDAO
from document_retrieval.utils.generate_trial_eligibility_certeria.generate_metrics_prompt import generate_metrics_prompt
from providers.aws.aws_bedrock_connection import BedrockLlamaClient
from document_retrieval.models.routes_models import DraftEligibilityCriteria


class TrialEligibilityAgent:
    def __init__(self):
        """
        Initializes the TrialEligibilityAgent class.

        Parameters:
        """
        self.bedrock_client = BedrockLlamaClient()
        self.categorisation_role = prompts.categorisation_role
        self.pattern = r'timeFrame\s*-\s*(.*?)(?=measure|$)'
        self.json_pattern = r'\{[\s\S]*\}'
        self.medical_writer_agent_role = prompts.medical_writer_agent_role
        self.filter_role = prompts.filter_role
        self.response_format = "Generating Response"

    def categorise_eligibility_criteria(self, eligibility_criteria: Dict) -> Dict:
        """
        Categorizes comprehensive inclusion and exclusion criteria for a medical trial based on provided inputs.

        Args:
            eligibility_criteria (Dict): The eligibility criteria for the medical trial.

        Returns:
            Dict: A dictionary containing:
                - success (bool): Indicates if the process was successful.
                - message (str): A descriptive message about the process outcome.
                - data (Dict): A dictionary containing:
                    - inclusionCriteria (List): Categorized inclusion criteria.
                    - exclusionCriteria (List): Categorized exclusion criteria.
        """
        # Initialize the final response structure
        final_response = {
            "success": False,
            "message": "Failed to categorize eligibility criteria",
            "data": None
        }

        try:
            # Construct the user input message for the categorisation agent
            user_input = f"Medical Trial Eligibility Criteria: {eligibility_criteria}"

            # Categorize criteria using the AI model
            inclusion_criteria, exclusion_criteria = self._generate_criteria_with_ai(user_input=user_input,
                                                                                     system_prompt=self.categorisation_role)

            # Prepare the final data structure
            final_data = {
                "inclusionCriteria": inclusion_criteria,
                "exclusionCriteria": exclusion_criteria
            }

            # Update the final response
            final_response["data"] = final_data
            final_response["success"] = True
            final_response["message"] = "Successfully categorized eligibility criteria"

        except Exception as e:
            # Handle any unexpected errors
            final_response["message"] = f"Error processing eligibility criteria: {e}"

        return final_response


    def filter_generated_criteria(self, inclusionCriteria: List[str], exclusionCriteria: List[str]) -> dict:
        """
        Filters the generated inclusion and exclusion criteria using an AI model.

        This method sends the provided inclusion and exclusion criteria to an AI model
        for filtering and returns the filtered results in a structured format.

        Args:
            inclusionCriteria (List[str]): A list of generated inclusion criteria to be filtered.
            exclusionCriteria (List[str]): A list of generated exclusion criteria to be filtered.

        Returns:
            dict: A dictionary containing:
                - success (bool): Indicates whether the filtering process was successful.
                - message (str): A descriptive message about the process outcome.
                - data (dict): The filtered criteria returned by the AI model.
        """
        # Initialize the final response structure
        final_response = {
            "success": False,
            "message": "Failed to filter eligibility criteria",
            "data": None
        }

        try:
            # Construct the user input message for the AI model
            user_input = (
                f"Inclusion Criteria: {inclusionCriteria}\n"
                f"Exclusion Criteria: {exclusionCriteria}\n"
            )

            # Prepare the user input
            processed_input = f"""### Now, Filter eligibility criteria from the following input:{user_input}"""
            model_input_prompt = self.filter_role + processed_input

            # Send the request to the AI model and get the response
            filter_response = self.bedrock_client.generate_text_llama(prompt=model_input_prompt,
                                                                      max_gen_len=2000)

            if filter_response["success"] is False:
                final_response["message"] = filter_response["message"]
                return filter_response

            # Parse the JSON response
            match = re.search(self.json_pattern, filter_response["data"])
            if match:
                json_str = match.group(0)
                response_json = json.loads(json_str)

                # Extract inclusion and exclusion criteria from the response
                inclusion_criteria = response_json.get("inclusionCriteria", [])
                exclusion_criteria = response_json.get("exclusionCriteria", [])

            else:
                inclusion_criteria = []
                exclusion_criteria = []

            # Prepare Response
            json_response = {
                "inclusionCriteria": inclusion_criteria,
                "exclusionCriteria": exclusion_criteria
            }
            print(json_response)

            # Update the final response with the filtered data
            final_response["data"] = json_response
            final_response["success"] = True
            final_response["message"] = "Successfully filtered eligibility criteria"

            return final_response

        except Exception as e:
            # Handle any unexpected errors during the filtering process
            final_response["message"] = f"Error filtering criteria: {e}"
            return final_response


    def draft_eligibility_criteria(self, draft_criteria: DraftEligibilityCriteria) -> Dict:
        """
        Drafts comprehensive inclusion and exclusion criteria for a medical trial based on provided inputs.

        Args:
            draft_criteria(DraftEligibilityCriteria): The draft criteria inputs

        Returns:
            Dict: A dictionary containing:
                - success (bool): Indicates if the process was successful.
                - message (str): A descriptive message about the process outcome.
                - data (Dict): A dictionary containing:
                    - inclusionCriteria (List): Extracted inclusion criteria.
                    - exclusionCriteria (List): Extracted exclusion criteria.
                    - timeFrame (List): Extracted time frame metrics.
                    - drugRanges (List): Extracted drug range metrics.
        """
        # Initialize the final response structure
        final_data = {
            "inclusionCriteria": [],
            "exclusionCriteria": [],
            "timeFrame": [],
            "drugRanges": []
        }
        final_response = {
            "success": False,
            "message": "Failed to draft eligibility criteria",
            "data": final_data
        }

        try:
            # Construct the user input message for the medical writer agent
            user_input = self._construct_user_input(draft_criteria=draft_criteria)

            # Generate criteria using the AI model
            inclusion_criteria, exclusion_criteria = self._generate_criteria_with_ai(user_input,
                                                                                     self.medical_writer_agent_role)

            # Extract additional metrics from similar trial documents
            drug_metrics = self._extract_drug_metrics(draft_criteria.similar_trial_documents)
            timeframe_metrics = self._extract_timeframe_metrics(draft_criteria.similar_trial_documents)

            # Prepare the final data structure
            final_data = self._prepare_final_data(inclusion_criteria, exclusion_criteria, timeframe_metrics,
                                                  drug_metrics, draft_criteria.similar_trial_documents)

            # Update the final response
            final_response["data"] = final_data
            final_response["success"] = True
            final_response["message"] = "Successfully drafted eligibility criteria"

        except Exception as e:
            # Handle any unexpected errors
            final_response["message"] = f"Error processing query rationale: {e}"

        return final_response

    def _construct_user_input(self, draft_criteria: DraftEligibilityCriteria) -> str:
        """
        Constructs the user input message for the medical writer agent.

        Args:
            draft_criteria(DraftEligibilityCriteria): The draft criteria inputs

        Returns:
            str: The constructed user input message.
        """
        print("Constructing user input")
        print(self.response_format)
        return f"""
            Medical Trial Rationale: {draft_criteria.sample_trial_rationale}
            Similar/Existing Medical Trial Document: {draft_criteria.similar_trial_documents}
            User Provided Inclusion Criteria: {draft_criteria.user_provided_inclusion_criteria}
            User Provided Exclusion Criteria: {draft_criteria.user_provided_exclusion_criteria}
            Trial Conditions: {draft_criteria.user_provided_trial_conditions}
            Trial Outcomes: {draft_criteria.user_provided_trial_outcome},
            Already Generated Inclusion Criteria: {draft_criteria.generated_inclusion_criteria},
            Already Exclusion Criteria: {draft_criteria.generated_exclusion_criteria}
        """

    def _generate_criteria_with_ai(self, user_input: str, system_prompt: str) -> tuple:
        """
        Generates inclusion and exclusion criteria using the AI model.

        Args:
            user_input (str): The constructed user input message.
            system_prompt (str): The system prompt.

        Returns:
            tuple: A tuple containing two lists:
                - inclusion_criteria (List): Generated inclusion criteria.
                - exclusion_criteria (List): Generated exclusion criteria.
        """
        response = None
        try:

          processed_input = f"""### Now, extract eligibility criteria from the following input:{user_input}"""
          model_input_prompt = system_prompt + processed_input

          # Send the request to the AI model
          response = self.bedrock_client.generate_text_llama(prompt=model_input_prompt, max_gen_len=2000)
          if response["success"] is False:
              print(response["message"])
              return [], []
          else:
              # Regex pattern to extract JSON
              match = re.search(self.json_pattern, response["data"])

              if match:
                  json_str = match.group(0)
                  response_json = json.loads(json_str)

                  # Extract inclusion and exclusion criteria from the response
                  inclusion_criteria = response_json.get("inclusionCriteria", [])
                  exclusion_criteria = response_json.get("exclusionCriteria", [])
                  print("Extracted criteria from draft criteria")

                  return inclusion_criteria, exclusion_criteria
              else:
                  return [], []
        except Exception as e:
            print(f"Error generating criteria with AI: {e}")
            print(response["data"])
            print("*"*100)
            return [], []


    def _extract_drug_metrics(self, similar_trial_documents: Dict) -> List:
        """
        Extracts drug metrics from similar trial documents.

        Args:
            similar_trial_documents (Dict): A similar document from a database.

        Returns:
            List: A list of extracted drug metrics.
        """
        metrics_response = None
        try:
            # Initialize MongoDBDAO
            mongo_dao = MongoDBDAO()

            # Query DB to fetch Prompt
            response = mongo_dao.find_one(collection_name="LOVs", query={"name": "metrics_prompt_data"})
            if response is None:
                return []
            else:
                values = response["values"]
            # Generate prompt
            system_prompt = generate_metrics_prompt(values=values)
            processed_input = (f"""### Now, extract metrics from the following input:{similar_trial_documents}. 
                                    Do not write any code. Just generate the required data in described format.""")
            model_input_prompt = system_prompt + processed_input

            # Generate the Response from LLama
            metrics_response = self.bedrock_client.generate_text_llama(prompt=model_input_prompt, max_gen_len=2000)

            # Extract JSON
            match = re.search(self.json_pattern, metrics_response["data"])

            if match:
                json_str = match.group(0)
                json_drug_metrics_output = json.loads(json_str)
                final_response = json_drug_metrics_output.get("response", [])
                print("Extracted Final response from Drug Metrics")
                return final_response
            else:
                return []
        except Exception as e:
            print(f"Error extracting drug metrics: {e}")
            print(metrics_response["data"])
            print("*"*100)
            return []

    def _extract_timeframe_metrics(self, similar_trial_documents: Dict) -> List:
        """
        Extracts timeframe metrics from similar trial documents.

        Args:
            similar_trial_documents (Dict): A similar document from a database.

        Returns:
            List: A list of extracted timeframe metrics.
        """
        timeline_response = None
        try:
            primary_outcomes = similar_trial_documents["document"]["primaryOutcomes"]
            primary_outcomes_timeline = self._extract_timeframes_and_text(primary_outcomes)
            time_line_output = [
                {
                    "nctId": similar_trial_documents["nctId"],
                    "timeLine": primary_outcomes_timeline
                }
            ]

            processed_input = f"""### Now, extract timeline data from the following input:{time_line_output}. 
                                Do not write any code. Just generate the required data in described format."""

            timeline_input_prompt = prompts.timeframe_count_prompt + processed_input

            timeline_response = self.bedrock_client.generate_text_llama(prompt=timeline_input_prompt, max_gen_len=2000)

            if timeline_response["success"] is False:
                print(timeline_response["message"])
                return []
            else:
                # Extract JSON
                match = re.search(self.json_pattern, timeline_response["data"])

                if match:
                    json_str = match.group(0)
                    json_timeframe_output = json.loads(json_str)
                    final_response = json_timeframe_output.get("response", [])
                    print("Extracted Final response from Timeframe")
                    return final_response
                else:
                    return []
        except Exception as e:
            print(f"Error extracting timeframe metrics: {e}")
            print(timeline_response["data"])
            print("*"*100)
            return []

    def _prepare_final_data(self, inclusion_criteria: List, exclusion_criteria: List,
                            timeframe_metrics: List, drug_metrics: List, similar_trial_documents: Dict) -> Dict:
        """
        Prepares the final data structure for the response.

        Args:
            inclusion_criteria (List): Generated inclusion criteria.
            exclusion_criteria (List): Generated exclusion criteria.
            timeframe_metrics (List): Extracted timeframe metrics.
            drug_metrics (List): Extracted drug metrics.
            similar_trial_documents (Dict): A similar document from a database.

        Returns:
            Dict: The final data structure containing all extracted and generated criteria.
        """
        print("Preparing final response...")
        print(self.response_format)

        # Add source information to inclusion and exclusion criteria
        for item in inclusion_criteria:
            source_statement = item["source"]
            item["source"] = {similar_trial_documents["nctId"]: source_statement}

        for item in exclusion_criteria:
            source_statement = item["source"]
            item["source"] = {similar_trial_documents["nctId"]: source_statement}

        return {
            "inclusionCriteria": inclusion_criteria,
            "exclusionCriteria": exclusion_criteria,
            "timeFrame": timeframe_metrics,
            "drugRanges": drug_metrics
        }

    def _extract_timeframes_and_text(self, text: str) -> list:
        """
            Extracts timeframes and text from primary outcomes.
            Args:
                text (str): A str of primary outcomes from the trial document.

            Returns:
                List: A list of extracted timeframes and text.
        """
        matches = re.findall(self.pattern, text, re.DOTALL)

        extracted_data = [match.strip() for match in matches]

        return extracted_data
