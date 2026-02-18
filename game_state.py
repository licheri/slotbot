"""
Game state - mutable state for active duels and domain expansion
"""
from typing import Dict, Any

# Active duels per chat: chat_id -> duel_data
ACTIVE_DUELS: Dict[int, Dict[str, Any]] = {}

# Domain expansion active until: chat_id -> timestamp
EXPANSION_UNTIL: Dict[int, float] = {}

# Global slot tracking block
SLOT_BLOCKED = False

# Debug mode
DEBUG_MODE = False
