import json


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

        self.categorisation_role = ("""
            Medical Trial Eligibility Criteria Writer Agent

            Objective:
                Your primary task is to categorise the provided eligibility criteria into to provided 14 classes.

            Inputs:
                1. List of eligibility criteria.

            Task:
                Using the provided inputs:
                1. Define Inclusion Criteria and Exclusion Criteria based on the following 14 key factors:
                    - Age
                    - Gender
                    - Health Condition/Status
                    - Clinical and Laboratory Parameters - (provide HbA1c in this category)
                    - Medication Status
                    - Informed Consent
                    - Ability to Comply with Study Procedures
                    - Lifestyle Requirements
                    - Reproductive Status
                    - Co-morbid Conditions
                    - Recent Participation in Other Clinical Trials
                    - Allergies and Drug Reactions
                    - Mental Health Disorders
                    - Infectious Diseases
                    - Other (if applicable)

                2. For each criterion, provide:
                    - criteriaID: Unique ID of criteria.
                    - Class: The specific category from the 14 key factors above.

            Response Format:
                json_object:
                {
                    "inclusionCriteria": [
                        {
                            "criteriaID": "string",
                            "class": "string"
                        }
                    ],
                    "exclusionCriteria": [
                        {
                            "criteriaID": "string",
                            "class": "string"
                        }
                    ]
                }

            Guidelines:
                - Maintain clarity, logic, and conciseness in explanations.
                - HbA1c levels will come in Clinical and Laboratory Parameters
            """)
        self.medical_writer_agent_role = ("""
            Medical Trial Eligibility Criteria Writer Agent

            Role:
            You are a Clinical Trial Eligibility Criteria Writer Agent. 
            You are responsible for writing Inclusion and Exclusion Criteria for a Clinical trial based on provided inputs.

            Permanent Inputs:
            1. Medical Trial Rationale – The rationale for conducting the trial.
            2. Similar/Existing Medical Trial Documents – Reference documents from similar trials to guide the criteria selection.
            3. Already Generated Inclusion and Exclusion Criteria - These are the criteria generated in previous pass so you do no generate again.

            Additional User-Provided Inputs (Trial-Specific):
            1. User Generated Inclusion Criteria – Additional inclusion criteria provided by the user.
            2. User Generated Exclusion Criteria – Additional exclusion criteria provided by the user.
            3. Trial Objective – The main goal of the trial.
            4. Trial Outcomes – The expected or desired outcomes of the trial.

            Steps:
            1. From the provided input documents, draft comprehensive Inclusion and Exclusion Criteria for the medical trial, ignoring the already generated criteria.
            2. Provide NCT ID and Original Statement used from documents for each criteria.
            3. Ensure that the criteria align with the trial rationale and objectives.

            Response Format:
            json_object
            {
              "inclusionCriteria": [
                {
                  "criteria": "string",
                  "source":{
                    "nctId1": "original statement",
                    "nctId2": "original statement"
                  }
                }
              ],
              "exclusionCriteria": [
                {
                  "criteria": "string",
                  "source":{
                    "nctId1": "original statement",
                    "nctId2": "original statement"
                  }
                }
              ]
            }

            Notes:
            - Ensure that the criteria align with the trial rationale and objectives.
            - Reference similar trials (NCT IDs).
            - Prioritize consistency between extracted criteria, user inputs, and trial goals.
            - Eligibility Criteria must be from trial documents only, so each criteria must have a NCT ID related to it.
            """)
        self.filter_role = ("""
        The Role:
        You are a agent responsible for filtering the AI generated trial Eligibility Criteria based on the provided 
        Similarity Score.
        You will be given AI generated eligibility criteria that will be redundant and you will have to filter them out
        based on the similarity score.

        The Process:
        1. Take the remaining criteria and if there are multiple similar criteria like Age related then keep which has the highest similarity score.
        2. Provide the remaining criteria Ids

        The Inputs:
        You will be provided with the following inputs:
        1. Generated Inclusion Criteria - The AI generated Inclusion Criteria.
        2. Generated Exclusion Criteria - The AI generated Exclusion Criteria.
        3. Similarity Score - The similarity score of the generated criteria against the user provided criteria.
        4. ID - The ID of the generated criteria.

        The Output format:
        You will provide the remaining criteria Ids in the following format:
        json_object: {
            "inclusionCriteria": [unique_criteria_id1, unique_criteria_id2],
            "exclusionCriteria": [unique_criteria_id1, unique_criteria_id2]
        }




        """)

    def draft_eligibility_criteria(self, sample_trial_rationale,
                                   similar_trial_documents,
                                   user_provided_inclusion_criteria,
                                   user_provided_exclusion_criteria,
                                   user_provided_trial_objective,
                                   user_provided_trial_outcome,
                                   generated_inclusion_criteria,
                                   generated_exclusion_criteria, ):
        """
        Drafts comprehensive Inclusion and Exclusion Criteria for a medical trial based on provided inputs.

        Parameters:
            sample_trial_rationale (str): The overall rationale for the medical trial.
            similar_trial_documents (list): A list of similar documents from a database.
            user_provided_inclusion_criteria (str): The user-provided inclusion criteria.
            user_provided_exclusion_criteria (str): The user-provided exclusion criteria.
            user_provided_trial_objective (str): The trial objective as provided by the user.
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
        final_response = {
            "success": False,
            "message": "Failed to draft eligibility criteria",
            "data": None
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
                Trial Objective: {user_provided_trial_objective}
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
                # Sending the request to Azure AI chat model
                response = self.azure_client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=message_list,
                    stream=False,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )

                # Parsing the AI-generated JSON response
                json_response = json.loads(response.choices[0].message.content)

                # Extracting inclusion and exclusion criteria from the response
                inclusion_criteria.extend(json_response.get("inclusionCriteria", []))
                exclusion_criteria.extend(json_response.get("exclusionCriteria", []))

            except Exception as e:
                print(f"Error processing AI response: {e}")  # Logging error in AI response processing

            # Preparing final response data
            final_data = {
                "inclusionCriteria": inclusion_criteria,
                "exclusionCriteria": exclusion_criteria
            }

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
                response = self.azure_client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=message_list,
                    stream=False,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )

                json_response = json.loads(response.choices[0].message.content)
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

    def filter_generated_criteria(self, generated_eligibility_criteria) -> dict:
        final_response = {
            "success": False,
            "message": "Failed to filter eligibility criteria",
            "data": None
        }
        try:
            user_input = (
                f"Generated Inclusion Criteria: {generated_eligibility_criteria['inclusionCriteria']}\n"
                f"Generated Exclusion Criteria: {generated_eligibility_criteria['exclusionCriteria']}\n"
            )

            message_list = [
                {"role": "system", "content": self.filter_role},
                {"role": "user", "content": user_input}
            ]
            print(message_list)

            response = self.azure_client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=message_list,
                stream=False,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            json_response = json.loads(response.choices[0].message.content)

            final_response["data"] = json_response
            final_response["success"] = True
            final_response["message"] = "Successfully filtered eligibility criteria"
            return final_response

        except Exception as e:
            final_response["message"] = f"Error filtering criteria: {e}"
            return final_response
