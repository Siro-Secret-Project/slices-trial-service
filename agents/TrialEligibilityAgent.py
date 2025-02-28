import re
import json
from document_retrieval.utils import prompts
from providers.openai.openai_connection import OpenAIClient


class TrialEligibilityAgent:
    def __init__(self, azure_client, model="model-4o", max_tokens=4000, temperature=0.2):
        """
        Initializes the TrialEligibilityAgent class.

        Parameters:
            azure_client: The Azure client instance to communicate with the AI model.
            model (str): The AI model to use for processing.
            max_tokens (int): The maximum number of tokens for the response.
            temperature (float): The randomness level for the response.
        """
        self.azure_client = azure_client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.categorisation_role = prompts.categorisation_role
        self.pattern = r'timeFrame\s*-\s*(.*?)(?=measure|$)'
        self.medical_writer_agent_role = prompts.medical_writer_agent_role
        self.filter_role = prompts.filter_role

    def draft_eligibility_criteria(self, sample_trial_rationale,
                                   similar_trial_documents,
                                   user_provided_inclusion_criteria,
                                   user_provided_exclusion_criteria,
                                   user_provided_trial_conditions,
                                   user_provided_trial_outcome,
                                   generated_inclusion_criteria,
                                   generated_exclusion_criteria, ):
        """
        Drafts comprehensive Inclusion and Exclusion Criteria for a medical trial based on provided inputs.

        Parameters:
            sample_trial_rationale (str): The overall rationale for the medical trial.
            similar_trial_documents (dict): A similar document from a database.
            user_provided_inclusion_criteria (str): The user-provided inclusion criteria.
            user_provided_exclusion_criteria (str): The user-provided exclusion criteria.
            user_provided_trial_conditions (str): The trial conditions as provided by the user.
            user_provided_trial_outcome (str): The expected outcome of the trial as provided by the user.
            generated_exclusion_criteria (list): A list of generated exclusion criteria.
            generated_inclusion_criteria (list): A list of generated inclusion criteria.

        Returns:
            dict: A dictionary containing:
                - success (bool): Indicates if the process was successful.
                - message (str): A descriptive message about the process outcome.
                - data (dict): A dictionary containing:
                    - inclusionCriteria (list): Extracted inclusion criteria.
                    - exclusionCriteria (list): Extracted exclusion criteria.
        """
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
            inclusion_criteria = []
            exclusion_criteria = []

            # Constructing the user input message for the medical writer agent
            user_input = f"""
                Medical Trial Rationale: {sample_trial_rationale}
                Similar/Existing Medical Trial Document: {similar_trial_documents}
                User Provided Inclusion Criteria: {user_provided_inclusion_criteria}
                User Provided Exclusion Criteria: {user_provided_exclusion_criteria}
                Trial Conditions: {user_provided_trial_conditions}
                Trial Outcomes: {user_provided_trial_outcome},
                Already Generated Inclusion Criteria: {generated_inclusion_criteria},
                Already Exclusion Criteria: {generated_exclusion_criteria}
            """

            # Creating a message list for the Azure AI model
            message_list = [
                {"role": "system", "content": self.medical_writer_agent_role},  # System role defining AI's function
                {"role": "user", "content": user_input}  # User input including trial details
            ]

            try:
                openai_client = OpenAIClient()
                response_format = {"type": "json_object"}

                # Sending the request to Azure AI chat model
                response = openai_client.generate_text(messages=message_list, response_format=response_format)

                # Parsing the AI-generated JSON response
                json_response = json.loads(response["data"].choices[0].message.content)

                # Extracting inclusion and exclusion criteria from the response
                inclusion_criteria.extend(json_response.get("inclusionCriteria", []))
                exclusion_criteria.extend(json_response.get("exclusionCriteria", []))

                # Extract Metrics
                message_list = [
                    {"role": "system", "content": prompts.values_count_prompt},
                    {"role": "user", "content": f"{similar_trial_documents}"}
                ]

                metrics_response = openai_client.generate_text(messages=message_list, response_format=response_format)


                drug_output = json.loads(metrics_response["data"].choices[0].message.content)

                primary_outcomes = similar_trial_documents["document"]["primaryOutcomes"]
                timeline = self.extract_timeframes_and_text(primary_outcomes)
                time_line_output = [
                    {
                        "nctId": similar_trial_documents["nctId"],
                        "timeLine": timeline
                    }
                ]
                messages = [
                    {"role": "system", "content": prompts.timeframe_count_prompt},
                    {"role": "user", "content": f"{time_line_output}"}
                ]

                timeframe_response = openai_client.generate_text(messages=messages, response_format=response_format)
                timeframe_output = json.loads(timeframe_response["data"].choices[0].message.content)

                # Preparing final response data
                for item in inclusion_criteria:
                    source_statement = item["source"]
                    item["source"] = {
                        similar_trial_documents["nctId"]: source_statement
                    }
                for item in exclusion_criteria:
                    source_statement = item["source"]
                    item["source"] = {
                        similar_trial_documents["nctId"]: source_statement
                    }

                final_data = {
                    "inclusionCriteria": inclusion_criteria,
                    "exclusionCriteria": exclusion_criteria,
                    "timeFrame": timeframe_output["response"],
                    "drugRanges": drug_output["response"]
                }

            except Exception as e:
                print(f"Error processing AI response: {e}")  # Logging error in AI response processing

            final_response["data"] = final_data
            final_response["success"] = True
            final_response["message"] = "Successfully drafted eligibility criteria"
            return final_response

        except Exception as e:
            # Handling any unexpected errors
            final_response["message"] = f"Error processing query rationale: {e}"
            return final_response

    def categorise_eligibility_criteria(self, eligibility_criteria):
        """
        Categorise comprehensive Inclusion and Exclusion Criteria for a medical trial based on provided inputs.

        Parameters:
            eligibility_criteria: Eligibility criteria for medical trial.

        Returns:
            dict: A dictionary containing inclusion and exclusion criteria.
        """
        final_response = {
            "success": False,
            "message": "failed to draft eligibility criteria",
            "data": None
        }
        try:
            inclusion_criteria = []
            exclusion_criteria = []

            user_input = f"""
                Medical Trial Eligibility Criteria: {eligibility_criteria}
            """

            message_list = [
                {"role": "system", "content": self.categorisation_role},
                {"role": "user", "content": user_input}
            ]

            try:
                openai_client = OpenAIClient()
                response = openai_client.generate_text(messages=message_list, response_format={"type": "json_object"})

                json_response = json.loads(response["data"].choices[0].message.content)
                inclusion_criteria.extend(json_response.get("inclusionCriteria", []))
                exclusion_criteria.extend(json_response.get("exclusionCriteria", []))


            except Exception as e:
                print(f"Error processing query rationale: {e}")

            final_data = {
                "inclusionCriteria": inclusion_criteria,
                "exclusionCriteria": exclusion_criteria
            }
            final_response["data"] = final_data
            final_response["success"] = True
            final_response["message"] = "Successfully draft eligibility criteria"
            return final_response
        except Exception as e:
            final_response["message"] = f"Error processing query rationale: {e}"
            return final_response

    def filter_generated_criteria(self, inclusionCriteria, exclusionCriteria) -> dict:
        final_response = {
            "success": False,
            "message": "Failed to filter eligibility criteria",
            "data": None
        }
        try:
            user_input = (
                f"Inclusion Criteria: {inclusionCriteria}\n"
                f"Exclusion Criteria: {exclusionCriteria}\n"
            )

            message_list = [
                {"role": "system", "content": self.filter_role},
                {"role": "user", "content": user_input}
            ]
            print(message_list)

            openai_client = OpenAIClient()
            response = openai_client.generate_text(messages=message_list, response_format={"type": "json_object"})

            json_response = json.loads(response["data"].choices[0].message.content)

            final_response["data"] = json_response
            final_response["success"] = True
            final_response["message"] = "Successfully filtered eligibility criteria"
            return final_response

        except Exception as e:
            final_response["message"] = f"Error filtering criteria: {e}"
            return final_response

    def extract_timeframes_and_text(self, text: str) -> list:
        matches = re.findall(self.pattern, text, re.DOTALL)

        extracted_data = [match.strip() for match in matches]

        return extracted_data
