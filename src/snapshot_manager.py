import json
import os
from datetime import datetime

SNAPSHOTS_FILE = "snapshots.json"

def load_snapshots():
    if not os.path.exists(SNAPSHOTS_FILE):
        return []
    try:
        with open(SNAPSHOTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_snapshot(date_str: str, url_30: str, url_60: str, url_90: str):
    snapshots = load_snapshots()
    
    # Check if this date already exists
    existing_idx = -1
    for i, s in enumerate(snapshots):
        if s.get("date") == date_str or s.get("name") == date_str:
            existing_idx = i
            break
            
    new_snapshot = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "date": date_str,
        "name": date_str, # Keep name for backwards compatibility
        "urls": {
            "30": url_30,
            "60": url_60,
            "90": url_90
        }
    }
    
    if existing_idx >= 0:
        snapshots[existing_idx] = new_snapshot
    else:
        snapshots.insert(0, new_snapshot)
        
    with open(SNAPSHOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, indent=2)
        
    try:
        from src.github_sync import push_to_github
        push_to_github(SNAPSHOTS_FILE)
    except Exception as e:
        print(f"Error triggering sync: {e}")
        
    return new_snapshot
    
def delete_snapshot(date_str: str):
    """Remove a snapshot entry for the given date string.
    Supports both "date" and legacy "name" keys.
    """
    snapshots = load_snapshots()
    new_snapshots = [s for s in snapshots if s.get("date") != date_str and s.get("name") != date_str]
    with open(SNAPSHOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_snapshots, f, indent=2)
        
    try:
        from src.github_sync import push_to_github
        push_to_github(SNAPSHOTS_FILE)
    except Exception as e:
        print(f"Error triggering sync: {e}")
        
    return new_snapshots

