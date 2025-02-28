values_count_prompt = """

Given a list of inclusion criteria for T2DM clinical trials, extract all unique HbA1c and BMI ranges, count their occurrences, and return the source document IDs where each criterion appears.

### Input Format:
A list of dictionaries where:
- "nctId" represents the unique study ID.
- "inclusionCriteria" contains text specifying HbA1c and BMI ranges.

### Instructions:
1. Extract all unique HbA1c and BMI ranges.
2. Normalize the ranges:
   - If a statement says "greater than 7.0", replace it with "7.5 - X".
   - If it says "less than 10.0", replace it with "X - 9.5".
3. Count occurrences of each unique range.
4. Track the source document IDs where each range appears.
5. Return a structured JSON output.

### Example Input:
```json
[
  {
    "nctId": "NCT03141073",
    "inclusionCriteria": "1. Male or female, aged 18\\~75 years old;\n2. T2DM and treated with Metformin ≥ 1500mg/day constantly for at least 12 consecutive weeks;\n3. 7.5% ≤ HbA1c ≤ 10.0% at screening;\n4. 18.5 kg/m2 \\< BMI \\< 35.0 kg/m2 at screening;"
  },
  {
    "nctId": "NCT00552227",
    "inclusionCriteria": "1. Type 2 diabetes mellitus\n2. ≥35 years of age\n3. HbA1c ≥7% and ≤11%."
  }
]

### Expected Output:

json_object:{
  response:[
    {
      "value": "HbA1c 7.5 - 10",
      "count": 1,
      "source": ["NCT03141073"]
    },
    {
      "value": "HbA1c 7 - 11",
      "count": 1,
      "source": ["NCT00552227"]
    },
    {
      "value": "BMI 18.5 - 35",
      "count": 1,
      "source": ["NCT03141073"]
    }
  ]
}

"""

timeframe_count_prompt = """
Given a list of clinical trial timelines, extract all unique time-related values (e.g., weeks, days, phases), count their occurrences, and return the source document IDs where each value appears.

### Input Format:
A list of dictionaries where:
- "nctId" represents the unique study ID.
- "timeLine" contains a list of time-related phrases.

### Instructions:
1. Extract all unique time-related values from the "timeLine" field.
2. Normalize the values:
   - Convert "Week 26" to "week 26".
   - Convert "Baseline to Week 24" to "week 24".
   - Extract numeric week and day values separately (e.g., "Day 1" -> "day 1").
   - For phrases like "Comparing intervention group during the 13-week study phase," extract "week 13".
3. Count occurrences of each unique time value.
4. Track the source document IDs where each value appears.
5. Return a structured JSON output.

### Example Input:
```json
[
  {"nctId": "NCT03141073", "timeLine": ["24 weeks"]},
  {"nctId": "NCT00552227", "timeLine": ["6 weeks"]},
  {"nctId": "NCT00637273", "timeLine": ["Day 1, Week 26"]},
  {"nctId": "NCT05923827", "timeLine": ["Comparing intervention group with control group during the 13-week study phase"]},
  {"nctId": "NCT04980027", "timeLine": ["Baseline to Week 24"]}
]


### Expected Output:
json_object:
{
  response : [
    {
      "value": "week 24",
      "count": 2,
      "source": ["NCT03141073", "NCT04980027"]
    },
    {
      "value": "week 6",
      "count": 1,
      "source": ["NCT00552227"]
    },
    {
      "value": "week 26",
      "count": 1,
      "source": ["NCT00637273"]
    },
    {
      "value": "day 1",
      "count": 1,
      "source": ["NCT00637273"]
    },
    {
      "value": "week 13",
      "count": 1,
      "source": ["NCT05923827"]
    }
  ]
}
"""

merge_prompt = """
You are an AI assistant responsible for processing clinical trial eligibility criteria. Given a list of eligibility 
criteria, your task is to identify similar criteria and merge their `criteriaID` values into a list.

### Rules for Merging Criteria:
1. **Criteria Similarity:** Two criteria are considered the same if they contain the same condition and value.
   - Example:
     - ✅ "Age greater than or equal to 18 years" == "Age 18 years or above"
     - ❌ "Age greater than or equal to 18 years" ≠ "Age equal to or above 20 years"
2. **Merging CriteriaID:** If multiple criteria match based on the rule above, merge their `criteriaID` values into 
   a list while keeping distinct criteria separate.

### Input Format:
A list of dictionaries where each dictionary has:
- `criteria`: A string representing the eligibility condition.
- `criteriaID`: A unique identifier for the criteria.
- `class`: The classification of the criteria (e.g., "Age").

Example input:
[
    {
        "criteria": "Male or female, age greater than or equal to 18 years at the time of signing informed consent",
        "criteriaID": "cid_67c0014af22dd889cf353062",
        "class": "Age"
    },
    {
        "criteria": "Age 18 years or above at the time of signing the informed consent.",
        "criteriaID": "cid_67c0014a4d68c20576d0ad5e",
        "class": "Age"
    },
    {
        "criteria": "Age 18 years or above at the time of signing the informed consent",
        "criteriaID": "cid_67c0014a3b8d564787cc2f57",
        "class": "Age"
    },
    {
        "criteria": "Age 20 years or above at the time of signing the informed consent",
        "criteriaID": "cid_67c0014a3b8d564787cc2f67",
        "class": "Age"
    }
]

### Output Format:
Return a list where similar criteria are merged with their `criteriaID` values combined into a list.

Example output:
json_object:
{
  response : [
      {
          "criteria": "Male or female, age greater than or equal to 18 years at the time of signing informed consent",
          "criteriaID": ["cid_67c0014af22dd889cf353062", "cid_67c0014a4d68c20576d0ad5e", "cid_67c0014a3b8d564787cc2f57"],
      },
      {
          "criteria": "Age 20 years or above at the time of signing the informed consent",
          "criteriaID": ["cid_67c0014a3b8d564787cc2f67"]
      }
  ]
}

Ensure the merged `criteriaID` list contains all unique IDs for the matching criteria. Keep distinct criteria separate.
"""

categorisation_role = ("""
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

medical_writer_agent_role = (
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

filter_role = ("""
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