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
    """Load scores from JSON file, with automatic cleanup of corrupted entries"""
    if not os.path.exists(SCORES_FILE):
        return {}
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            scores = json.load(f)
        
        # Filter out corrupted entries (non-dict values)
        cleaned = {k: v for k, v in scores.items() if isinstance(v, dict)}
        
        # If we removed entries, save the cleaned version
        if len(cleaned) < len(scores):
            save_scores(cleaned)
        
        return cleaned
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


def auto_import_latest_backup() -> bool:
    """Auto-import the latest backup on bot startup. Returns True if successful."""
    backups = get_backup_list()
    if not backups:
        return False
    
    latest_backup = backups[-1]  # Get the most recent backup
    
    try:
        with zipfile.ZipFile(latest_backup, "r") as z:
            # Extract all files
            z.extractall(".")
        print(f"✅ Auto-imported latest backup: {latest_backup}")
        return True
    except Exception as e:
        print(f"❌ Failed to auto-import backup {latest_backup}: {str(e)}")
        return False

def save_leaderboard_snapshot() -> None:
    """Save a snapshot of today's leaderboard for daily recap"""
    scores = load_scores()
    
    # Create snapshot with timestamp
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    snapshot_dir = "leaderboard_snapshots"
    if not os.path.exists(snapshot_dir):
        os.makedirs(snapshot_dir)
    
    # Sort by points for top 10
    top_10 = sorted(scores.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]
    
    snapshot_data = {
        "date": today,
        "timestamp": datetime.now(timezone.utc).timestamp(),
        "top_10": [
            {
                "user_id": uid,
                "name": data.get("name", "Unknown"),
                "points": data.get("points", 0),
                "streak": data.get("streak", 0),
                "elo": data.get("elo", 1000)
            }
            for uid, data in top_10
        ]
    }
    
    snapshot_file = f"{snapshot_dir}/{today}_snapshot.json"
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(snapshot_data, f, indent=2, ensure_ascii=False)


def get_leaderboard_snapshots(days_back: int = 1) -> Dict[str, Any]:
    """Get snapshots from N days ago for comparison"""
    from datetime import datetime, timezone, timedelta
    
    snapshot_dir = "leaderboard_snapshots"
    if not os.path.exists(snapshot_dir):
        return None
    
    target_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    snapshot_file = f"{snapshot_dir}/{target_date}_snapshot.json"
    
    if not os.path.exists(snapshot_file):
        return None
    
    with open(snapshot_file, 'r', encoding='utf-8') as f:
        return json.load(f)