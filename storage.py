"""
Storage layer - handles all JSON file operations
"""
import json
import os
import zipfile
import io
import glob
from datetime import datetime, timezone
from typing import Dict, Any, List
from config import (
    SCORES_FILE, USERS_FILE, DUELS_FILE, 
    CURRENT_JSON_VERSION, MAX_BACKUPS
)


def load_scores() -> Dict[str, Any]:
    """Load scores from JSON file"""
    if not os.path.exists(SCORES_FILE):
        return {}
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_scores(scores: Dict[str, Any]) -> None:
    """Save scores to JSON file"""
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


def load_users() -> Dict[str, Any]:
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_users(users: Dict[str, Any]) -> None:
    """Save users to JSON file"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_duels() -> List[Dict[str, Any]]:
    """Load duels from JSON file"""
    if not os.path.exists(DUELS_FILE):
        return []
    try:
        with open(DUELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_duels(duels: List[Dict[str, Any]]) -> None:
    """Save duels to JSON file"""
    with open(DUELS_FILE, "w", encoding="utf-8") as f:
        json.dump(duels, f, ensure_ascii=False, indent=2)


def migrate_scores(scores: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate scores to current version"""
    version = scores.get("_version", 1)

    # MIGRATION FROM VERSION 1 → 2
    if version < 2:
        for user_id, d in scores.items():
            if user_id.startswith("_"):
                continue

            d.setdefault("domains_used", 0)
            d.setdefault("last_triple_msg_id", None)
            d.setdefault("best_speed", 0.0)

        scores["_version"] = 2

    return scores


def migrate_duels(duels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Migrate duels to current version"""
    if isinstance(duels, list):
        # If it's a list, wrap it or handle appropriately
        pass
    else:
        duels = duels.copy() if isinstance(duels, dict) else {}
    
    return duels


def migrate_users(users: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate users to current version"""
    users.setdefault("_version", CURRENT_JSON_VERSION)
    return users


def create_backup_zip() -> str:
    """Create a backup ZIP file with all JSON data"""
    os.makedirs("backup", exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
    zip_path = f"backup/backup_{timestamp}.zip"

    # CREATE ZIP FILE
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for filename in [SCORES_FILE, DUELS_FILE, USERS_FILE]:
            if os.path.exists(filename):
                z.write(filename)

    # KEEP ONLY LAST 10 BACKUPS
    backups = sorted(glob.glob("backup/backup_*.zip"))
    if len(backups) > MAX_BACKUPS:
        for old in backups[:-MAX_BACKUPS]:
            try:
                os.remove(old)
            except:
                pass

    return zip_path


def get_backup_list() -> List[str]:
    """Get list of available backups"""
    return sorted(glob.glob("backup/backup_*.zip"))


def create_export_zip() -> io.BytesIO:
    """Create an in-memory ZIP buffer with all JSON files"""
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for filename in [SCORES_FILE, DUELS_FILE, USERS_FILE]:
            try:
                z.write(filename)
            except:
                pass
    
    buffer.seek(0)
    return buffer
