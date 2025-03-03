import re
import json
from document_retrieval.utils import prompts
from typing import Dict, List
from database.mongo_db_connection import MongoDBDAO
from document_retrieval.utils.generate_metrics_prompt import generate_metrics_prompt


class TrialEligibilityAgent:
    def __init__(self, openai_client, response_format: dict):
        """
        Initializes the TrialEligibilityAgent class.

        Parameters:
            openai_client: The OpenAI client instance to communicate with the AI model.
            response_format: The format of the response from OpenAI.
        """
        self.openai_client = openai_client
        self.categorisation_role = prompts.categorisation_role
        self.pattern = r'timeFrame\s*-\s*(.*?)(?=measure|$)'
        self.medical_writer_agent_role = prompts.medical_writer_agent_role
        self.filter_role = prompts.filter_role
        self.response_format = response_format

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

            # Prepare the message list for the AI model
            message_list = [
                {"role": "system", "content": self.filter_role},  # System role defining the AI's function
                {"role": "user", "content": user_input}  # User input containing the criteria
            ]

            # Send the request to the AI model and get the response
            response = self.openai_client.generate_text(messages=message_list, response_format=self.response_format)

            # Parse the AI-generated JSON response
            json_response = json.loads(response["data"].choices[0].message.content)

            # Update the final response with the filtered data
            final_response["data"] = json_response
            final_response["success"] = True
            final_response["message"] = "Successfully filtered eligibility criteria"

            return final_response

        except Exception as e:
            # Handle any unexpected errors during the filtering process
            final_response["message"] = f"Error filtering criteria: {e}"
            return final_response


    def draft_eligibility_criteria(self, sample_trial_rationale: str, similar_trial_documents: Dict,
                                   user_provided_inclusion_criteria: str, user_provided_exclusion_criteria: str,
                                   user_provided_trial_conditions: str, user_provided_trial_outcome: str,
                                   generated_inclusion_criteria: List[str],
                                   generated_exclusion_criteria: List[str]) -> Dict:
        """
        Drafts comprehensive inclusion and exclusion criteria for a medical trial based on provided inputs.

        Args:
            sample_trial_rationale (str): The overall rationale for the medical trial.
            similar_trial_documents (Dict): A similar document from a database.
            user_provided_inclusion_criteria (str): The user-provided inclusion criteria.
            user_provided_exclusion_criteria (str): The user-provided exclusion criteria.
            user_provided_trial_conditions (str): The trial conditions as provided by the user.
            user_provided_trial_outcome (str): The expected outcome of the trial as provided by the user.
            generated_inclusion_criteria (List[str]): A list of generated inclusion criteria.
            generated_exclusion_criteria (List[str]): A list of generated exclusion criteria.

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
            user_input = self._construct_user_input(sample_trial_rationale, similar_trial_documents,
                                                    user_provided_inclusion_criteria, user_provided_exclusion_criteria,
                                                    user_provided_trial_conditions, user_provided_trial_outcome,
                                                    generated_inclusion_criteria, generated_exclusion_criteria)

            # Generate criteria using the AI model
            inclusion_criteria, exclusion_criteria = self._generate_criteria_with_ai(user_input,
                                                                                     self.medical_writer_agent_role)

            # Extract additional metrics from similar trial documents
            drug_metrics = self._extract_drug_metrics(similar_trial_documents)
            timeframe_metrics = self._extract_timeframe_metrics(similar_trial_documents)

            # Prepare the final data structure
            final_data = self._prepare_final_data(inclusion_criteria, exclusion_criteria, timeframe_metrics,
                                                  drug_metrics, similar_trial_documents)

            # Update the final response
            final_response["data"] = final_data
            final_response["success"] = True
            final_response["message"] = "Successfully drafted eligibility criteria"

        except Exception as e:
            # Handle any unexpected errors
            final_response["message"] = f"Error processing query rationale: {e}"

        return final_response

    def _construct_user_input(self, sample_trial_rationale: str, similar_trial_documents: Dict,
                              user_provided_inclusion_criteria: str, user_provided_exclusion_criteria: str,
                              user_provided_trial_conditions: str, user_provided_trial_outcome: str,
                              generated_inclusion_criteria: List[str], generated_exclusion_criteria: List[str]) -> str:
        """
        Constructs the user input message for the medical writer agent.

        Args:
            sample_trial_rationale (str): The overall rationale for the medical trial.
            similar_trial_documents (Dict): A similar document from a database.
            user_provided_inclusion_criteria (str): The user-provided inclusion criteria.
            user_provided_exclusion_criteria (str): The user-provided exclusion criteria.
            user_provided_trial_conditions (str): The trial conditions as provided by the user.
            user_provided_trial_outcome (str): The expected outcome of the trial as provided by the user.
            generated_inclusion_criteria (List[str]): A list of generated inclusion criteria.
            generated_exclusion_criteria (List[str]): A list of generated exclusion criteria.

        Returns:
            str: The constructed user input message.
        """
        print("Constructing user input")
        print(self.response_format)
        return f"""
            Medical Trial Rationale: {sample_trial_rationale}
            Similar/Existing Medical Trial Document: {similar_trial_documents}
            User Provided Inclusion Criteria: {user_provided_inclusion_criteria}
            User Provided Exclusion Criteria: {user_provided_exclusion_criteria}
            Trial Conditions: {user_provided_trial_conditions}
            Trial Outcomes: {user_provided_trial_outcome},
            Already Generated Inclusion Criteria: {generated_inclusion_criteria},
            Already Exclusion Criteria: {generated_exclusion_criteria}
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
        message_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        # Send the request to the AI model
        str_criteria_response = self.openai_client.generate_text(messages=message_list,
                                                                 response_format=self.response_format)
        json_criteria_response = json.loads(str_criteria_response["data"].choices[0].message.content)

        # Extract inclusion and exclusion criteria from the response
        inclusion_criteria = json_criteria_response.get("inclusionCriteria", [])
        exclusion_criteria = json_criteria_response.get("exclusionCriteria", [])

        return inclusion_criteria, exclusion_criteria

    def _extract_drug_metrics(self, similar_trial_documents: Dict) -> List:
        """
        Extracts drug metrics from similar trial documents.

        Args:
            similar_trial_documents (Dict): A similar document from a database.

        Returns:
            List: A list of extracted drug metrics.
        """

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

        message_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{similar_trial_documents}"}
        ]

        str_drug_metrics_response = self.openai_client.generate_text(messages=message_list,
                                                                     response_format=self.response_format)
        json_drug_metrics_output = json.loads(str_drug_metrics_response["data"].choices[0].message.content)
        return json_drug_metrics_output.get("response", [])

    def _extract_timeframe_metrics(self, similar_trial_documents: Dict) -> List:
        """
        Extracts timeframe metrics from similar trial documents.

        Args:
            similar_trial_documents (Dict): A similar document from a database.

        Returns:
            List: A list of extracted timeframe metrics.
        """
        primary_outcomes = similar_trial_documents["document"]["primaryOutcomes"]
        primary_outcomes_timeline = self._extract_timeframes_and_text(primary_outcomes)
        time_line_output = [
            {
                "nctId": similar_trial_documents["nctId"],
                "timeLine": primary_outcomes_timeline
            }
        ]

        messages = [
            {"role": "system", "content": prompts.timeframe_count_prompt},
            {"role": "user", "content": f"{time_line_output}"}
        ]

        str_timeframe_response = self.openai_client.generate_text(messages=messages,
                                                                  response_format=self.response_format)
        json_timeframe_output = json.loads(str_timeframe_response["data"].choices[0].message.content)
        return json_timeframe_output.get("response", [])

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
