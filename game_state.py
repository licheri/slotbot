"""
Game state - mutable state for active duels and domain expansion
"""
from typing import Dict, Any

# Active duels per chat: chat_id -> duel_data
# Possibili stati: "pending" (in attesa di accettazione) o "active" (in corso)
ACTIVE_DUELS: Dict[int, Dict[str, Any]] = {}

# Pending duel requests: (chat_id, challenger_id) -> target_id
# Tiene traccia di chi ha sfidato chi e sta aspettando accettazione
PENDING_DUELS: Dict[tuple, int] = {}

# Domain expansion active until: chat_id -> timestamp
EXPANSION_UNTIL: Dict[int, float] = {}

# Global slot tracking block
SLOT_BLOCKED = False

# Debug mode
DEBUG_MODE = False
