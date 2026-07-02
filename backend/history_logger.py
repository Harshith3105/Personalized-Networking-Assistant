import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

HISTORY_FILE = "history.json"
FEEDBACK_FILE = "feedback.json"

def _load_json(file_path: str) -> List[Dict[str, Any]]:
    """Helper to safely load a JSON list file."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return []

def _save_json(file_path: str, data: List[Dict[str, Any]]) -> bool:
    """Helper to safely save a JSON list file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")
        return False

def init_storage():
    """Initializes the json storage files if they don't exist."""
    if not os.path.exists(HISTORY_FILE):
        _save_json(HISTORY_FILE, [])
    if not os.path.exists(FEEDBACK_FILE):
        _save_json(FEEDBACK_FILE, [])

def save_conversation(event_description: str, interests: List[str], themes: List[str], starters: List[str]) -> Dict[str, Any]:
    """
    Saves a conversation suggestion block to history.json.
    Each starter gets a unique ID so it can receive feedback.
    """
    init_storage()
    history = _load_json(HISTORY_FILE)
    
    # Structure the starters with unique IDs and initial feedback status
    starters_with_metadata = [
        {
            "id": str(uuid.uuid4()),
            "text": text,
            "feedback": None  # 'up', 'down', or None
        }
        for text in starters
    ]
    
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "event_description": event_description,
        "interests": interests,
        "themes": themes,
        "starters": starters_with_metadata
    }
    
    history.append(entry)
    _save_json(HISTORY_FILE, history)
    return entry

def save_feedback(starter_id: str, feedback_type: str) -> Dict[str, Any]:
    """
    Saves a feedback action ('up' or 'down') to feedback.json,
    and updates the corresponding starter feedback state in history.json.
    """
    init_storage()
    history = _load_json(HISTORY_FILE)
    feedbacks = _load_json(FEEDBACK_FILE)
    
    # 1. Update history.json
    found_starter = None
    associated_event = ""
    for entry in history:
        for starter in entry.get("starters", []):
            if starter["id"] == starter_id:
                starter["feedback"] = feedback_type
                found_starter = starter
                associated_event = entry.get("event_description", "")
                break
        if found_starter:
            break
            
    if found_starter:
        _save_json(HISTORY_FILE, history)
        
    # 2. Log to feedback.json
    feedback_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "starter_id": starter_id,
        "starter_text": found_starter["text"] if found_starter else "Unknown",
        "event_description": associated_event,
        "feedback": feedback_type
    }
    
    # Avoid duplicate feedback entries for the same starter_id by replacing it
    feedbacks = [f for f in feedbacks if f["starter_id"] != starter_id]
    feedbacks.append(feedback_entry)
    _save_json(FEEDBACK_FILE, feedbacks)
    
    return feedback_entry

def get_history() -> List[Dict[str, Any]]:
    """Returns the full conversation history, newest first."""
    history = _load_json(HISTORY_FILE)
    # Sort by timestamp desc
    history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return history

def get_feedback() -> List[Dict[str, Any]]:
    """Returns the logged feedbacks."""
    return _load_json(FEEDBACK_FILE)
