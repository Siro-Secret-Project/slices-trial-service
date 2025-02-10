def process_filters(documents, filters):
    filtered_docs = []

    for doc in documents:
        # Check phase match (OR logic)
        if not any(phase in filters['phases'] for phase in doc['phases']):
            continue

        # Check location match based on countryLogic
        if filters['countryLogic'] == 'AND':
            if not all(loc in doc['locations'] for loc in filters['locations']):
                continue
        else:  # OR logic
            if not any(loc in doc['locations'] for loc in filters['locations']):
                continue

        # Check sponsorType match
        if doc['sponsorType'] != filters['sponsorType']:
            continue

        # Check date range
        if not (filters['startDate'] <= doc['startDate'] <= filters['endDate'] and
                filters['startDate'] <= doc['endDate'] <= filters['endDate']):
            continue

        # Check sample size range
        if not (filters['sampleSizeMin'] <= doc['enrollmentCount'] <= filters['sampleSizeMax']):
            continue

        filtered_docs.append(doc)

    return filtered_docs