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
