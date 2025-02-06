import json
from collections import defaultdict
import numpy as np


class TrialEligibilityAgent:
    def __init__(self, azure_client, pinecone_index, documents_collection, model="model-4o", max_tokens=500, temperature=0.2):
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
        self.documents_collection = documents_collection
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.pinecone_index = pinecone_index

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
                    - Reasoning: A brief explanation, referencing similar trials (NCT IDs) when applicable.
                    - Class: The specific category from the 14 key factors above.
    
            Response Format:
                json_object:
                {
                    "inclusionCriteria": [
                        {
                            "criteria": "string",
                            "reasoning": "string",
                            "class": "string"
                        }
                    ],
                    "exclusionCriteria": [
                        {
                            "criteria": "string",
                            "reasoning": "string",
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
            2. Integrate user-provided criteria into the extracted list, ensuring consistency and relevance.
            3. Resolve conflicts in criteria:
               - If multiple documents provide conflicting criteria (e.g., drug levels, lab values), prioritize the one 
               with the highest similarity score to the trial rationale.
               - Ensure that the selected criteria are the most relevant to the current trial.
            4. Provide justification for each selected criterion, referencing the source trial (e.g., NCT ID) and 
            explaining why it was chosen.
    
            Response Format:
            json_object
            {
              "inclusionCriteria": [
                {
                  "criteria": "string",
                  "reasoning": "string"
                }
              ],
              "exclusionCriteria": [
                {
                  "criteria": "string",
                  "reasoning": "string"
                }
              ]
            }
    
            Notes:
            - Ensure that the criteria align with the trial rationale and objectives.
            - Reference similar trials (NCT IDs) for justification.
            - Justifications should be concise and evidence-based.
            - If lab values are included, explain their significance.
            - Prioritize consistency between extracted criteria, user inputs, and trial goals.
            """

        )

    def generate_embeddings_from_azure_client(self, text):
        try:
              response = self.azure_client.embeddings.create(
                  input=text,
                  model="embedding_model"
              )
              # Extract and flatten the embedding
              return np.array(json.loads(response.model_dump_json(indent=2))["data"][0]["embedding"]).reshape(1, 1536)
        except Exception as e:
              print(f"Error generating embeddings: {e}")
              print(text)
              return None

    def query_pinecone_db(self, query: str, module: str = None) -> dict:
        """
        Queries the Pinecone database to fetch documents related to the provided query and module.

        Parameters:
            query (str): The query to search for.
            module (str): The module to filter the results by.

        Returns:
            dict: The final response with documents fetched from Pinecone and MongoDB.
        """
        final_response = {
            "success": False,
            "message": "failed to fetch documents",
            "data": None
        }
        try:
            # Generate embedding for the query
            embedding = self.generate_embeddings_from_azure_client(query).flatten().tolist()

            # Query Pinecone and fetch similar documents
            if module is not None:
                result = self.pinecone_index.query(vector=embedding,
                                                   top_k=10,
                                                   include_metadata=True,
                                                   include_values=True,
                                                   filter={"module": {"$eq": module}})
            else:
                result = self.pinecone_index.query(vector=embedding,
                                                   top_k=10,
                                                   include_metadata=True,
                                                   include_values=True)

            # Process the Response Results
            data = result

            # Prepare a dictionary to store NCT IDs with their related information
            nct_data = defaultdict(lambda: {'count': 0, 'max_score': 0, 'module_max_score': ''})

            # Process the data
            for match in data['matches']:
                nct_id = match['metadata']['nctId']
                module = match['metadata']['module']
                score = match['score']
                value = match['values']

                # Update the count
                nct_data[nct_id]['count'] += 1

                # Update the max score and corresponding module
                if score > nct_data[nct_id]['max_score']:
                    nct_data[nct_id]['max_score'] = score
                    nct_data[nct_id]['module_max_score'] = module
                    nct_data[nct_id]['embeddings'] = value

            # Prepare the final response data
            final_data = []
            for key, value in nct_data.items():
                nctId = key
                module = value['module_max_score']
                similarity_score = int(value['max_score'] * 100)
                if similarity_score < 50:
                    continue
                document_response = self.fetch_mongo_document(nctId, module)
                if document_response['success'] is True:
                    final_data.append({
                        "nctId": nctId,
                        "module": module,
                        "similarity_score": similarity_score,
                        "document": document_response['data']
                    })

            # Return the final response
            final_response['data'] = final_data
            final_response['success'] = True
            final_response['message'] = "Successfully fetched documents"
        except Exception as e:
            final_response['message'] = f"Error occurred: {str(e)}"

        return final_response

    import json

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
                        max_tokens=3000,
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


    def fetch_mongo_document(self, nct_id: str, module: str = None) -> dict:
        final_response = {
            "success": False,
            "message": "Failed to fetch document",
            "data": None
        }

        try:
            mapping = {
                "identificationModule": ["officialTitle"],
                "conditionsModule": ["conditions"],
                "eligibilityModule": ["inclusionCriteria", "exclusionCriteria"],
                "outcomesModule": ["primaryOutcomes", "secondaryOutcomes"],
                "designModule": ["designModule"]
            }

            # Query MongoDB for the document using the nct_id
            document = self.documents_collection.find_one({"nctId": nct_id}, {"_id": 0, "keywords": 0})

            if document and module is None:
                final_response["data"] = document
                final_response["message"] = "Successfully fetched MongoDB document"
                final_response["success"] = True
                return final_response
            elif document and module is not None:
              document_items = mapping[module]
              document_data = {}
              for item in document_items:
                document_data[item] = document[item]
              final_response["data"] = document_data
              final_response["message"] = "Successfully fetched MongoDB document"
              final_response["success"] = True
              return final_response
            else:
                final_response['message'] = f"Document with nctId '{nct_id}' not found"

        except Exception as e:
            final_response['message'] = f"Unexpected error while fetching MongoDB document: {e}"

        return final_response
