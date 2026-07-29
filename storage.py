import json
import os
from datetime import datetime

ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "research_archive.json")

def load_archive():
    """Loads all archived search runs from the JSON file."""
    if not os.path.exists(ARCHIVE_FILE):
        return []
    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading archive: {e}")
        return []

def save_to_archive(report_type, query, content, meta=None):
    """Saves a new analysis run to the JSON archive.
    
    Args:
        report_type (str): 'fact_check' or 'market_analysis'
        query (str): The search claim or topic
        content (dict/str): The analysis payload
        meta (dict): Optional metadata (e.g. scores, sources)
    """
    archive = load_archive()
    
    entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": report_type,
        "query": query,
        "content": content,
        "meta": meta or {}
    }
    
    archive.insert(0, entry) # Add to the beginning of the list
    
    try:
        with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(archive, f, indent=4, ensure_ascii=False)
        return entry["id"]
    except Exception as e:
        print(f"Error saving archive: {e}")
        return None

def delete_from_archive(entry_id):
    """Deletes an entry from the archive by ID."""
    archive = load_archive()
    updated_archive = [entry for entry in archive if entry["id"] != entry_id]
    try:
        with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_archive, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error deleting entry: {e}")
        return False
