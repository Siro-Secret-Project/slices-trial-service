from database.document_retrieval.fetch_preprocessed_trial_document_with_nct_id import fetch_preprocessed_trial_document_with_nct_id


def fetch_trial_filters(trial_documents: list) -> dict:
    final_response = {
        "success": False,
        "message": "Failed to filter trials by country",
        "data": None
    }
    try:
        for item in trial_documents:
            nct_id = item["nctId"]
            item["locations"] = []
            item["phases"] = []
            item["enrollmentCount"] = "Unknown"
            item["startDate"] = "Unknown"
            item["endDate"] = "Unknown"
            item["sponsorType"] = "Unknown"
            preprocessed_trial_document_response = fetch_preprocessed_trial_document_with_nct_id(nct_id=nct_id)
            if preprocessed_trial_document_response["success"] is False:
                continue
            else:

                preprocessed_trial_document = preprocessed_trial_document_response["data"]

                # fetch country for each document
                trial_locations = preprocessed_trial_document["protocolSection"].get("contactsLocationsModule", {}).get("locations", [])
                countries = set()
                for location in trial_locations:
                    countries.add(location["country"])
                item["locations"] = countries

                # fetch phase for document
                phases_info = preprocessed_trial_document["protocolSection"].get("designModule",{}).get("phases", ["Unknown"])
                trial_phases = phases_info
                item['phases'] = trial_phases

                # fetch trail participant count protocolSection.designModule.enrollmentInfo.count
                enrollment_info = preprocessed_trial_document["protocolSection"].get("designModule",{}).get("enrollmentInfo",{})
                enrollment = enrollment_info.get("count", 0)
                item['enrollmentCount'] = enrollment

                # fetch trial start date and end date
                date_info = preprocessed_trial_document["protocolSection"].get("statusModule",{})
                start_date = date_info.get("startDateStruct", {}).get("date", None)
                end_date = date_info.get("completionDateStruct", {}).get("date", None)
                item['startDate'] = start_date
                item['endDate'] = end_date

                # Fetch Sponsor Type
                sponsorType = preprocessed_trial_document["protocolSection"].get("sponsorCollaboratorsModule",{}).get("leadSponsor", {}).get("class", "Unknown")
                item['sponsorType'] = sponsorType

        final_response["success"] = True
        final_response["data"] = trial_documents
        final_response["message"] = "Successfully filtered trials by country"
    except Exception as e:
        final_response["message"] = f"Failed to filter trials by country: {e}"

    return final_response