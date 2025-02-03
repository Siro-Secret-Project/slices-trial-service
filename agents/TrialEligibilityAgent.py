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
        self.query_breakdown_agent_role = (
            """
            You are an AI assistant specialized in processing medical trial rationales.
            Your task is to break down a provided trial rationale into small, logically structured, and independent rationales. 
            Each rationale should be self-contained, contextually relevant, and designed to help query a database like Pinecone to find related documents.
            You have to divide in max 4 sub trial rationale

            ### Input:
            You will be provided with a medical trial rationale.

            ### Task:
            1. Parse the rationale into meaningful, independent rationales.
            2. Ensure each rationale is concise, self-contained, and contextually accurate.

            ### Output Format:
            The response should be structured as follows:

            json_object = {
              "response": [
                "independent rationale 1",
                "independent rationale 2",
                "independent rationale 3",
                ...
              ]
            }

            ### Notes:
            - Each rationale should be self-sufficient and formatted to allow precise database searching.
            - Avoid redundancy in the rationales and focus on capturing distinct key points from the provided rationale.
            """
        )

        self.medical_writer_agent_role = (
            """
            Medical Trial Eligibility Criteria Writer Agent
    
            Objective:
                Your primary task is to draft Inclusion and Exclusion Criteria for a medical trial based on the provided information.
    
            Inputs:
                1. Medical Trial Rationale: The purpose and objectives of the medical trial.
                2. Reference Medical Trials: Documents from similar or past trials to guide the eligibility criteria formulation.
                3. User provided inclusion and exclusion criteria.
    
            Task:
                Using the provided inputs:
                1. Define Inclusion Criteria and Exclusion Criteria based on the following 14 key factors:
                    - Age
                    - Gender
                    - Health Condition/Status
                    - Clinical and Laboratory Parameters
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
                - Ensure accuracy and relevance by comparing similarity scores between the trial rationale and reference documents.
                - Base criteria on evidence and align them with the trial's purpose.
                - Use correct lab values and justify their inclusion.
                - Reference similar trials (NCT IDs) to support the reasoning for each criterion.
                - Maintain clarity, logic, and conciseness in explanations.
            """

        )
        self.filter_role = """
              You are tasked with refining a list of Eligibility Criteria for a medical trial. Along with the criteria, you will also be provided with the trial rationale.

              ### Objective:
              - Remove redundant or repetitive criteria from the provided list.
              - Return a clean and filtered list of eligibility criteria.

              ### Response Format:
              json_object
              {
                "response": [
                  "criteria1",
                  "criteria2"
                ]
              }
            """

    def process_rationale(self, trial_rationale):
        """
        Breaks down a medical trial rationale into smaller, logical queries using an AI model.

        Parameters:
            trial_rationale (str): The input trial rationale text to be processed.

        Returns:
            dict: A dictionary containing the success status, message, and the processed data or error details.
        """
        final_response = {
            "success": False,
            "message": "",
            "data": None
        }

        try:
            # Prepare the chat history with the system and user roles
            chat_history = [
                {"role": "system", "content": self.query_breakdown_agent_role},
                {"role": "user", "content": trial_rationale}
            ]

            # Call the Azure client to get the response
            response = self.azure_client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=chat_history,
                stream=False,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            # Parse the AI response into JSON
            str_response = response.choices[0].message.content
            json_response = json.loads(str_response)

            # Update the final response with success data
            final_response["data"] = json_response["response"]
            final_response["success"] = True
            final_response["message"] = "Successfully broken down rationale"
        except Exception as e:
            # Handle exceptions and update the final response with the error message
            final_response["message"] = str(e)

        return final_response

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

    def draft_eligibility_criteria(self, sample_trial_rationale,
                                   similar_trial_documents,
                                   user_provided_inclusion_criteria,
                                   user_provided_exclusion_criteria):
        """
        Drafts comprehensive Inclusion and Exclusion Criteria for a medical trial based on provided inputs.

        Parameters:
            sample_trial_rationale (str): The overall rationale for the medical trial.
            similar_trial_documents (list): A list of similar documents from a database.
            user_provided_inclusion_criteria (str): The user provided inclusion criteria.
            user_provided_exclusion_criteria (str): The user provided exclusion criteria.

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
                Medical Trial Rationale: {sample_trial_rationale}
                Similar/Existing Medical Trial Document: {similar_trial_documents},
                User provided: {user_provided_inclusion_criteria},
                {user_provided_exclusion_criteria}
            """

            message_list = [
                    {"role": "system", "content": self.medical_writer_agent_role},
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


    def filter_eligibility_criteria(self, inclusion_criteria, trial_rationale):
        """
        Filters the eligibility criteria based on trial rationale by calling an AI model.

        Parameters:
            inclusion_criteria (list): A list of inclusion criteria for the trial.
            trial_rationale (str): The rationale for the trial.

        Returns:
            list: A filtered list of eligibility criteria.
        """

        # Format the inclusion criteria list
        inclusion_criteria_list = [item["criteria"] for item in inclusion_criteria]

        message_list = [
            {"role": "system", "content": self.filter_role},
            {"role": "user", "content": f"Eligibility Criteria: {inclusion_criteria_list}, trial rationale: {trial_rationale}"},
        ]

        # Make the API call to get the filtered criteria
        response = self.azure_client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=message_list,
            stream=False,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        # Parse and return the filtered criteria from the response
        inclusion_criteria_filtered = json.loads(response.choices[0].message.content)['response']

        return inclusion_criteria_filtered

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
