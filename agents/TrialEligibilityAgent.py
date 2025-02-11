import json


class TrialEligibilityAgent:
    def __init__(self, azure_client, model="model-4o", max_tokens=5000, temperature=0.2):
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

        self.categorisation_role = (
            """
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
                    - Criteria: A precise inclusion or exclusion statement.
                    - nctId: NCT IDs of the trial.
                    - Class: The specific category from the 14 key factors above.
    
            Response Format:
                json_object:
                {
                    "inclusionCriteria": [
                        {
                            "criteria": "string",
                            "nctId": "string",
                            "class": "string"
                        }
                    ],
                    "exclusionCriteria": [
                        {
                            "criteria": "string",
                            "nctId": "string",
                            "class": "string"
                        }
                    ]
                }
    
            Guidelines:
                - Maintain clarity, logic, and conciseness in explanations.
                - HbA1c levels will come in Clinical and Laboratory Parameters
            """

        )
        self.medical_writer_agent_role = (
            """
            Medical Trial Eligibility Criteria Writer Agent
    
            Role:
            You are a Medical Trial Eligibility Criteria Writer Agent, responsible for extracting and refining 
            Inclusion and Exclusion Criteria for a medical trial based on provided inputs.
    
            Permanent Inputs:
            1. Medical Trial Rationale – The rationale for conducting the trial.
            2. Similar/Existing Medical Trial Documents – Reference documents from similar trials to guide the criteria 
            selection.
    
            Additional User-Provided Inputs (Trial-Specific):
            1. User Generated Inclusion Criteria – Additional inclusion criteria provided by the user.
            2. User Generated Exclusion Criteria – Additional exclusion criteria provided by the user.
            3. Trial Objective – The main goal of the trial.
            4. Trial Outcomes – The expected or desired outcomes of the trial.
    
            Task:
            1. Extract all eligibility criteria (both Inclusion and Exclusion) from the provided similar trial documents.
            2. Resolve conflicts in criteria:
               - If multiple documents provide conflicting criteria (e.g., drug levels, lab values), prioritize the one 
               with the highest similarity score to the trial rationale.
               - Ensure that the selected criteria are the most relevant to the current trial.
            3. Provide NCT ID of each criteria to track from which trial document it was extracted.
            4. Avoid Redundant criteria.
    
            Response Format:
            json_object
            {
              "inclusionCriteria": [
                {
                  "criteria": "string",
                  "nctId": "string"
                }
              ],
              "exclusionCriteria": [
                {
                  "criteria": "string",
                  "nctId": "string"
                }
              ]
            }
    
            Notes:
            - Ensure that the criteria align with the trial rationale and objectives.
            - Reference similar trials (NCT IDs).
            - If lab values are included, explain their significance.
            - Prioritize consistency between extracted criteria, user inputs, and trial goals.
            - Eligibility Criteria must be from trial documents only, so each criteria must have a NCT ID related to it.
            """

        )



    def draft_eligibility_criteria(self, sample_trial_rationale,
                                   similar_trial_documents,
                                   user_provided_inclusion_criteria,
                                   user_provided_exclusion_criteria,
                                   user_provided_trial_objective,
                                   user_provided_trial_outcome):
        """
        Drafts comprehensive Inclusion and Exclusion Criteria for a medical trial based on provided inputs.

        Parameters:
            sample_trial_rationale (str): The overall rationale for the medical trial.
            similar_trial_documents (list): A list of similar documents from a database.
            user_provided_inclusion_criteria (str): The user-provided inclusion criteria.
            user_provided_exclusion_criteria (str): The user-provided exclusion criteria.
            user_provided_trial_objective (str): The trial objective as provided by the user.
            user_provided_trial_outcome (str): The expected outcome of the trial as provided by the user.

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
                Trial Outcomes: {user_provided_trial_outcome}
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
