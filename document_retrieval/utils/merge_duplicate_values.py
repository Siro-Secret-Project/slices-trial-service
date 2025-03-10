import re
from collections import defaultdict
from typing import List, Dict


def merge_duplicate_values(data: List[Dict]) -> List[Dict]:
    """
    Merges duplicate values in a list of dictionaries.

    Args:
        data (List[Dict]): List of dictionaries with 'value', 'count', and 'source' keys.

    Returns:
        List[Dict]: Processed list with merged values, updated counts, and combined sources.
    """
    merged_data = defaultdict(lambda: {"count": 0, "source": set()})

    for item in data:
        key = item["value"]
        merged_data[key]["source"].update(item["source"])  # Merge sources

    # Convert set to list and compute count
    return [
        {"value": key, "count": len(value["source"]), "source": list(value["source"])}
        for key, value in merged_data.items()
    ]


def normalize_bmi_ranges(data):
    updated_data = []

    for entry in data:
        bmi_value = entry["value"]

        # Convert "BMI X - 44.5" -> "BMI <= 44.5"
        match_upper = re.match(r'BMI X\s*-\s*(\d+\.?\d*)', bmi_value)
        if match_upper:
            normalized_value = f'BMI <= {match_upper.group(1)}'
        else:
            # Convert "BMI 30 - X" -> "BMI >= 30"
            match_lower = re.match(r'BMI (\d+\.?\d*)\s*-\s*X', bmi_value)
            if match_lower:
                normalized_value = f'BMI >= {match_lower.group(1)}'
            else:
                # Keep original value if no transformation is needed
                normalized_value = bmi_value

        updated_data.append({"value": normalized_value, "count": entry["count"], "source": entry["source"]})

    return updated_data