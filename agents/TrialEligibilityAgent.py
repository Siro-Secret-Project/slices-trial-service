import json
from document_retrieval.utils.prompts import timeframe_count_prompt, values_count_prompt
from document_retrieval.utils.fetch_trial_filters import extract_timeframes_and_text


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
        self.medical_writer_agent_role = (
            """
                Medical Trial Eligibility Criteria Writer Agent

                Role:
                You are a Clinical Trial Eligibility Criteria Writer Agent. 
                You are responsible for writing Inclusion and Exclusion Criteria for a Clinical trial based on provided inputs.

                Permanent Inputs:
                1. Medical Trial Rationale – The rationale for conducting the trial.
                2. Similar/Existing Medical Trial Documents – Reference documents from similar trials to guide the criteria selection.
                3. Already Generated Inclusion and Exclusion Criteria – These are the criteria generated in the previous pass.

                Additional User-Provided Inputs (Trial-Specific):
                1. User Generated Inclusion Criteria – Additional inclusion criteria provided by the user.
                2. User Generated Exclusion Criteria – Additional exclusion criteria provided by the user.
                3. Trial Conditions – The medical conditions being assessed in the trial.
                4. Trial Outcomes – The expected or desired outcomes of the trial.

                Steps:
                1. From the provided input documents, draft **comprehensive Inclusion and Exclusion Criteria** for the medical trial, **ignoring the already generated criteria**.
                2. Provide **Original Statement(s)** used from documents for each criterion.
                3. Ensure that the criteria align with the trial rationale.
                4. Tag Inclusion Criteria and Exclusion Criteria based on the following 14 key factors:
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

                Response Format:
                ```json_object:
                {
                  "inclusionCriteria": [
                    {
                      "criteria": "string",
                      "source": "original statement used for criteria from the document",
                      "class": "string"
                    }
                  ],
                  "exclusionCriteria": [
                    {
                      "criteria": "string",
                      "source":  "source": "original statement used for criteria from the document",
                      "class": "string"
                    }
                  ]
                }

                ### Example output format

                {
                  "inclusionCriteria": [
                    {
                      "criteria": "Male or female, 18 years or older at the time of signing informed consent",
                      "source": "Participants must be at least 18 years old at the time of enrollment",
                      "class": "Age"
                    }
                  ],
                  "exclusionCriteria": [
                    {
                      "criteria": "Participants with a history of severe allergic reactions to study medication",
                      "source": "Subjects with known hypersensitivity to the investigational drug or any of its components",
                      "class": "Allergies and Drug Reactions"
                    }
                  ]
                }

                Important Notes:
                  The "source" object must contain actual original statements as values.
                  Do not modify the original statements; they must remain as they appear in the trial documents.
                  Do not generate similar criteria again if the statement is same but values are different then they are different statements and must be generated
                  Ensure consistency between extracted criteria, user inputs, and trial goals.
            """
        )
        self.filter_role = ("""
            Role:
                You are an agent responsible for filtering AI-generated trial eligibility criteria.
                Your task is to process given eligibility criteria (both Inclusion and Exclusion) by splitting any combined statements into individual criteria.

            Task:
                - Identify and separate multiple criteria within a single statement.
                - Return the refined criteria in a structured JSON format.

            Response Format:
                The output should be a JSON object with two lists: 
                - "inclusionCriteria" for criteria that qualify participants.
                - "exclusionCriteria" for criteria that disqualify participants.
                json_object{
                    "inclusionCriteria": ["statement1", "statement2"],
                    "exclusionCriteria": ["statement1", "statement2"]
                }

            Example Input:
                Inclusion Criteria: Adults, Diabetes type 2, Wide A1C range, Overweight or obese
                Exclusion Criteria: Kidney disease, heart conditions, Any condition that renders the trial unsuitable for the patient as per investigator's opinion, participation in other trials within 45 days

            Example Output:
                {
                    "inclusionCriteria": [
                        "Adults",
                        "Diabetes type 2",
                        "Wide A1C range",
                        "Overweight or obese"
                    ],
                    "exclusionCriteria": [
                        "Kidney disease",
                        "Heart conditions",
                        "Any condition that renders the trial unsuitable for the patient as per investigator's opinion",
                        "Participation in other trials within 45 days"
                    ]
                }
            """
                            )

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

                # Extract Metrics
                message_list = [
                    {"role": "system", "content": values_count_prompt},
                    {"role": "user", "content": f"{similar_trial_documents}"}
                ]

                metrics_response = self.azure_client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=message_list,
                    stream=False,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )

                drug_output = json.loads(metrics_response.choices[0].message.content)

                primary_outcomes = similar_trial_documents["document"]["primaryOutcomes"]
                timeline = extract_timeframes_and_text(primary_outcomes)
                time_line_output = [
                    {
                        "nctId": similar_trial_documents["nctId"],
                        "timeLine": timeline
                    }
                ]
                messages = [
                    {"role": "system", "content": timeframe_count_prompt},
                    {"role": "user", "content": f"{time_line_output}"}
                ]

                timeframe_response = self.azure_client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=messages,
                    stream=False,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                timeframe_output = json.loads(timeframe_response.choices[0].message.content)

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
